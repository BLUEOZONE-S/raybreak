import sys, time
from rayjet_sf import Rayjet, parse_status, be32
X_UM_PER_STEP = 5.0     # stored settings 5 / 3.75 / 0.192 um (X verified by measurement)

def move_cmd(x_steps, y_steps, speed_steps):
    # the move block: 46 00 | 1A DA <speed> | 9E <x> <y> | 86
    return bytes([0x46, 0x00, 0x1A, 0xDA]) + be32(speed_steps) + bytes([0x9E]) + be32(x_steps) + be32(y_steps) + bytes([0x86])

def poll(rj, label, n=1, gap=0.25):
    last = None
    for _ in range(n):
        r = rj.xfer()
        if r and r.get("type") is not None:
            st = parse_status(r["ext"]); last = st
            print(f"   [{label}] type={r['type']:#x} status={st.get('status')} X={st.get('x')} Y={st.get('y')} Z={st.get('z')}", flush=True)
        time.sleep(gap)
    return last

x = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
y = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
v = int(sys.argv[3]) if len(sys.argv) > 3 else 4000
rj = Rayjet("COM3", verbose=False).connect()
try:
    poll(rj, "before", 2)
    cmd = move_cmd(x, y, v)
    print("   MOVE data:", cmd.hex(" "))
    rj.verbose = True
    r = rj.xfer(data=cmd)
    rj.verbose = False
    if r and r.get("type") is not None: print("   move reply:", hex(r["type"]), parse_status(r["ext"]))
    poll(rj, "after", 14, 0.3)
finally:
    rj.close()
