#! /usr/bin/env python3

import subprocess
import os

class BindCtl():

  """ Create a BindCtl object""" 
  def __init__(self, 
               identity_file, 
               user, 
               ip,
               bind_dir="/etc/bind",
               zoneconfig="named.conf.local",
               systemd_service="named.service",
               zone_dir="/etc/bind/zones",
               zonefile_suffix=".zone",
               log_dir="/etc/bind/log",
               log_file="query.log"):
    
    # BIND configuration
    self.BIND_DIR = bind_dir
    self.ZONECONFIG = zoneconfig
    self.SYSTEMD_SERVICE = systemd_service
   
    # Zone configuration
    self.ZONE_DIR = zone_dir
    self.ZONEFILE_SUFFIX = zonefile_suffix
  
    # Log configuration
    self.LOG_DIR = log_dir
    self.LOG_FILE = log_file

    
    # SSH configuration
    self.identity_file = identity_file
    self.ip = ip
    self.user = user
    self.remote =  "-i {} {}@{}".format(identity_file, user, ip) 
  
  """ Check BIND service status""" 
  def status(self):
    cmd = f"ssh {self.remote} systemctl status {self.SYSTEMD_SERVICE}"
    return self._run_command(cmd)  
  
  """ Restart BIND service""" 
  def restart(self):
    cmd = f"ssh {self.remote} systemctl restart {self.SYSTEMD_SERVICE}"
    return self._run_command(cmd)
  
  """ Fetch logs from BIND server"""
  def fetch_logs(self, target="."):
    cmd = f"ssh {self.remote} mv {self.LOG_DIR}/{self.LOG_FILE} {self.LOG_DIR}/{self.LOG_FILE}.old"
    print(cmd)
    s = self._run_command(cmd)
    self.restart()
    print(s)
    cmd = f"scp {self.remote}:{self.LOG_DIR}/{self.LOG_FILE}.old {target}"
    print(cmd)
    return self._run_command(cmd) 

  """ Delete logs on BIND server""" 
  def delete_logs(self):
    cmd = f"ssh {self.remote} rm {self.LOG_DIR}/*"
    return self._run_command(cmd)

  """ Run 'named-checkzone <zonename>' on BIND server"""
  def check_zone(self, zonename):
    cmd = f"ssh {self.remote} named-checkzone {zonename} {self.ZONE_DIR}/{zonename}{self.ZONEFILE_SUFFIX}"
    return self._run_command(cmd)

  """ Run 'named-checkconf' on BIND server""" 
  def check_config(self):
    cmd = f"ssh {self.remote} named-checkconf"
    return self._run_command(cmd)
  
  def _generate_zone_config(self, zonefiles:list):
    for z in zonefiles:
      assert z.endswith(self.ZONEFILE_SUFFIX)
    
    # Generate named.conf.local
    named_conf = ""
    for z in zonefiles:
      named_conf += f"zone \"{z[:-len(self.ZONEFILE_SUFFIX)]}\" {{\n  type master;\n  file \"{self.ZONE_DIR}/{z}\";\n}};\n"
    return named_conf



  """ Install multiple Zones. zonefiles is a list of pairs (zonename, zonefile)"""
  def install_zones(self, zonefiles:list):
    status = []
    for zonename, zonefile in zonefiles:
      cmd = f"scp -i {self.identity_file} {zonefile} {self.user}@{self.ip}:{self.ZONE_DIR}/{zonename}{self.ZONEFILE_SUFFIX}"
      status.append(self._run_command(cmd))
    # List zone directory, generate named.conf.local for all zone files
    cmd = f"ssh {self.remote} ls {self.ZONE_DIR}"
    r = subprocess.run(
      cmd.split(' '), 
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT
    )
    r.check_returncode()
    zonefiles = r.stdout.decode().split()
    
    # Generate named.conf.local
    named_conf = self._generate_zone_config(zonefiles)
    
    # Write named.conf.local to file and copy to server
    with open(self.ZONECONFIG, "w") as f:
      f.write(named_conf)

    # Copy named.conf.local to server
    cmd = f"scp -i {self.identity_file} {self.ZONECONFIG} {self.user}@{self.ip}:{self.BIND_DIR}/{self.ZONECONFIG}"
    status.append(self._run_command(cmd))

    # Remove local file
    os.remove(self.ZONECONFIG)


    return all(status)

  """ Clean all zones below SLD on BIND server""" 
  def clean_zones(self, keep=[]):
    
    # List zone directory
    cmd = f"ssh {self.remote} ls {self.ZONE_DIR}"
    r = subprocess.run(
      cmd.split(' '), 
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT
    )
    r.check_returncode()
    zonefiles = r.stdout.decode().split()
    
    # Exclude zones to keep
    zonefiles = [z for z in zonefiles if z[:-5] not in keep]
    
    # Remove all zone files that are not in keep
    #print("Removing zone files: ", zonefiles)
    status = []
    for z in zonefiles:
      cmd = f"ssh {self.remote} rm {self.ZONE_DIR}/{z}"
      print(cmd)
      status.append(self._run_command(cmd))
    
    named_conf = self._generate_zone_config([f"{z}{self.ZONEFILE_SUFFIX}" for z in keep])
    # Copy named.conf.local to server
    with open(self.ZONECONFIG, "w") as f:
      f.write(named_conf)
    cmd = f"scp -i {self.identity_file} {self.ZONECONFIG} {self.user}@{self.ip}:{self.BIND_DIR}/{self.ZONECONFIG}"
    #print(cmd)
    status.append(self._run_command(cmd))
    # Remove local file
    os.remove(self.ZONECONFIG)

    return all(status)

  """ Run arbitrary command, return True if successful, otherwise print stdout and return False"""
  def _run_command(self, c):
    
    r = subprocess.run(
      c.split(' '), 
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
    )
    try:
      r.check_returncode()
      return True
    except:
      print(r.stdout.decode())
      return False



