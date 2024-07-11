#! /usr/bin/env python3


import subprocess
import os

class SessionCtl():
  
  def __init__(self, identity_file, user, ip):
    self.identity_file = identity_file
    self.ip = ip
    self.user = user
    self.remote =  "-i {} {}@{}".format(identity_file, user, ip) 

  """ Check if tmux session 'session' is running on remote host""" 
  def session_running(self, session):
    cmd = f"ssh -t {self.remote} tmux has-session -t {session}"
    try:
      r = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      r.check_returncode()
      return True
    except:
      return False

  """ Check if all programs in list 'programs' are installed on remote host, return True if so, False if any are not installed""" 
  def check_installed(self, programs:list):
    cmd = f"ssh -t {self.remote} which {' '.join(programs)}"
    # 'which' returns number of programs that are NOT installed
    try:
      r = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      return r.returncode == 0
    except:
      print(f"Checking dependencies on {self.ip} failed! FATAL")
      exit(1)

  """ Run command 'command' in detached tmux session 'session' on remote host"""
  def run_session(self, session, command):
    cmd = f"ssh -t {self.remote} tmux new-session -d -s {session} '{command} && exit'"
    return self._run_command(cmd)

  """ Kill tmux session 'session' on remote host"""
  def kill_session(self, session):
    cmd = f"ssh -t {self.remote} tmux kill-session -t {session}"
    return self._run_command(cmd)
  
  """ Remove file at 'remotepath' on remote host"""
  def remove_file(self, remotepath):
    return self._run_command(f"ssh {self.remote} rm {remotepath}")

  """ Run command 'make clean' in folder 'remotepath' on remote host"""
  def make_clean(self, remotepath):
    return self._run_command(f"ssh {self.remote} cd {remotepath} && make clean")

  """ Copy file 'localfile' to 'remotepath' on remote host"""
  def copy_file_to(self, localfile, remotepath):
    return self._run_command(f"scp -i {self.identity_file} {localfile} {self.user}@{self.ip}:{remotepath}")

  """ Copy file 'remotepath' from remote host to current directory""" 
  def copy_file_from(self, remotepath, target="."):
    return self._run_command(f"scp {self.remote}:{remotepath} {target}")

  """ Copy folder 'localfolder' to 'remotepath' on remote host""" 
  def copy_folder_to(self, localfolder, remotepath):
    return self._run_command(f"scp -r -i {self.identity_file} {localfolder} {self.user}@{self.ip}:{remotepath}")

  """ Check if file 'remote_filepath' exists on remote host"""
  def file_exists(self, remote_filepath):
    cmd = f"ssh -t {self.remote} test -f {remote_filepath}"
    try:
      r = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      r.check_returncode()
      return True
    except:
      return False

  """ Run arbitrary command, return True if successful, otherwise print stdout and return False"""
  def _run_command(self, c):
    
    r = subprocess.run(
      c.split(' '), 
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT
    )
    try:
      r.check_returncode()
      return True
    except:
      print(r.stdout.decode('utf-8'))
      return False



