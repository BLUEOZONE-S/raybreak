#!/usr/bin/env python3
"""
laser_seq.py -- "enable + laser-flagged move" tests with the head parked at X = 10 mm. NO value-setting commands
other than the normal move speed (1A DA). You watch the laser's LASE light.

    python laser_seq.py                          # DRY RUN: list the trials
    python laser_seq.py --go --confirm LASER-CLEAR [--start N]

Phase 1: a move with the alternate move opcode 9F, 10 mm to the right (X 10 -> 20 mm) at three speeds.
Phase 2: each harmless no-argument command placed just before a 9F move in the same block.
After every trial the head returns to X = 10 mm with an ordinary 9E move; the sweep stops if the machine fails to
answer, a position/state is not as expected, or Y/Z change. Excluded: 85, AA-AE, B1, C9, CD, 0A 04, console commands.
"""
import argparse, json, os, sys, time
from rayjet_sf import Rayjet, be32
from laser_sweep import poll, params, stamp, PARK, NOISE, STOPFILE
import canary

PORT = "COM4"
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "fuzz_logs", "laser_seq.jsonl")
TARGET = PARK + 2000                 # +10 mm

def mvblock(op, x, v, pre=b""):
    return bytes([0x46, 0x00]) + pre + bytes([0x1A, 0xDA]) + be32(v) + bytes([op]) + be32(x) + be32(0) + bytes([0x86])

def trials():
    t = []
    for v in (3000, 1500, 600):
        t.append((f"P1 9F alone speed {v}", mvblock(0x9F, TARGET, v), v))
    for op in (0xC2, 0xC4, 0xC6, 0xC8, 0xB3, 0xB7, 0xBB, 0xBF, 0xC3, 0xC7, 0xCB, 0xCF, 0x32):
        t.append((f"P2 {op:02X} then 9F", mvblock(0x9F, TARGET, 1500, bytes([op])), 1500))
    return t

def wait_at(rj, x, secs=20):
    t0 = time.time()
    while time.time() - t0 < secs:
        p = poll(rj)
        if p and p.get("x") == x and not p.get("status", "").startswith("04"):
            return p
        time.sleep(0.05)
    return poll(rj)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--confirm", default="")
    ap.add_argument("--start", type=int, default=1)
    a = ap.parse_args()
    ts = trials()
    if not a.go:
        for i, (n, b, v) in enumerate(ts, 1):
            print(f"{i:2}  {n:24} {b.hex(' ')}")
        print(f"{len(ts)} trials. DRY RUN - nothing sent. Add --go --confirm LASER-CLEAR.")
        return 0
    if a.confirm != "LASER-CLEAR":
        print("Refusing: add --confirm LASER-CLEAR"); return 1
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if os.path.exists(STOPFILE): os.remove(STOPFILE)
    pre = canary.run(PORT)
    print(stamp(), "canary before:", pre["result"], flush=True)
    if pre["result"] != "PASS":
        print("ABORT: canary failed; nothing sent"); return 2
    rj = Rayjet(PORT, verbose=False).connect()
    code = 0
    try:
        rj.xfer(data=mvblock(0x9E, PARK, 3000), ext=bytes([0x10, 0x2C, 0x2E]))
        p0 = wait_at(rj, PARK)
        print(stamp(), "head parked at X=10 mm:", p0, flush=True)
        base = poll(rj); base_params = params(rj)
        for i, (name, block, v) in enumerate(ts, 1):
            if i < a.start: continue
            if os.path.exists(STOPFILE):
                print(stamp(), "STOP file found: stopping"); break
            print(f"{stamp()}  TRIAL {i:2}/{len(ts)}  {name:24}  MOVE 10->20 mm NOW   bytes: {block.hex(' ')}", flush=True)
            rj.xfer(data=block, ext=bytes([0x10, 0x2C, 0x2E]), timeout=1.5)
            p = wait_at(rj, TARGET)
            print(f"{stamp()}    move finished: {p}", flush=True)
            open(LOG, "a").write(json.dumps({"trial": i, "name": name, "bytes": block.hex(" "), "t": stamp(), "poll": p}) + "\n")
            if p is None or p.get("x") != TARGET or p.get("y") != base.get("y") or p.get("z") != base.get("z"):
                print(f"{stamp()}  >>> UNEXPECTED after trial {i} ({name}): {p}. STOP."); code = 3; break
            time.sleep(1.0)
            rj.xfer(data=mvblock(0x9E, PARK, 3000), ext=bytes([0x10, 0x2C, 0x2E]), timeout=1.5)
            q = wait_at(rj, PARK)
            if q is None or q.get("x") != PARK or q.get("z") != base.get("z"):
                print(f"{stamp()}  >>> could not return to 10 mm after trial {i} ({name}): {q}. STOP."); code = 4; break
            if i % 5 == 0:
                pr = params(rj)
                ch = [k for k in sorted(set(pr) | set(base_params)) if k not in NOISE and pr.get(k) != base_params.get(k)]
                print(f"{stamp()}  parameter changes: {ch or 'none'}", flush=True)
                if ch:
                    print(f"{stamp()}  >>> parameters changed after trial {i} ({name}). STOP."); code = 5; break
            time.sleep(1.0)
        else:
            print(stamp(), "all trials done")
        try:
            rj.xfer(data=mvblock(0x9E, 0, 3000), ext=bytes([0x10, 0x2C, 0x2E])); wait_at(rj, 0)
            print(stamp(), "head returned to X=0")
        except Exception as e:
            print("could not return head:", e)
    finally:
        rj.close()
    return code

if __name__ == "__main__":
    sys.exit(main())
