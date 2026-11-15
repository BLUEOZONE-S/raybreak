#!/usr/bin/env python3
"""
laser_job.py -- "job pattern" tests: <set value> + <its enable> + a 9F move in ONE block, head parked at X = 10 mm.
Value is the smallest non-zero value (1) so that, whatever its scale, power is as low as it can be. You watch the LASE light.

    python laser_job.py                       # DRY RUN: lists the trials
    python laser_job.py --go --confirm LASER-CLEAR [--start N] [--value V]

Pairs tried (set, enable): B5+B7 (16-bit), B9+BB, BD+BF, C1+C3, C5+C7 (32-bit). Excluded (disturbed the machine): B1, C9, CD, C6, B3 alone.
After each trial the head returns to X = 10 mm with an ordinary 9E move. Stops at the first anomaly.
"""
import argparse, json, os, sys, time
from rayjet_sf import Rayjet, be32
from laser_sweep import poll, params, stamp, PARK, NOISE, STOPFILE
from laser_seq import wait_at, TARGET
import canary

PORT = "COM4"
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "fuzz_logs", "laser_job.jsonl")

def b16(v): return bytes([(v >> 8) & 255, v & 255])

def move_part(op, x, v):
    return bytes([0x1A, 0xDA]) + be32(v) + bytes([op]) + be32(x) + be32(0)

def trials(val):
    t = []
    t.append(("J1 B5(16) + B7", bytes([0xB5]) + b16(val) + bytes([0xB7])))
    for s, e in ((0xB9, 0xBB), (0xBD, 0xBF), (0xC1, 0xC3), (0xC5, 0xC7)):
        t.append((f"J {s:02X}(32) + {e:02X}", bytes([s]) + be32(val) + bytes([e])))
    return t

def block(prefix, op, x, v):
    return bytes([0x46, 0x00]) + prefix + move_part(op, x, v) + bytes([0x86])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--confirm", default="")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--value", type=int, default=1)
    a = ap.parse_args()
    ts = trials(a.value)
    if not a.go:
        for i, (n, p) in enumerate(ts, 1):
            print(f"{i}  {n:16} {block(p, 0x9F, TARGET, 1500).hex(' ')}")
        print("DRY RUN - nothing sent. Add --go --confirm LASER-CLEAR.")
        return 0
    if a.confirm != "LASER-CLEAR":
        print("Refusing: add --confirm LASER-CLEAR"); return 1
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if os.path.exists(STOPFILE): os.remove(STOPFILE)
    pre = canary.run(PORT); print(stamp(), "canary before:", pre["result"], flush=True)
    if pre["result"] != "PASS":
        print("ABORT: canary failed; nothing sent"); return 2
    rj = Rayjet(PORT, verbose=False).connect()
    code = 0
    try:
        rj.xfer(data=block(b"", 0x9E, PARK, 3000), ext=bytes([0x10, 0x2C, 0x2E]))
        print(stamp(), "head parked at X=10 mm:", wait_at(rj, PARK), flush=True)
        base = poll(rj); base_params = params(rj)
        for i, (name, pre_) in enumerate(ts, 1):
            if i < a.start: continue
            if os.path.exists(STOPFILE): print(stamp(), "STOP file: stopping"); break
            blk = block(pre_, 0x9F, TARGET, 1500)
            print(f"{stamp()}  TRIAL {i}/{len(ts)}  {name:16}  MOVE 10->20 mm NOW  value={a.value}  bytes: {blk.hex(' ')}", flush=True)
            rj.xfer(data=blk, ext=bytes([0x10, 0x2C, 0x2E]), timeout=1.5)
            p = wait_at(rj, TARGET)
            print(f"{stamp()}    after: {p}", flush=True)
            open(LOG, "a").write(json.dumps({"trial": i, "name": name, "bytes": blk.hex(" "), "t": stamp(), "poll": p}) + "\n")
            if p is None or p.get("x") != TARGET or p.get("y") != base.get("y") or p.get("z") != base.get("z") or p.get("status") != base.get("status"):
                print(f"{stamp()}  >>> UNEXPECTED after trial {i} ({name}): {p}. STOP."); code = 3; break
            time.sleep(1.0)
            rj.xfer(data=block(b"", 0x9E, PARK, 3000), ext=bytes([0x10, 0x2C, 0x2E]), timeout=1.5)
            q = wait_at(rj, PARK)
            if q is None or q.get("x") != PARK:
                print(f"{stamp()}  >>> could not return to 10 mm after trial {i}: {q}. STOP."); code = 4; break
            pr = params(rj)
            ch = [k for k in sorted(set(pr) | set(base_params)) if k not in NOISE and pr.get(k) != base_params.get(k)]
            print(f"{stamp()}    parameter changes: {ch or 'none'}", flush=True)
            if ch:
                print(f"{stamp()}  >>> parameters changed after trial {i}. STOP."); code = 5; break
            time.sleep(1.5)
        else:
            print(stamp(), "all trials done")
        try:
            rj.xfer(data=block(b"", 0x9E, 0, 3000), ext=bytes([0x10, 0x2C, 0x2E])); wait_at(rj, 0); print(stamp(), "head returned to X=0")
        except Exception as e:
            print("could not return head:", e)
    finally:
        rj.close()
    return code

if __name__ == "__main__":
    sys.exit(main())
