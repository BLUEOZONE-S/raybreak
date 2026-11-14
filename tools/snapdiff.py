#!/usr/bin/env python3
"""snapdiff.py -- compare two snapshot files and print every value that differs.   python snapdiff.py A.json B.json"""
import json, sys


def flat(d, pre=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flat(v, pre + k + "."))
        else:
            out[pre + k] = v
    return out


a, b = (flat(json.load(open(f))) for f in sys.argv[1:3])
skip = ("time", "label")
n = 0
for k in sorted(set(a) | set(b)):
    if k in skip:
        continue
    if a.get(k) != b.get(k):
        n += 1
        print(f"{k}: {a.get(k)!r}  ->  {b.get(k)!r}")
print(f"{n} difference(s)")
