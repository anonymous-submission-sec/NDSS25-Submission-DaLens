
import re

class BindLog:

  """ 
  Initialize BindLog object with regex pattern for log entries.
  The regex pattern should contain named groups for the following fields:
  - timestamp
  - client_address
  - query_type
  - query
  """
  def __init__(self, regex:str):
    self.pattern = re.compile(regex)

  """ Parse one line of a bind log file. Return None if the line does not match the pattern."""
  def parse(self, c:str):
    match = self.pattern.search(c)
    if match:
      entry = {
        "timestamp": match.group('timestamp'),
        "ip": match.group('client_address'),
        "query": match.group('query').lower(),
        "type": match.group('query_type'),
      }
      return entry
    else:
      return None
  
# Example Logentry:
# 11-Jan-2024 15:02:58.283 info: client @0x7f87e016ac48 213.211.50.1#46988 (v2nr.5352a16f-9de6617e.ta6.ch): query: v2nr.5352a16f-9de6617e.ta6.ch IN A -E(0)D (207.154.207.150)
