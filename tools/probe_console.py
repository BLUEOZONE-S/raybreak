#!/usr/bin/env python3
"""
probe_console.py -- send ONE console command from the not-ready state and watch GS/GQ for a readiness change.

    python probe_console.py "RS0,0,0,0"      # sends \n\n\nRS0,0,0,0;  then polls GS, GQ, GE for ~7 s

Read-before/after design: records GS GQ GE GX GY GZ before, sends the one command, then polls for `--secs`.
Prints and logs (fuzz_logs/probe.jsonl) the before/after and whether GS flipped 1->0 (= activated).
Stops immediately and reports if the console stops answering (possible lock-up).
"""
import argparse, json, os, sys, time
import serial

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "fuzz_logs", "probe.jsonl")
GETTERS = ("GS", "GQ", "GE", "GX", "GY", "GZ")


def snap(s):
    out = {}
    for v in GETTERS:
        s.reset_input_buffer()
        s.write(b"\n\n\n" + v.encode() + b";")
        time.sleep(0.5)
        out[v] = s.read(120).decode(errors="replace").strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", help="console command WITHOUT the leading newlines or trailing ; e.g. RS0,0,0,0")
    ap.add_argument("--port", default="COM4")
    ap.add_argument("--secs", type=float, default=7)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    s = serial.Serial(a.port, 19200, 8, "N", 1, timeout=0.3)
    s.dtr = True; s.rts = True; time.sleep(0.3)
    before = snap(s)
    print("before:", before, flush=True)
    s.reset_input_buffer()
    s.write(b"\n\n\n" + a.cmd.encode() + b";")
    print(f"sent: {a.cmd!r}", flush=True)
    time.sleep(0.4)
    immediate = s.read(200).decode(errors="replace").strip()
    if immediate:
        print("immediate reply:", repr(immediate), flush=True)
    t0 = time.time(); after = before; flipped = False; lock = False
    while time.time() - t0 < a.secs:
        after = snap(s)
        if not any(after.values()):
            lock = True; break
        if after.get("GS") == "0" and before.get("GS") == "1":
            flipped = True; break
        if after != before:
            print(f"  t+{time.time()-t0:4.1f}s change: " +
                  ", ".join(f"{k} {before[k]!r}->{after[k]!r}" for k in GETTERS if before[k] != after[k]), flush=True)
        time.sleep(0.4)
    s.close()
    rec = {"time": time.strftime("%H:%M:%S"), "cmd": a.cmd, "before": before, "after": after,
           "immediate": immediate, "activated": flipped, "possible_lock": lock}
    open(LOG, "a").write(json.dumps(rec) + "\n")
    verdict = "ACTIVATED (GS 1->0)" if flipped else ("POSSIBLE LOCK (no console reply)" if lock else "no activation")
    print("RESULT:", verdict, "| after:", after, flush=True)
    sys.exit(0 if flipped else (2 if lock else 1))


if __name__ == "__main__":
    main()
