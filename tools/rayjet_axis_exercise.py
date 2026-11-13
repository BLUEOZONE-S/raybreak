#!/usr/bin/env python3
"""
rayjet_axis_exercise.py -- move each axis in turn, announcing which one, so you can watch the cards' LEDs
(and the machine) and see how the front-back card reacts compared with the left-right card.

Run it when the machine is READY (Z buttons alive).  Small moves only; the laser is not touched.

    python rayjet_axis_exercise.py                 # 10 mm moves, 4 rounds
    python rayjet_axis_exercise.py --mm 5 --rounds 6 --pause 4

For every move it prints the axis and a timestamp.  Note, per card: do TX / RX / ERR flicker or light?
"""
import argparse, time
from rayjet_sf import Rayjet, parse_status, be32

UM_PER_STEP = 5.0   # assumed; only used to turn millimetres into steps


def move_cmd(x, y, speed):
    return bytes([0x46, 0x00, 0x1A, 0xDA]) + be32(speed) + bytes([0x9E]) + be32(x) + be32(y) + bytes([0x86])


def status(rj):
    r = rj.xfer()
    return parse_status(r["ext"]) if r and r.get("type") is not None else None


def goto(rj, x, y, speed):
    rj.xfer(data=move_cmd(x, y, speed))
    t0 = time.time()
    while time.time() - t0 < 15:
        s = status(rj)
        if s and s["x"] == x and s["y"] == y and not s["status"].startswith("04"):
            return s
        time.sleep(0.05)
    return s


def wait(rj, secs):
    t0 = time.time()
    while time.time() - t0 < secs:
        status(rj)          # keeps the link alive
        time.sleep(0.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mm", type=float, default=10.0)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--pause", type=float, default=4.0, help="seconds to rest between moves")
    ap.add_argument("--speed", type=int, default=4000, help="steps per second")
    a = ap.parse_args()
    d = int(round(a.mm * 1000 / UM_PER_STEP))

    rj = Rayjet("COM3", verbose=False).connect()
    try:
        s = status(rj)
        bx, by = s["x"], s["y"]
        print(f"start X={bx} Y={by}   ({a.mm} mm = {d} steps)\n", flush=True)
        for r in range(1, a.rounds + 1):
            for name, tx, ty in (("LEFT-RIGHT (green card)", bx + d, by), ("FRONT-BACK (blue card)", bx, by + d)):
                print(f"[{time.strftime('%H:%M:%S')}] round {r}: {name}  -> out", flush=True)
                goto(rj, tx, ty, a.speed)
                wait(rj, 1.5)
                print(f"[{time.strftime('%H:%M:%S')}] round {r}: {name}  -> back", flush=True)
                goto(rj, bx, by, a.speed)
                wait(rj, a.pause)
        print("done", flush=True)
    finally:
        rj.close()


if __name__ == "__main__":
    main()
