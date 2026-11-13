#!/usr/bin/env python3
"""READ-ONLY console logger: polls GS, GE, GF, GX, GY, GZ about 3 times a second and prints every change with a timestamp.
Use it while you do one physical thing at a time (open the lid, close it, press a panel button, nudge an axis ...) so we can
see exactly which action changes the state.   python gs_watch.py [seconds]"""
import sys, time, serial
dur = float(sys.argv[1]) if len(sys.argv) > 1 else 90
s = serial.Serial("COM3", 19200, 8, 'N', 1, timeout=0.12); s.dtr = True; s.rts = True; time.sleep(0.3)
def ask(c, w=0.12):
    s.reset_input_buffer(); s.write(b"\n\n\n" + c.encode()); s.flush(); time.sleep(w)
    return s.read(300).decode("latin-1", "replace").strip().replace("\r\n", " | ")
last = None; t0 = time.time()
print(f"watching {dur:.0f}s - do ONE physical action at a time and say what you did", flush=True)
while time.time() - t0 < dur:
    cur = tuple(ask(c) for c in ("GS;", "GE;", "GF;", "GX;", "GY;", "GZ;"))
    if cur != last:
        print(f"{time.time()-t0:6.1f}s  GS={cur[0]} GE={cur[1]} GX={cur[3]} GY={cur[4]} GZ={cur[5]}  GF=[{cur[2]}]", flush=True)
        last = cur
s.close()
