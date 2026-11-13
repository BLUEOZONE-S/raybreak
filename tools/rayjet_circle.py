#!/usr/bin/env python3
"""Trace a circle with the head (motion only, no laser commands).
usage: rayjet_circle.py [diameter_mm=50] [center_x_mm=40] [center_y_mm=40] [speed_mm_s=20] [segments=72]"""
import sys, time, math
from rayjet_sf import Rayjet, parse_status, be32

UM_PER_STEP = 5.0            # X scale verified; Y scale unverified
MAX_X_MM, MAX_Y_MM = 475, 314

def steps(mm): return int(round(mm * 1000.0 / UM_PER_STEP))

def move_cmd(x, y, v):
    return bytes([0x46, 0x00, 0x1A, 0xDA]) + be32(v) + bytes([0x9E]) + be32(x) + be32(y) + bytes([0x86])

def status(rj):
    r = rj.xfer()
    return parse_status(r["ext"]) if r and r.get("type") is not None else None

def goto(rj, x, y, v, timeout=30.0):
    r = rj.xfer(data=move_cmd(x, y, v))
    if not r or r.get("type") is None: raise RuntimeError("no ack for move")
    end = time.time() + timeout
    while time.time() < end:
        st = status(rj)
        if st and st.get("x") == x and st.get("y") == y and st.get("status", "")[:2] != "04":
            return st
        time.sleep(0.02)
    raise RuntimeError(f"timeout waiting for {x},{y}; last status {st}")

a = sys.argv[1:]
dia = float(a[0]) if len(a) > 0 else 50.0
cx  = float(a[1]) if len(a) > 1 else 40.0
cy  = float(a[2]) if len(a) > 2 else 40.0
spd = float(a[3]) if len(a) > 3 else 20.0
seg = int(a[4])   if len(a) > 4 else 72
r = dia / 2.0
if cx - r < 0 or cy - r < 0 or cx + r > MAX_X_MM or cy + r > MAX_Y_MM:
    sys.exit("circle does not fit on the table")
v = steps(spd)

rj = Rayjet("COM3", verbose=False).connect()
try:
    st = status(rj); print("start position:", st, flush=True)
    print(f"moving to circle start ({cx + r:.1f}, {cy:.1f}) mm", flush=True)
    goto(rj, steps(cx + r), steps(cy), v)
    t0 = time.time()
    for i in range(1, seg + 1):
        ang = 2 * math.pi * i / seg
        st = goto(rj, steps(cx + r * math.cos(ang)), steps(cy + r * math.sin(ang)), v)
        if i % 12 == 0: print(f"  {i}/{seg} segments  X={st['x']} Y={st['y']}", flush=True)
    print(f"circle done in {time.time() - t0:.1f}s; final:", status(rj), flush=True)
finally:
    rj.close()
