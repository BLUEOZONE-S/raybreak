#!/usr/bin/env python3
"""
laser_probe.py -- STAGED, one-change-at-a-time tester to find which packet command sets the laser power,
using the controller's own readbacks (GP LASER_POWER, parameter table, diagnostics, status) as feedback.

It NEVER sends an enable/gate opcode and NEVER sends a move that is meant to fire. Every stage here is a
"set a value" candidate sent ALONE, then compared against a before-snapshot. If LASER_POWER (or anything else)
changes, that opcode is the power setter, found without firing anything.

    python laser_probe.py --list                       # show the stages, send nothing
    python laser_probe.py --stage S0                   # DRY RUN: show exactly what would be sent (default)
    python laser_probe.py --stage W1 --go --confirm LASER-CLEAR   # really run ONE stage

Rules built in: refuses unless GS=0 and the X canary passes before the stage; runs the canary again after; logs
everything to fuzz_logs/laser_stages.jsonl; stops on any failure and tells you to power-cycle. Stages are
independent; power-cycle the machine between any stage that changed something.
Uses COM4. Forbidden and not implemented: opcode 85 (store), AA/AB/AC/AE (licence), PD, any enable/gate opcode.
"""
import argparse, json, os, sys, time
import serial
from rayjet_sf import Rayjet, be32, parse_status
from rayjet_params import walk, be32 as b32
import canary

PORT = "COM4"
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "fuzz_logs", "laser_stages.jsonl")
NOISE_PARAMS = {"52", "56", "57", "B8"}          # counters that drift on their own
PROBE_VALUE = 37                                  # distinctive small value

def b16(v): return bytes([(v >> 8) & 255, v & 255])

# stage name -> (description, bytes of the data block body, sent between '46 00' and '86')
STAGES = {
    "S0": ("noise baseline: two snapshots, nothing sent", b""),
    "W1": ("write parameter 0x4A (tickle delay) with its CURRENT value 350: proves the 1C write path is harmless",
           bytes([0x1C, 0x4A]) + b16(350)),
    "P-B5": ("candidate 'set value' opcode B5 (16-bit) = 37, alone", bytes([0xB5]) + b16(PROBE_VALUE)),
    "P-B9": ("candidate 'set value' opcode B9 (32-bit) = 37, alone", bytes([0xB9]) + be32(PROBE_VALUE)),
    "P-BD": ("candidate 'set value' opcode BD (32-bit) = 37, alone", bytes([0xBD]) + be32(PROBE_VALUE)),
    "P-C1": ("candidate 'set value' opcode C1 (32-bit) = 37, alone", bytes([0xC1]) + be32(PROBE_VALUE)),
    "P-C5": ("candidate 'set value' opcode C5 (32-bit) = 37, alone", bytes([0xC5]) + be32(PROBE_VALUE)),
    "P-C9": ("candidate 'set value' opcode C9 (8-bit) = 37, alone", bytes([0xC9, PROBE_VALUE])),
    "P-B1": ("candidate 'set value' opcode B1 (32-bit) = 37, alone. KNOWN to disturb the machine (Z counter jumped once): run LAST",
             bytes([0xB1]) + be32(PROBE_VALUE)),
}
ORDER = ["S0", "W1", "P-B5", "P-B9", "P-BD", "P-C1", "P-C5", "P-C9", "P-B1"]


def console(verb, wait=0.8):
    s = serial.Serial(PORT, 19200, 8, "N", 1, timeout=0.3); s.dtr = True; s.rts = True
    try:
        time.sleep(0.3); s.reset_input_buffer()
        s.write(b"\n\n\n" + verb + b";"); time.sleep(wait)
        return s.read(400).decode(errors="replace").strip()
    finally:
        s.close()


def wait_console():
    for _ in range(30):                           # console is silent for a while after a packet session
        if console(b"GS") in ("0", "1"):
            return True
        time.sleep(3)
    return False


def gp():
    out = {}
    for line in console(b"GP", 1.0).replace("\r", "").split("\n"):
        if ":" in line and not line.upper().startswith("CPU_ID"):    # never record the CPU id
            k, v = line.split(":", 1); out[k.strip()] = v.strip()
    return out


def snapshot(rj):
    snap = {"params": {}, "diag": {}, "poll": None}
    r = rj.xfer()
    if r and r.get("type") is not None:
        snap["poll"] = r["ext"].hex(" ")
    for base in range(0, 256, 16):
        reads = b"".join(bytes([0x20, i]) for i in range(base, base + 16))
        r = rj.xfer(data=b"\x00", ext=reads)
        for tag, pay in (walk(r["ext"]) if r and r.get("type") is not None else []):
            if tag == 0x21:
                snap["params"][f"{pay[0]:02X}"] = b32(pay[5:9])
    ext = b"".join(bytes([0x87, 0, i]) for i in range(9))
    r = rj.xfer(data=b"\x00", ext=ext)
    for tag, pay in (walk(r["ext"]) if r and r.get("type") is not None else []):
        if tag == 0x88:
            snap["diag"][f"{pay[1]:02X}"] = [b32(pay[2:6]), b32(pay[6:10])]
    return snap


def diff(a, b):
    out = []
    for k in sorted(set(a["params"]) | set(b["params"])):
        if k not in NOISE_PARAMS and a["params"].get(k) != b["params"].get(k):
            out.append(f"param {k}: {a['params'].get(k)} -> {b['params'].get(k)}")
    for k in sorted(set(a["diag"]) | set(b["diag"])):
        if k == "08":
            continue
        if a["diag"].get(k) != b["diag"].get(k):
            out.append(f"diag {k}: {a['diag'].get(k)} -> {b['diag'].get(k)}")
    if a["poll"] != b["poll"]:
        out.append(f"status poll: {a['poll']} -> {b['poll']}")
    return out


def run_stage(name, go):
    desc, body = STAGES[name]
    block = bytes([0x46, 0x00]) + body + bytes([0x86]) if body else b""
    print(f"STAGE {name}: {desc}")
    print("  data block:", block.hex(" ") if block else "(none)")
    if not go:
        print("  DRY RUN - nothing sent. Add --go --confirm LASER-CLEAR to run this one stage.")
        return 0
    rec = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "stage": name, "block": block.hex(" ")}
    if not wait_console() or console(b"GS") != "0":
        print("ABORT: machine not ready (GS != 0)"); return 2
    rec["gp_before"] = gp()
    print("  GP before:", rec["gp_before"])
    pre = canary.run(PORT); rec["canary_before"] = pre["result"]
    print("  canary before:", pre["result"])
    if pre["result"] != "PASS":
        print("ABORT: canary failed before the stage; nothing sent"); return 3
    rj = Rayjet(PORT, verbose=False).connect()
    try:
        snap_a = snapshot(rj)
        if block:
            print(time.strftime("%H:%M:%S"), "SENDING", block.hex(" "), flush=True)
            rj.xfer(data=block, ext=bytes([0x10, 0x2C, 0x2E]))
            time.sleep(1.0)
        else:
            time.sleep(1.0)
        snap_b = snapshot(rj)
    finally:
        rj.close()
    rec["diff"] = diff(snap_a, snap_b)
    print("  changes in params/diag/status:", rec["diff"] or "none")
    if not wait_console():
        print("WARNING: console did not return; power-cycle may be needed")
    rec["gp_after"] = gp()
    print("  GP after: ", rec["gp_after"])
    gp_diff = {k: (rec["gp_before"].get(k), rec["gp_after"].get(k)) for k in rec["gp_after"]
               if rec["gp_before"].get(k) != rec["gp_after"].get(k)}
    rec["gp_diff"] = gp_diff
    print("  GP differences:", gp_diff or "none")
    post = canary.run(PORT); rec["canary_after"] = post["result"]
    print("  canary after:", post["result"], post.get("why", ""))
    open(LOG, "a").write(json.dumps(rec) + "\n")
    if post["result"] != "PASS":
        print(">>> CANARY FAILED after this stage. Stop. Power-cycle and restore the working mode before anything else.")
        return 4
    if rec["diff"] or gp_diff:
        print(">>> This stage CHANGED something. Record it, then power-cycle before the next stage.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--stage", choices=ORDER)
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--confirm", default="")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if a.list or not a.stage:
        for n in ORDER:
            print(f"{n:5} {STAGES[n][0]}")
        sys.exit(0)
    if a.go and a.confirm != "LASER-CLEAR":
        print("Refusing: add --confirm LASER-CLEAR to confirm the setup is safe (beam contained, covers closed, observer ready)")
        sys.exit(1)
    sys.exit(run_stage(a.stage, a.go and a.confirm == "LASER-CLEAR"))
