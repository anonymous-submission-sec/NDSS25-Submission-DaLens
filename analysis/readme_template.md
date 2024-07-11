

## Resolver List

All measurements in this folder are run on the public1000 resolver list.
It consists of the public60 and swiss resolver lists as well as random resolvers from the intersection list.
The list is found as `resolverlist.csv` in the dataset.

## Format

Data in this folder was generated using an old pattern model that only allowed
to configure 1 zone on 1 nameserver.
Zone configuration is embedded in the BasicMeasurements under a 'zone' field.

Client Data Format
```json
{
    "pattern": "...",
    "zone": [..],
    "queries": [..],
    "responses": [..],
}
```

The combined data is organized in two folders: 

- `combined` contains all measurements involving a single resolver
- `combined-pairs` contains all measurements involving pairs of resolvers
    - the IP addresses of the pair are lexicographically ordered

Both `combined` folders have the following structure:

- there are subdirectories `x.x` representing a /16 prefix
- in each such folder, there are multiple files `x.x.x.x-pattern`
    - `x.x.x.x` is the IP of the resolver that was measured
    - `pattern` is the measurement pattern that produced the result
- each file contains measurements concerning only one / one pair of resolvers
- it contains measurements performed from multiple vantage points
    

Combined Data Format
```json
{
    "pattern": "...",
    "zone": [..],
    "queries": [..],
    "responses": [..],
    "logentries": [..]
}
```

## Measurements

Based on `resolverlist.csv`:

- enum: run on 2024-01-25
- enum1: run on 2024-01-25
- rd0: run on 2024-01-25
- shared: run on 2024-01-25
- ttl0: run on 2024-01-25
- qmin: run on 2024-01-30

Based on `egress_overlap.csv` synthecised from the above `enum`:

- order_cachebased: run on 2024-02-05


