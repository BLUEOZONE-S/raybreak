#!/usr/bin/env python3
"""READ-ONLY survey of the extra status tags the machine can return (sensor / switch / interlock flags).
Run it once the machine is READY (Z buttons alive). It sends no motion commands.
Reply tag = request tag + 1.  """
import sys, time
from rayjet_sf import Rayjet, parse_status

REPLY_TAGS = [0x11,0x2D,0x2F,0x43,0xA1,0xAD,0xAF,0xA5,0xAB,0x21,0x0F,0x88,0xB4,0xB8,0xBC,0xC0,0xC4,0xC8,0xCC]

def survey(rj, label):
    print(f"--- {label}", flush=True)
    for rt in REPLY_TAGS:
        req = rt - 1
        r = rj.xfer(ext=bytes([req]), data=b"\x00")
        if r and r.get("type") is not None:
            print(f"   request {req:#04x} -> ext {r['ext'].hex(' ') or '(empty)'}", flush=True)
        else:
            print(f"   request {req:#04x} -> no reply", flush=True)
        time.sleep(0.1)

if __name__ == "__main__":
    rj = Rayjet("COM3", verbose=False).connect()
    try:
        survey(rj, "baseline")
        if len(sys.argv) > 1 and sys.argv[1] == "watch":
            # poll the flag tags while you push the Y gantry by hand; prints on any change
            tags = bytes([0x42,0xA0,0xAC,0xAE,0x10])
            last = None; t0 = time.time()
            print("watching flag tags for 40 s - push the Y gantry slowly toward and away from the rear stop", flush=True)
            while time.time() - t0 < 40:
                r = rj.xfer(ext=tags, data=b"\x00")
                cur = r["ext"].hex(" ") if r and r.get("type") is not None else None
                if cur != last: print(f"  {time.time()-t0:5.1f}s  {cur}", flush=True); last = cur
                time.sleep(0.1)
    finally:
        rj.close()
