#!/usr/bin/env python3
"""
console_watch.py -- READ-ONLY console watcher for the not-ready -> ready transition.

    python console_watch.py [--port COM4] [--secs 180]

Polls the getters GS GE GX GY GZ GQ GF in a loop (about 3 cycles per second), prints a line whenever any reply
changes, and logs every raw reply (including any text the machine sends by itself) to fuzz_logs/watch_<time>.jsonl.
Sends nothing but getters.
"""
import argparse, json, os, time
import serial

HERE = os.path.dirname(os.path.abspath(__file__))
VERBS = ("GS", "GE", "GX", "GY", "GZ", "GQ", "GF")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM4")
    ap.add_argument("--secs", type=float, default=180)
    a = ap.parse_args()
    os.makedirs(os.path.join(HERE, "fuzz_logs"), exist_ok=True)
    fn = os.path.join(HERE, "fuzz_logs", f"watch_{time.strftime('%Y%m%d_%H%M%S')}.jsonl")
    s = serial.Serial(a.port, 19200, 8, "N", 1, timeout=0.05)
    s.dtr = True; s.rts = True
    time.sleep(0.3)
    last, t0, n = {}, time.time(), 0
    print(time.strftime("%H:%M:%S"), "watching for", a.secs, "s ->", fn, flush=True)
    with open(fn, "w") as f:
        try:
            while time.time() - t0 < a.secs:
                idle = s.read(200)                      # anything the machine says on its own
                if idle:
                    rec = {"t": round(time.time() - t0, 2), "unsolicited": idle.decode(errors="replace")}
                    f.write(json.dumps(rec) + "\n")
                    print(time.strftime("%H:%M:%S"), "UNSOLICITED:", repr(rec["unsolicited"]), flush=True)
                for v in VERBS:
                    s.reset_input_buffer()
                    s.write(b"\n\n\n" + v.encode() + b";")
                    buf, t1 = b"", time.time()
                    while time.time() - t1 < 0.12:
                        buf += s.read(100)
                    r = buf.decode(errors="replace").strip()
                    f.write(json.dumps({"t": round(time.time() - t0, 2), "v": v, "r": r}) + "\n")
                    if last.get(v) != r:
                        print(f"{time.strftime('%H:%M:%S')} t+{time.time() - t0:6.1f}s  {v}: {last.get(v)!r} -> {r!r}", flush=True)
                        last[v] = r
                n += 1
        finally:
            s.close()
    print(time.strftime("%H:%M:%S"), "done,", n, "cycles", flush=True)


if __name__ == "__main__":
    main()
