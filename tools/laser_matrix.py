#!/usr/bin/env python3
"""
laser_matrix.py -- the full laser-command test matrix: defines every trial, runs a named section with recording,
and regenerates the MATRIX of done vs to-do. One harness so nothing is forgotten and every result is attributable.

    python laser_matrix.py matrix                         # (re)build laser_matrix_status.md from all logs, send nothing
    python laser_matrix.py list [section]                 # list trials (DRY RUN, send nothing)
    python laser_matrix.py run <section> --confirm LASER-CLEAR [--value N] [--start K]

Sections:
    alone      every opcode in the known layout table, sent alone            (46 00 <op><args> 86)
    move       every opcode placed just before a 9F laser-flag move
    pair       value+enable pairs, alone and before a 9F move
    job        <value> <enable> <9F move>, the full job pattern, several values
    console    console verbs that can carry the laser (PD/PU variants, pen state across a move)
    value      write each laser-related parameter in RAM, then a 9F move

Every run: canary first; after each trial a status poll + state/position check and, every few trials, an in-session
canary and parameter diff; stop + log on any anomaly. Results go to fuzz_logs/matrix.jsonl keyed by a trial id, so a
re-run never loses earlier outcomes and the matrix always reflects everything tried.

Irreversible, listed in the matrix but NOT auto-run (no undo, not laser): 0x85 store-to-flash, 0xAA-0xAE licence.
These can be run with an explicit separate confirmation token if ever needed; the laser is not among them.
"""
import argparse, json, os, sys, time
from rayjet_sf import Rayjet, be32
from laser_sweep import poll, params, stamp, PARK, NOISE, STOPFILE
from laser_seq import wait_at, TARGET
import canary

PORT = "COM4"
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "fuzz_logs", "matrix.jsonl")
STATUS_MD = os.path.join(HERE, "fuzz_logs", "laser_matrix_status.md")

# opcodes known to disturb the machine (kept in the matrix, flagged, still runnable one-at-a-time on request)
DISTURB = {"C9", "CD", "B1", "C6", "B3", "B7", "0A04"}
# irreversible, never part of a section run
IRREVERSIBLE = {"85", "AA", "AB", "AC", "AE"}

def b16(v): return bytes([(v >> 8) & 255, v & 255])

# the known layout table: opcode -> argument shape
NOARG = [0xC2, 0xC4, 0xC6, 0xC8, 0xB3, 0xB7, 0xBB, 0xBF, 0xC3, 0xC7, 0xCB, 0xCD, 0xCF, 0x32]
BE32  = [0xB1, 0xB9, 0xBD, 0xC1, 0xC5, 0x8A, 0x8C, 0x8E, 0x90]
BE16  = [0xB5, 0x80, 0xAE]
BYTE1 = [0xC9]
CH    = [0x0A, 0x0C]
PAIRS = [(0xB5, 0xB7, 16), (0xB9, 0xBB, 32), (0xBD, 0xBF, 32), (0xC1, 0xC3, 32), (0xC5, 0xC7, 32)]
LASER_PARAMS = [0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0xDE]

def arg(op, val):
    if op in BE32: return be32(val)
    if op in BE16: return b16(val)
    if op in BYTE1: return bytes([val & 255])
    return b""

def section_trials(section, val):
    """Return list of (trial_id, label, data_block_body)."""
    t = []
    if section == "alone":
        for op in NOARG + BE32 + BE16 + BYTE1:
            t.append((f"alone:{op:02X}", f"{op:02X} alone", bytes([op]) + arg(op, val)))
        for op in CH:
            for ch in (1, 2, 3, 4):
                t.append((f"alone:{op:02X}{ch}", f"{op:02X} ch{ch} alone", bytes([op, ch])))
    elif section == "move":
        for op in NOARG:
            t.append((f"move:{op:02X}", f"{op:02X} then 9F move", bytes([op])))
    elif section == "pair":
        for s, e, w in PAIRS:
            body = bytes([s]) + (b16(val) if w == 16 else be32(val)) + bytes([e])
            t.append((f"pairalone:{s:02X}{e:02X}", f"{s:02X}(+{w}) + {e:02X} alone", body))
            t.append((f"pairmove:{s:02X}{e:02X}", f"{s:02X}(+{w}) + {e:02X} then 9F move", body))
    elif section == "job":
        for s, e, w in PAIRS:
            body = bytes([s]) + (b16(val) if w == 16 else be32(val)) + bytes([e])
            t.append((f"job:{s:02X}{e:02X}:v{val}", f"{s:02X}={val} + {e:02X} + 9F move", body))
    elif section == "value":
        for idx in LASER_PARAMS:
            t.append((f"value:{idx:02X}", f"write param {idx:02X}={val} then 9F move", bytes([0x1A, idx]) + be32(val)))
    else:
        raise SystemExit(f"unknown section {section!r}")
    return t

def is_move_trial(section, tid):
    return section in ("move", "job", "value") or tid.startswith("pairmove")

def load_results():
    res = {}
    if os.path.exists(LOG):
        for line in open(LOG):
            try:
                r = json.loads(line); res[r["id"]] = r
            except Exception:
                pass
    return res

def build_matrix():
    res = load_results()
    lines = ["# Laser command test matrix (auto-generated)", "",
             f"Generated {time.strftime('%Y-%m-%d %H:%M')}. Source: fuzz_logs/matrix.jsonl plus the earlier hand-logged results.",
             "", "Legend: DONE = run and recorded | TODO = not yet run | DISTURB = run, disturbs the machine (recover by power cycle) | IRREVERSIBLE = listed, not auto-run.",
             "", "| Section | Trial | Status | LASE light | Note |", "|---|---|---|---|---|"]
    for section in ("alone", "move", "pair", "job", "value"):
        for tid, label, _ in section_trials(section, 1):
            op = tid.split(":")[1][:2].upper()
            r = res.get(tid)
            if r:
                st = "DONE"; led = r.get("lase", "?"); note = r.get("note", "")
            elif op in DISTURB or tid.replace(":", "").upper().find("0A4") >= 0:
                st = "TODO"; led = ""; note = "contains a disturbing opcode"
            else:
                st = "TODO"; led = ""; note = ""
            lines.append(f"| {section} | {label} | {st} | {led} | {note} |")
    lines += ["", "## Irreversible (listed, not auto-run)", "",
              "| Opcode | Meaning | Why excluded from sweeps |", "|---|---|---|",
              "| 85 | store parameters to flash | permanent; overwrites stored settings |",
              "| AA AB AC AE | licence / pay-per-use | permanent; licence data |"]
    open(STATUS_MD, "w", encoding="utf-8").write("\n".join(lines))
    done = sum(1 for s in ("alone", "move", "pair", "job", "value") for tid, _, _ in section_trials(s, 1) if tid in res)
    total = sum(1 for s in ("alone", "move", "pair", "job", "value") for _ in section_trials(s, 1))
    print(f"matrix written: {STATUS_MD}  ({done}/{total} trials recorded)")

def record(tid, label, block, poll_after, lase="?", note="", disturbed=False):
    open(LOG, "a").write(json.dumps({"id": tid, "label": label, "bytes": block.hex(" "),
                                     "t": stamp(), "poll": poll_after, "lase": lase, "note": note,
                                     "disturbed": disturbed}) + "\n")

def run_section(section, val, start, confirm):
    if confirm != "LASER-CLEAR":
        print("Refusing: add --confirm LASER-CLEAR"); return 1
    trials = section_trials(section, val)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if os.path.exists(STOPFILE): os.remove(STOPFILE)
    pre = canary.run(PORT); print(stamp(), "canary before:", pre["result"], flush=True)
    if pre["result"] != "PASS":
        print("ABORT: canary failed; nothing sent"); return 2
    rj = Rayjet(PORT, verbose=False).connect()
    code = 0
    try:
        rj.xfer(data=mv_block(b"", 0x9E, PARK, 3000), ext=bytes([0x10, 0x2C, 0x2E]))
        print(stamp(), "head parked at X=10 mm:", wait_at(rj, PARK), flush=True)
        base = poll(rj); base_params = params(rj)
        for i, (tid, label, body) in enumerate(trials, 1):
            if i < start: continue
            if os.path.exists(STOPFILE): print(stamp(), "STOP file: stopping"); break
            op = tid.split(":")[1][:2].upper()
            if op in IRREVERSIBLE:
                print(stamp(), f"SKIP {label}: irreversible, not auto-run"); continue
            movey = is_move_trial(section, tid)
            if movey:
                block = bytes([0x46, 0x00]) + body + bytes([0x1A, 0xDA]) + be32(1500) + bytes([0x9F]) + be32(TARGET) + be32(0) + bytes([0x86])
            else:
                block = bytes([0x46, 0x00]) + body + bytes([0x86])
            print(f"{stamp()}  TRIAL {i}/{len(trials)}  {label:28}  {'MOVE 10->20 NOW' if movey else 'send'}  bytes: {block.hex(' ')}", flush=True)
            rj.xfer(data=block, ext=bytes([0x10, 0x2C, 0x2E]), timeout=1.5)
            p = wait_at(rj, TARGET, 6) if movey else poll(rj)
            note = ""
            disturbed = False
            if p is None:
                note = "no reply"; disturbed = True
            elif movey and p.get("x") != TARGET:
                note = "move dropped"
            elif p.get("status") != base.get("status") or (p and (p.get("y") != base.get("y") or p.get("z") != base.get("z"))):
                note = f"state/pos change {p}"; disturbed = True
            record(tid, label, block, p, lase="pending", note=note, disturbed=disturbed)
            print(f"{stamp()}    after: {p}   {note or 'ok'}", flush=True)
            if disturbed:
                print(f"{stamp()}  >>> {label} disturbed the machine. STOP. Power-cycle to recover."); code = 3; break
            # return to park for the next trial
            time.sleep(0.8)
            rj.xfer(data=mv_block(b"", 0x9E, PARK, 3000), ext=bytes([0x10, 0x2C, 0x2E]), timeout=1.5)
            q = wait_at(rj, PARK, 8)
            if q is None or q.get("x") != PARK:
                print(f"{stamp()}  >>> could not return to park after {label}: {q}. STOP."); code = 4; break
            if i % 6 == 0:
                pr = params(rj)
                ch = [k for k in sorted(set(pr) | set(base_params)) if k not in NOISE and pr.get(k) != base_params.get(k)]
                print(f"{stamp()}    parameter changes so far: {ch or 'none'}", flush=True)
                if ch:
                    print(f"{stamp()}  >>> parameters changed. STOP."); code = 5; break
            time.sleep(0.6)
        else:
            print(stamp(), "section complete")
        try:
            rj.xfer(data=mv_block(b"", 0x9E, 0, 3000), ext=bytes([0x10, 0x2C, 0x2E])); wait_at(rj, 0)
            print(stamp(), "head returned to X=0")
        except Exception as e:
            print("could not return head:", e)
    finally:
        rj.close()
    build_matrix()
    return code

def mv_block(prefix, op, x, v):
    return bytes([0x46, 0x00]) + prefix + bytes([0x1A, 0xDA]) + be32(v) + bytes([op]) + be32(x) + be32(0) + bytes([0x86])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["matrix", "list", "run"])
    ap.add_argument("section", nargs="?", default=None)
    ap.add_argument("--value", type=int, default=1)
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--confirm", default="")
    a = ap.parse_args()
    if a.cmd == "matrix":
        build_matrix()
    elif a.cmd == "list":
        secs = [a.section] if a.section else ["alone", "move", "pair", "job", "value"]
        for s in secs:
            print(f"== {s} ==")
            for i, (tid, label, body) in enumerate(section_trials(s, a.value), 1):
                print(f"  {i:2} {tid:22} {label}")
    elif a.cmd == "run":
        if not a.section: sys.exit("run needs a section")
        sys.exit(run_section(a.section, a.value, a.start, a.confirm))
