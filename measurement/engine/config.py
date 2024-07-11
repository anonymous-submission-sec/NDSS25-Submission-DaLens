#! /usr/bin/env python3



"""
Maximum number of queries to run in parallel from a single vantage point / docker container

Example: 1000
"""
NUM_WORKERS = 1000

"""
Name of the docker image being built and run

Example: "vantagepoint:latest"
"""
IMAGE_NAME = "vantagepoint:latest"

"""
Maximum number of subprocesses to use for running the vantage point containers

Example: 4
"""
NUM_VANTAGE_POINTS = 4

"""
Subdirectory of the measurement directory where the available VPN configurations are stored
"""
VPN_CONFIG_DIR = "configs"

"""
Subdirectory of the measurement directory where the query tasks for each vantage point are stored

Example: "tasks"
"""
QUERY_TASK_DIR = "tasks"

# =======================
#   Engine Settings
# =======================

"""
API URL for the EchoIP service that is used to determine the public IP address of a vantage point.

Example: "https://ifconfig.me/ip"
"""
ECHOIP_URL = "https://ifconfig.me/ip"

"""
Threshold used by the Status Tracker to determine if a query has failed.

Example: 3
"""
MAX_FAILS = 3

"""
Wait policy used by the Status Tracker. Check StatusTracker.py for available policies.

Example: "wait_policy_if_online"
"""
WAIT_POLICY = "wait_policy_if_online"

"""
Abort policy used by the Status Tracker. Check StatusTracker.py for available policies.

Example: "abort_policy_n_timeout_no_success"
"""
ABORT_POLICY = "abort_policy_n_timeout_no_success"

"""
Debug flag. If set to True, the engine will periodically check the status of the workers and retrieve stack traces of the workers that have crashed.

Example: False
"""
DEBUG = False