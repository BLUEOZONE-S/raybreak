#!/usr/bin/env python3
"""
snapshot.py -- READ-ONLY machine snapshot. Sends only getters and read requests; moves nothing, writes nothing.

    python snapshot.py <label> [--port COM4] [--diag-last 0x3FF]

Writes fuzz_logs/snap_<label>_<time>.json with:
  console : GS GE GF GQ GX GY GZ replies (always)
  packet  : handshake string, raw status ext, state bytes, X/Y/Z, parameters 0..255, diagnostic ids (only if GS = 0)
"""
import argparse, json, os, sys, time
import serial
from rayjet_sf import Rayjet
from rayjet_params import walk, be32

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "fuzz_logs")


def console_all(port, verbs=("GS", "GE", "GF", "GQ", "GX", "GY", "GZ")):
    out = {}
    s = serial.Serial(port, 19200, 8, "N", 1, timeout=0.3)
    s.dtr = True; s.rts = True
    try:
        time.sleep(0.3)
        for v in verbs:
            s.reset_input_buffer()
            s.write(b"\n\n\n" + v.encode() + b";")
            time.sleep(0.7)
            out[v] = s.read(300).decode(errors="replace").strip()
    finally:
        s.close()
    return out


def packet_part(port, diag_last):
    rj = Rayjet(port, verbose=False).connect()
    res = {"handshake": rj.fw, "polls": [], "params": {}, "diag": {}, "unknown": []}
    try:
        for _ in range(3):
            r = rj.xfer()
            if r and r.get("type") is not None:
                res["polls"].append(r["ext"].hex(" "))
            time.sleep(0.1)
        for base in range(0, 256, 16):
            reads = b"".join(bytes([0x20, i]) for i in range(base, base + 16))
            r = rj.xfer(data=b"\x00", ext=reads)
            for tag, pay in (walk(r["ext"]) if r and r.get("type") is not None else []):
                if tag == 0x21:
                    res["params"][f"{pay[0]:02X}"] = [be32(pay[1:5]), be32(pay[5:9])]
                elif tag == "unknown":
                    res["unknown"].append(pay)
        for base in range(0, diag_last + 1, 8):
            ids = range(base, min(base + 8, diag_last + 1))
            ext = b"".join(bytes([0x87, i >> 8, i & 255]) for i in ids)
            r = rj.xfer(data=b"\x00", ext=ext)
            for tag, pay in (walk(r["ext"]) if r and r.get("type") is not None else []):
                if tag == 0x88:
                    i = (pay[0] << 8) | pay[1]
                    res["diag"][f"{i:04X}"] = [be32(pay[2:6]), be32(pay[6:10])]
                elif tag == "unknown":
                    res["unknown"].append(pay)
        r = rj.xfer()
        if r and r.get("type") is not None:
            res["polls"].append(r["ext"].hex(" "))
    finally:
        rj.close()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("--port", default="COM4")
    ap.add_argument("--diag-last", type=lambda s: int(s, 0), default=0x1F)
    a = ap.parse_args()
    os.makedirs(LOGS, exist_ok=True)
    snap = {"label": a.label, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "port": a.port}
    for attempt in range(25):                      # after a packet session the console stays silent for a while
        snap["console"] = console_all(a.port, ("GS",))
        if snap["console"].get("GS") in ("0", "1"):
            break
        time.sleep(3)
    snap["console_wait_tries"] = attempt
    snap["console"] = console_all(a.port)
    print("console:", snap["console"], flush=True)
    if snap["console"].get("GS") == "0":
        snap["packet"] = packet_part(a.port, a.diag_last)
        p = snap["packet"]
        print(f"handshake {p['handshake']}  polls {p['polls'][0] if p['polls'] else None}", flush=True)
        print(f"params {len(p['params'])}  diag ids with data {len(p['diag'])}  unknown {len(p['unknown'])}", flush=True)
    else:
        print("GS is not 0: packet part skipped (machine not ready or still in packet mode)", flush=True)
    fn = os.path.join(LOGS, f"snap_{a.label}_{time.strftime('%Y%m%d_%H%M%S')}.json")
    json.dump(snap, open(fn, "w"), indent=1)
    print("wrote", fn)


if __name__ == "__main__":
    main()
