## Directory Overview

- `config.py`: main configuration file of the framework
- `discovery`: wrapper scripts around [XMap](https://github.com/idealeer/xmap) to scan the IP address space and discover recursive resolvers on the Internet from probes configured for the framework
- `measurement`: scripts related to performing measurements, notably contains:
    - `materialize.py`: script to materialize abstract query patterns
    - `run_measurement.py`: to distribute files in `materialized` directory, run measurement, and retrieve data to `results` directory
    - `patterns/`: containing declaration of a number of abstract query patterns
    - `engine/`: contains query engine copied to probes
- `analysis`: contains scripts related to combining and analyzing the data, notably:
    - `Combine.py`: to combine responses and log entries collected by the framework
    - `lib/`: code with analysis logic
    - `All.py` declaration of data to be retrieved
- `common`: code used by multiple of the above listed parts of the framework

## Installation Instructions

### Preparing the Remote Machines

To run the framework, a number of machines with public IPs are needed.
There are two types of machines: **probes** and authoritative **nameservers**, each of which you may want to have multiple depending on the measurements you want to perform.
The two types of machines require the following dependencies:

Probes

- `tmux`, `make`, the docker engine, and `python3` must be installed to run measurements.
- Additionally, if you intend to discover resolvers using the same probes, `xmap` has to be installed. `discovery/install_xmap.sh` outlines the steps. For more information refer to their [GitHub repository](https://github.com/idealeer/xmap)

Nameservers

- On the nameserver, `tmux` and `make` must be installed.
- Additionally, BIND must be installed and configured on the nameserver 
to be authoritative for a domain used for the experiments.

### Preparing the Orchestrator

In addition to the remote machines performing the measurements,
an orchestrator machine is used (e.g. your laptop) to which this repo is cloned.
Scripts for discovering resolvers, preparing and running measurements, and processing data are run on this machine.

To prepare the machine, create a python `venv` and install the dependencies in `requirements.txt`:
```bash
python3 -m venv .venv           # Create the virtual environment
. .venv/bin/activate            # Source the virtual environment
pip install -r requirements.txt # Install the dependencies
```




### Configuring the Framework

Once the machines are set up, edit the main configuration file `config.py` appropriately.

For the probe, change the `CLIENT_HOST` dictionary appropriately
by inserting the probes' public IP address as well as the SSH user and the path to the SSH key on the localhost (identity file).

For the nameserver, change the `NAMESERVERS` directory appropriately:

- Set the `IP`, `user`, and `identity` fields just like for the probe (described above).
- Set the `DOMAIN` field to the domain for which the nameserver is authoritative and under which the tests should be run. This field will be used to generate zonefiles and queries according to the abstract query patterns.
- Set the `SOA` field: this is a list of resource records in string format. It will be pasted at the beginning of all generated zonefiles for this nameserver. Thus, it *must* contain the SOA record for the test domain as well as any other records that should always be present in the zonefile (e.g. www or ns1).
- Set the `persistent_zone` field: this is a list of zone names that should never be removed from the nameserver completely. Adding them here excludes them from the `clean-zones` command of the `run_measurement.py` script.
- Finally, if your BIND configuration differs from the default, you may need to adjust some parameters in the `bind_config` field. The default values are commented out in the configuration file.
For example, if BIND is configured to log to a different directory than `/etc/bind/log/`, you should set the `log_dir` field to the correct path so that the framework can retrieve the logs successfully. An example of the default values is given below.

```python
"bind_config": {
  #"bind_dir": "/etc/bind",
  #"zoneconfig": "named.conf.local",
  #"systemd_service": "named.service",
  #"zone_dir": "/etc/bind/zones",
  #"zonefile_suffix": ".zone",
  "log_dir": "/mnt/ta6_ch_storage/bindlog",
  #"log_file": "query.log"
}
```

These configurations are sufficient to run measurements. Nonetheless, we briefly describe the rest of the configuration parameters:

- `MATERIALIZE_DIR` and `RESULTS_DIR` refer to the directories from/to which the scripts read and write data. The default values are `materialized` and `results`, respectively. There is no need to change these.
- `MAX_ZONE_ENTRIES` is the threshold of the number of resource records which the `materialize.py` script will emit for a single nameserver before automatically sharding the measurement.
The default value is 2800000 which was fine for a nameserver with 2GB of memory. If you are running a weaker machine as nameserver, you may want to adapt this value.
- `PATTERN_ZONE_DEFAULT` and `PATTERN_QUERY_DEFAULT` contain the default values that are used by the `materialize.py` script if the abstract query pattern does not contain all fields. There is no need to change these.
- `RE_LOGENTRY` contains a regular expression for parsing the log file and is used by the `Combine.py` script when processing the raw log files. Depending on the BIND configuration, this field needs to be adapted.

## Running the Framework

This section is structured into the three mostly independent parts of the framework: discovery, measurement, and analysis.

### Discovery

Everything related to discovering resolvers in the wild is located in the `discovery/` directory.

The main script is `discover_resolvers.py` and is essentially a wrapper around XMap including persistent sessions on the probe machines using `tmux`.

Launching a discovery:

```bash
./discover_resolvers.py --d ta6.ch --o out.json --r 100
```

- the command will start a discovery which will send a *single* query for `ta6.ch` to each IP in the IPv4 address space.
- the script will shard the work among *all* probes that are configured in `config.py` and have xmap installed.
- the flag `--r` sets the packets per second that the probes send. The default value is 100. For an actual measurement a value of 10000 is more appropriate on a 1Gbps link.

Checking progress:

- You can check the status by running `./discover_resolvers.py status` which will check the presence of a tmux session on the probes.
- Additionally, you can track the progress by logging into one machine and running `tail -f discovery.log` or by attaching to the tmux session with `tmux attach -t discovery`.

Retrieving Results:

- Once the discovery is finished, run `./discover_resolvers.py retrieve` to collect the results from the probes.
- The output will be stored in the file specified by the `--o` flag (in this case `out.json`).
- In case multiple probes were used, the outputs will be called `out.json<n>`.
- The output is in JSON Line format, i.e. contains one JSON object per line and can be concatenated (e.g. `cat out.json* > all.json`).

General Remarks:

- XMap will run with the output filter `dns_rcode = 0 && dns_ra = 1`, i.e. only NOERROR responses with the recursion available bit set are recorded.
- Only a subset of response field is emitted due to space considerations.
- The discovery script also offers a `--dry` flag for a dry run of 30 seconds to check if everything is set up correctly.
- It also offers a `--n` option to run until a certain number of resolvers have been found. With this option enabled, the script will only use a single probe.

Data Conversion:

```bash
./make_csv.py out.json --o resolverlist.csv
```

- XMap's output is in JSON but the rest of the framework expects the resolver lists as a CSV file with certain header fields.
- `make_csv.py` is a simple script to emit a tabular format of resolvers that can be used by the rest of the framework.

Intersection:

```bash
./find_intersection.py resolverlist1.csv resolverlist2.csv --o intersection.csv
```

- In case the intersection between different discovery runs is desired, the `find_intersection.py` script can be used.

### Measurement

Everything related to performing measurements is located in the `measurement/` directory.

General:

- The `materialize.py` script is used to prepare a measurement and outputs all required files into the `materialized/` directory (unless changed in the config).
- The `run_measurement.py` script uses the files in the `materialized/` directory to distribute the measurement to the probes and retrieve the results to the `results/` directory.

Materialization:

```bash
./materialize.py patterns/enum.json resolverlists/list.csv --xprod --skip-duplicate-check
```

- The `materialize.py` script takes two arguments: the abstract query pattern and the resolver list.
- It outputs zonefiles (for the nameservers) and query task files (for the probes) into the `materialized/` directory.
- The `--xprod` flag instantiates the abstract pattern for the cross-product of all available probes and each resolver in the `rr0` column of the resolverlist.
- If no `--xprod` flag is given, the script will instantiate the pattern for each line in the resolver list (i.e. for each `rr0,vp0` tuple).
- Alternatively, there is a `--split` flag which will distribute the work among all probes in a round-robin fashion. Alongside, there is a `--shift <n>` flag which will shift the starting point of the round-robin distribution by `n` probes.
- There is a `--shard-after` option that overrides the `MAX_ZONE_ENTRIES` configuration parameter in the configuration file.
- Finally, there is a `--skip-duplicate-check` option: if not provided, the script will check that no duplicate records are emitted to the same zonefile, potentially signifying a collision in names between multiple measurements.
This check is implemnted with a simple set membership and thus takes a lot of time for large resolver lists. It is recommended to test an abstract query pattern with a small resolver list and checks enabled before materializing the pattern for a large resolver list.

Query Engine Configuration:

- The `run_measurement.py` script will send the files in `materialized/` to the probes and nameservers, respectively.
- It will copy the query engine to the probes and start the measurement.
- It is good practice to double-check the engine configuration **BEFORE** running the measurement (`measurement/engine/config.py`).
- In particular, the `NUM_WORKERS` parameter should be reduced if the nameserver is rather resource-limited and the query pattern is highly parallel (e.g. fanout)
- The `MAX_FAILS`, `ABORT_POLICY`, and `WAIT_POLICY` parameters may also be adapted according to the needs.
Running the Measurement:

Running the Measurement:

```bash
./run_measurement.py run
```

- The above command launches the measurement in the `materialized/` directory.
- In case the materialization emitted multiple shards for a single measurement, the shard to be run can be selected with the `-s` or `--shard` option.

Checking Progress:

- Similar to the discovery, the status can be checked by running `./run_measurement.py status`.
- For more detailed progress information, log into the probe and run `tail -f engine/tasks/log***`. Note that this file is only present while the measurement is running.
- Before and after the measurement is running, run `tail -f engine/log.txt`.

Retrieving Results:

```bash
./run_measurement.py retrieve
```

- Once the measurement is finished on all involved probes, this command will collect the responses collected by the probes and the logs from the nameservers and save them to the `results/` directory.
- At this point, all files in the `results/` directory constitute the raw data of the measurement and should be saved / moved somewhere else.

General Remarks:

- The `run_measurement.py` script offers a `clean` command to remove task and log files from the engine on all probes.
- It also offers a `clean-zones` command to remove all zones from the nameservers (except those listed in the `persistent_zone` field in the global `config.py`).
- In case something goes wrong, the script offers a `kill` command which terminates the tmux sessions on all probes. In some cases, this might not completely terminate the probing and manual intervention (e.g. reboot of probe) may be required.

### Analysis

Everything related to analyzing the data is located in the `analysis/` directory.

Combining raw data:

```bash
./Combine.py all data/raw/enum/ data/combined_enum/
```

- In the raw data format collected by the framework, log entries are not yet associated with a resolver measurement.
- The `Combine.py` script takes the raw data (here `data/raw/enum`)
and builds a folder structure containing the combined data (here below `data/combined_enum`).
- The command `all` instructs the script to perform all 4 steps required to build the folder structure consecutively.
- Alternatively, the commands `distribute_client`, `distribute_server`, `combine`, and `move_serverless` can be run sequentially.

Measurements involving 2 Resolvers:

- There is **currently no command line flag** to specify the decoding of IP addresses. The default is `decoding = ('ns','vp')` specified in the code and corresponding to the `enc(rr0-vp0)` symbol in the abstract query patterns.
- In case the encoding involves 2 resolvers and a vantage point / probe, the decoding has to be adapted in the code.
- For example, if the pattern uses `enc(rr0-rr1-vp0)` and `enc(rr1-rr0-vp0)` as an encoding, the variable should be set to `decoding = ('ns','ns','vp')`.
- In the resulting folder structure, only the first half of the IPv4 address space will be present as the measurements are inserted according to lexicographically ordered IPs of the involved resolvers.

General Remarks:

- It makes sense to build a new folder structure for each measurement type (e.g. `enum`, `fanout`, `fanout2`, etc.). The different structures can easily be combined later with e.g. `rsync -aq combined_enum/ combined_all/`.
- The script outputs two logfiles into `combined_enum/combine_log/`:
`enum.stats` and `enum.error`

Aggregation:

- Inferring properties from the data involves more coding.
- The file `All.py` contains examples of how to write processing code.
- Below is an example of the specification of one output file `all.csv` of aggregated data.

```python
out_file = f"all.csv"
funcs = {
  "qmin": agg.Process_Qmin("qmin"),
  "enum": agg.Process_Enumerate("enum"),
  "maxfetch": agg.Process_NumFetches("maxfetch"),
  "rd0": agg.Process_Rd0("rd0"),
  "shared_frontend": agg.Process_SharedFrontend("shared_frontend"),
  "ttl0": agg.Process_TTL0("ttl0"),
}
db.process_multiple_datasets(f"{out_dir}/{out_file}", funcs, group_by_rr=False)
```

- The specification essentially consists of a dictionary of measurement results mapped to processing classes.
- The processing classes are defined in `analysis/lib/Aggregate.py`.
- Each processing class defines what to infer and which columns to output to the aggregated data csv.
- Make sure that the processing class is chosen appropriately for the measurement pattern that was run or the column in the csv file will be empty.