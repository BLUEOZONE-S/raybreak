#!/usr/bin/env python3
"""
rayjet_diag.py -- READ-ONLY scan of the firmware's diagnostic values.

The idle status poll can carry extra
3-byte requests  87 <id hi> <id lo>  after the usual 10 2C 2E, and the machine answers with a tag
  88 <id hi> <id lo> <be32 a> <be32 b>        (10 bytes after the tag; 'b' is the interesting value)
This script asks for a range of ids and prints what comes back.  It sends no commands and moves nothing.
Run it when the machine is READY (Z buttons alive).

    python rayjet_diag.py                 # ids 0..255
    python rayjet_diag.py --last 0x3FF
"""
import argparse, json, time
from rayjet_sf import Rayjet
from rayjet_params import walk, be32


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=lambda s: int(s, 0), default=0xFF)
    ap.add_argument("--batch", type=int, default=8)
    a = ap.parse_args()
    rj = Rayjet("COM3", verbose=False).connect()
    found, silent = {}, []
    try:
        for base in range(0, a.last + 1, a.batch):
            ids = [i for i in range(base, min(base + a.batch, a.last + 1))]
            ext = bytes([0x10, 0x2C, 0x2E]) + b"".join(bytes([0x87, i >> 8, i & 255]) for i in ids)
            got = set()
            t0 = time.time()
            while time.time() - t0 < 1.5 and len(got) < len(ids):
                r = rj.xfer(data=b"\x00", ext=ext)
                if not r or r.get("type") is None:
                    continue
                for tag, pay in walk(r["ext"]):
                    if tag == 0x88:
                        i = (pay[0] << 8) | pay[1]
                        found[i] = (be32(pay[2:6]), be32(pay[6:10]))
                        got.add(i)
            silent += [i for i in ids if i not in got]
            print(f"  ids {ids[0]:#05x}-{ids[-1]:#05x}: {len(got)}/{len(ids)} answered", flush=True)
    finally:
        rj.close()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    json.dump({"answered": {str(k): {"a": v[0], "b": v[1]} for k, v in sorted(found.items())}, "silent": silent},
              open(f"diag_dump_{stamp}.json", "w"), indent=1)
    print(f"\n{len(found)} ids answered -> diag_dump_{stamp}.json")
    for k, (x, y) in sorted(found.items()):
        print(f"  {k:#05x}  a={x:<12} b={y}")


if __name__ == "__main__":
    main()
