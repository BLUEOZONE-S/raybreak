#!/usr/bin/env python3
"""
laser_sweep.py -- slow, attributable sweep of the not-yet-understood command opcodes with the head PARKED at X = 10 mm.
You watch the laser's LASE light; every trial prints its exact time and bytes so a light can be matched to one command.

    python laser_sweep.py            # DRY RUN: lists the trials, sends nothing
    python laser_sweep.py --go --confirm LASER-CLEAR [--gap 3.0] [--start N]

Safety rules built in:
  * excluded and never sent: 85 (store), AA AB AC AE (licence), B1 (disturbed the machine), C9 (hangs the machine),
    88 (reply tag), and PD / any console command. Parameter writes (1A/1C/1E) are not part of this sweep.
  * one trial = one block  46 00 <command> 86  (or one value+enable pair), then a quiet gap with the link kept alive.
  * after every trial: the machine must answer a status poll, the state byte must still be idle (03) and the X/Y/Z
    counters must be unchanged. Any deviation stops the sweep immediately and says which trial did it.
  * every 6 trials: a small in-session canary move (X 2000 -> 2200 -> 2000) and a parameter-table comparison.
  * create a file named STOP next to this script to stop cleanly at the next gap. Ctrl+C also stops.
Uses COM4.
"""
import argparse, json, os, sys, time
from rayjet_sf import Rayjet, be32, parse_status
from rayjet_params import walk, be32 as b32
import canary

PORT = "COM4"
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "fuzz_logs", "laser_sweep.jsonl")
STOPFILE = os.path.join(HERE, "STOP")
PARK = 2000                          # 10 mm at 5 um/step
V = 37                               # distinctive small value
NOISE = {"52", "56", "57", "B8", "B6"}

def b16(v): return bytes([(v >> 8) & 255, v & 255])

def build_trials():
    t = []
    # A. commands with no arguments
    for op in (0xC2, 0xC4, 0xC6, 0xC8, 0xB3, 0xB7, 0xBB, 0xBF, 0xC3, 0xC7, 0xCB, 0xCD, 0xCF, 0x32):
        t.append((f"A {op:02X}", bytes([op])))
    # B. channel-code commands 0A and 0C with channels 1..4
    for op in (0x0A, 0x0C):
        for ch in (1, 2, 3, 4):
            t.append((f"B {op:02X} ch{ch}", bytes([op, ch])))
    # C. value commands not yet tried alone
    t.append(("C 80 be16", bytes([0x80]) + b16(V)))
    for op in (0x8A, 0x8C, 0x8E, 0x90):
        t.append((f"C {op:02X} be32", bytes([op]) + be32(V)))
    t.append(("C A2 3xbe32", bytes([0xA2]) + be32(V) + be32(0) + be32(0)))
    for op in (0x44, 0x16, 0xB8):
        t.append((f"C {op:02X} 1+be16", bytes([op, 1]) + b16(V)))
    # D. value + enable pairs, sent together in one block exactly as pairs
    t.append(("D B5+B7", bytes([0xB5]) + b16(V) + bytes([0xB7])))
    for a, b in ((0xB9, 0xBB), (0xBD, 0xBF), (0xC1, 0xC3), (0xC5, 0xC7)):
        t.append((f"D {a:02X}+{b:02X}", bytes([a]) + be32(V) + bytes([b])))
    return t

def poll(rj):
    r = rj.xfer(timeout=1.5)
    return parse_status(r["ext"]) if r and r.get("type") is not None else None

def params(rj):
    out = {}
    for base in range(0, 256, 16):
        reads = b"".join(bytes([0x20, i]) for i in range(base, base + 16))
        r = rj.xfer(data=b"\x00", ext=reads, timeout=1.5)
        for tag, pay in (walk(r["ext"]) if r and r.get("type") is not None else []):
            if tag == 0x21:
                out[f"{pay[0]:02X}"] = b32(pay[5:9])
    return out

def move(rj, x, op=0x9E, v=3000):
    blk = bytes([0x46, 0, 0x1A, 0xDA]) + be32(v) + bytes([op]) + be32(x) + be32(0) + bytes([0x86])
    rj.xfer(data=blk, ext=bytes([0x10, 0x2C, 0x2E]))
    t0 = time.time()
    while time.time() - t0 < 15:
        p = poll(rj)
        if p and p.get("x") == x and not p.get("status", "").startswith("04"):
            return p
        time.sleep(0.05)
    return poll(rj)

def stamp(): return time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--confirm", default="")
    ap.add_argument("--gap", type=float, default=3.0)
    ap.add_argument("--start", type=int, default=1)
    a = ap.parse_args()
    trials = build_trials()
    if not a.go:
        for i, (n, b) in enumerate(trials, 1):
            print(f"{i:2}  {n:14} 46 00 {b.hex(' ')} 86")
        print(f"{len(trials)} trials. DRY RUN - nothing sent. Add --go --confirm LASER-CLEAR.")
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
        p0 = move(rj, PARK)
        print(stamp(), "head parked at X=10 mm:", p0, flush=True)
        base = poll(rj); base_params = params(rj)
        print(stamp(), "baseline:", base, flush=True)
        for i, (name, body) in enumerate(trials, 1):
            if i < a.start: continue
            if os.path.exists(STOPFILE):
                print(stamp(), "STOP file found: stopping cleanly"); break
            block = bytes([0x46, 0x00]) + body + bytes([0x86])
            print(f"{stamp()}  TRIAL {i:2}/{len(trials)}  {name:14}  bytes: {block.hex(' ')}", flush=True)
            rj.xfer(data=block, ext=bytes([0x10, 0x2C, 0x2E]), timeout=1.5)
            p = poll(rj)
            rec = {"trial": i, "name": name, "bytes": block.hex(" "), "t": stamp(), "poll": p}
            open(LOG, "a").write(json.dumps(rec) + "\n")
            if p is None:
                print(f"{stamp()}  >>> NO REPLY after trial {i} ({name}). STOP. Machine may be hung: power-cycle."); code = 3; break
            if (p.get("status") != base.get("status")) or any(p.get(k) != base.get(k) for k in ("x", "y", "z")):
                print(f"{stamp()}  >>> STATE CHANGED after trial {i} ({name}): {p}  (baseline {base}). STOP."); code = 4; break
            if i % 6 == 0:
                m = move(rj, PARK + 200); m2 = move(rj, PARK)
                ok = m.get("x") == PARK + 200 and m2.get("x") == PARK and m2.get("y") == base.get("y")
                pr = params(rj)
                ch = [k for k in sorted(set(pr) | set(base_params)) if k not in NOISE and pr.get(k) != base_params.get(k)]
                print(f"{stamp()}  in-session canary: {'PASS' if ok else 'FAIL'}   parameter changes: {ch or 'none'}", flush=True)
                if not ok or ch:
                    print(f"{stamp()}  >>> canary/parameter problem after trial {i} ({name}). STOP."); code = 5; break
            t_end = time.time() + a.gap
            while time.time() < t_end:           # quiet gap, link kept alive
                time.sleep(0.3)
                if poll(rj) is None:
                    print(f"{stamp()}  >>> link lost during the gap after trial {i} ({name}). STOP."); code = 3; break
            if code: break
        else:
            print(stamp(), "all trials done")
        print(stamp(), "returning head to X=0", flush=True)
        try: move(rj, 0)
        except Exception as e: print("could not return head:", e)
    finally:
        rj.close()
    return code

if __name__ == "__main__":
    sys.exit(main())
