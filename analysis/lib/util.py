#! /usr/bin/env python3

#""" Transform 
#{"k": abc, "d": def} into {"k": abc, "k_inner": {"d": def}}
#"""
#def group_by(l:list[dict], k:str, k_inner) -> list():
#  assert all([k in m.keys() for m in l]), f"Use of group_by requires key k to be present in all dicts"
#  res = dict()
#  for m in l:
#    kk = m[k]
#    if kk in res.keys():
#      res[kk] += [m]
#    else:
#      res[kk] = [m]
#    del m[k]
#  return [{k: kk, k_inner: res[kk]} for kk in res.keys()]
#
#""" Print arbitrary list of identical *flat* dictionaries in csv format"""
#def print_csv(l:list):
#  print(",".join(l[0].keys()))
#  for e in l:
#    print(",".join([str(e[k]) for k in e.keys()]))