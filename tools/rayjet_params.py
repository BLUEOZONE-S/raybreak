#!/usr/bin/env python3
"""
rayjet_params.py -- READ-ONLY dump of the machine's parameter table (the "FRAM").

How it works:
  host -> machine   0x20 <index>            read parameter <index>   (16 at a time works well)
  machine -> host   tag 0x21 <index> <be32 a> <be32 b>   reply; 'b' is the value
  host -> machine   0x1A <index> <be32>     WRITE parameter (e.g. 1A DA = move speed)   <-- this script never sends it
  host -> machine   0x85                    store to FRAM                               <-- never sent either

Run it when the machine is READY (Z buttons alive).  It sends only read requests.

    python rayjet_params.py                    # indices 0..0x12F, writes params_dump_<time>.json and .md
    python rayjet_params.py --last 0x40        # only 0..0x40
"""
import argparse, json, time
from rayjet_sf import Rayjet

# payload length (bytes after the tag byte) of the reply tags we understand
TAG_LEN = {0x0F: 2, 0x11: 4, 0x21: 9, 0x2D: 8, 0x2F: 4, 0x43: 0, 0x88: 10, 0xA1: 0, 0xA5: 2, 0xAB: 5, 0xAD: 0, 0xAF: 0,
           0xB4: 4, 0xB8: 2, 0xBC: 4, 0xC0: 4, 0xC4: 4, 0xC8: 4, 0xCC: 1}


def walk(ext):
    """Split a reply's ext block into (tag, payload) items; stop at the first unknown tag."""
    i, out = 0, []
    while i < len(ext):
        t = ext[i]
        if t not in TAG_LEN:
            out.append(("unknown", ext[i:].hex(" ")))
            break
        n = TAG_LEN[t]
        out.append((t, ext[i + 1:i + 1 + n]))
        i += 1 + n
    return out


def be32(b):
    return int.from_bytes(b, "big")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=lambda s: int(s, 0), default=0xFF)   # one-byte index: 0x00-0xFF
    a = ap.parse_args()

    rj = Rayjet("COM3", verbose=False).connect()
    params, other = {}, {}
    try:
        for base in range(0, a.last + 1, 16):
            idxs = [i for i in range(base, base + 16) if i <= a.last]
            reads = b"".join(bytes([0x20, i]) for i in idxs)      # parameter reads go in the EXT part
            got = set()
            r0 = rj.xfer(data=b"\x00", ext=reads)       # the machine answers in the SAME reply packet
            for tag, pay in (walk(r0["ext"]) if r0 and r0.get("type") is not None else []):
                if tag == 0x21:
                    params[pay[0]] = (be32(pay[1:5]), be32(pay[5:9])); got.add(pay[0])
            t0 = time.time()
            while time.time() - t0 < 2.0 and len(got) < len(idxs):
                r = rj.xfer(data=b"\x00", ext=bytes([0x10]))
                if not r or r.get("type") is None:
                    continue
                for tag, pay in walk(r["ext"]):
                    if tag == 0x21:
                        params[pay[0]] = (be32(pay[1:5]), be32(pay[5:9]))
                        got.add(pay[0])
                    elif tag == "unknown":
                        other.setdefault("unknown", []).append(pay)
                    else:
                        other[hex(tag)] = pay.hex(" ")
            print(f"  indices {idxs[0]:#04x}-{idxs[-1]:#04x}: {len(got)}/{len(idxs)} replies", flush=True)
    finally:
        rj.close()

    stamp = time.strftime("%Y%m%d_%H%M%S")
    with open(f"params_dump_{stamp}.json", "w") as f:
        json.dump({"params": {str(k): {"a": v[0], "b": v[1]} for k, v in sorted(params.items())}, "other_tags": other}, f, indent=1)
    with open(f"params_dump_{stamp}.md", "w") as f:
        f.write("# Machine parameter dump\n\n| idx | hex | a | b (value) |\n|---|---|---|---|\n")
        for k, (x, y) in sorted(params.items()):
            f.write(f"| {k} | {k:#04x} | {x} | {y} |\n")
    print(f"\n{len(params)} parameters -> params_dump_{stamp}.json / .md")


if __name__ == "__main__":
    main()
