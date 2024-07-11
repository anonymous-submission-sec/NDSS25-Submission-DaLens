#! /usr/bin/env python3


# Used to validate loaded pattern file
pattern_scheme = {
  "type": "object",
  "properties": {
    "pattern": {"type": "string"},
    "nameservers": {
      "type": "object",
      "additionalProperties": {
        # variable number of nameservers "0": [..], each of them an array of zone objects
        "type": "array",
        "items": {
          # zone object {"zone": "..", "records": [..]}
          "type": "object",
          "properties": {
            "zone": {"type": "string"},
            "records": {
              "type": "array",
              # record object {"name": "..", "ttl": "..", "type": "..", "ans": ".."}
              "items": {
                "type": "object",
                "properties": {
                  "name": {"type": "string"},
                  "ttl": {"type": "integer"},
                  "type": {"type": "string"},
                  "ans": {"type": "string"}
                },
              }}
          },
        }
      }
    },
    #"zone": {"type": "array", 
    #  "items": {
    #    "type": "object",
    #    "properties": {
    #      "name": {"type": "string"},
    #      "type": {"type": "string"},
    #      "ttl": {"type": "integer"},
    #      "ans": {"type": "string"},
    #      "random_subdomains": {"type": "boolean"},
    #    },
    #    "required": ["name"]
    #  }},
    "queries": {"type": "array", 
      "items": {
        "type": "object",
        "properties": {
          "rr": {"type": "string"},
          "vp": {"type": "string"},
          "query": {"type": "string"},
          "type": {"type": "string"},
          "wait": {"type": ["integer", "string"]},
          "repeat": {"type": ["integer", "string"]},
          "timeout": {"type": ["integer", "string"]},
          "random_subdomains": {"type": "boolean"},
          "concurrent": {"type": "boolean"},
          "expected_status": {"type": "string"},
          "recursion_desired": {"type": "boolean"},
          "wait_after": {"type": ["integer", "string"]},
        },
        "required": ["rr","vp","query"]
      }},
  },
  "required": ["pattern", "nameservers", "queries"]
}

# Used to validate resource records before they are written to the Zonefile
rr_scheme = {
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "ttl": {"type": "integer", "minimum": 0},
    "class": {"type": "string", "enum": ["IN"]},
    "type": {"type": "string", "enum": ["A"]},
    "ans": {"type": "string"}
  },
  "required": ["name"]
}