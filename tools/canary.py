#!/usr/bin/env python3
"""
canary.py -- health check: proves the machine is still in its working mode using the known-good left-right (X) move.

    python canary.py [--port COM4]        exit code 0 = PASS, 1 = FAIL, 2 = NOT READY (nothing sent)

Checks: GS = 0 and GE = 0, handshake, then X out 10 mm (2000 steps) and back; counters must reach the targets,
state byte must return to idle, Y and Z counters must not change.  Appends one JSON line to fuzz_logs/canary.jsonl.
"""
import argparse, json, os, sys, time
import serial
from rayjet_sf import Rayjet, be32, parse_status

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "fuzz_logs", "canary.jsonl")


def console(port, verb):
    s = serial.Serial(port, 19200, 8, "N", 1, timeout=0.3)
    s.dtr = True; s.rts = True
    try:
        time.sleep(0.3); s.reset_input_buffer()
        s.write(b"\n\n\n" + verb + b";"); time.sleep(0.7)
        return s.read(100).decode(errors="replace").strip()
    finally:
        s.close()


def run(port):
    rec = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "result": "FAIL", "why": ""}
    gs = ""
    for _ in range(25):                      # console is silent for a while after a packet session
        gs = console(port, b"GS")
        if gs in ("0", "1"):
            break
        time.sleep(3)
    rec["GS"] = gs
    if gs != "0":
        rec["result"] = "NOT_READY"; rec["why"] = f"GS={gs!r}"
        return rec
    rec["GE"] = console(port, b"GE")
    if rec["GE"] != "0":
        rec["why"] = f"GE={rec['GE']!r}"
        return rec
    rj = Rayjet(port, verbose=False).connect()
    try:
        def pos():
            r = rj.xfer()
            return parse_status(r["ext"]) if r and r.get("type") is not None else {}
        def move(x, y, v=3000):
            blk = bytes([0x46, 0, 0x1A, 0xDA]) + be32(v) + bytes([0x9E]) + be32(x) + be32(y) + bytes([0x86])
            rj.xfer(data=blk, ext=bytes([0x10, 0x2C, 0x2E]))
            t0 = time.time()
            while time.time() - t0 < 15:
                p = pos()
                if p.get("x") == x and p.get("y") == y and not p.get("status", "").startswith("04"):
                    return p
                time.sleep(0.05)
            return pos()
        p0 = pos(); rec["start"] = p0
        if not p0 or p0.get("x") is None:
            rec["why"] = "no status"; return rec
        x0, y0, z0 = p0["x"], p0["y"], p0["z"]
        p1 = move(x0 + 2000, y0); rec["out"] = p1
        p2 = move(x0, y0); rec["back"] = p2
        ok = (p1.get("x") == x0 + 2000 and p2.get("x") == x0 and p1.get("y") == y0 and p2.get("y") == y0
              and p1.get("z") == z0 and p2.get("z") == z0 and p2.get("status", "").startswith("03"))
        rec["result"] = "PASS" if ok else "FAIL"
        if not ok:
            rec["why"] = "counters/state did not match"
    finally:
        rj.close()
    return rec


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--port", default="COM4"); a = ap.parse_args()
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    rec = run(a.port)
    open(LOG, "a").write(json.dumps(rec) + "\n")
    print(time.strftime("%H:%M:%S"), "CANARY", rec["result"], rec.get("why", ""), "| start", rec.get("start"), "| out", rec.get("out"), "| back", rec.get("back"))
    sys.exit({"PASS": 0, "NOT_READY": 2}.get(rec["result"], 1))
