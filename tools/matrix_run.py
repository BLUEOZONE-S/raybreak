import time, serial, sys
s=serial.Serial("COM3",19200,8,'N',1,timeout=0.3); s.dtr=True; s.rts=True; time.sleep(0.3)
s.reset_input_buffer(); s.write(b"\n\n\nGS;"); time.sleep(0.6); g=s.read(40).strip(); s.close()
print("GS =", g, flush=True)
if g!=b"0": print("NOT READY"); sys.exit(1)
T0=time.time()+12
print(time.strftime("%H:%M:%S"), "lead-in 12 s", flush=True); time.sleep(12)
from rayjet_sf import Rayjet, be32, parse_status
rj=Rayjet("COM3",verbose=False).connect()
def mv(x,y,v): return bytes([0x46,0,0x1A,0xDA])+be32(v)+bytes([0x9E])+be32(x)+be32(y)+bytes([0x86])
def pos():
    r=rj.xfer(); return parse_status(r["ext"]) if r and r.get("type") is not None else None
def go(label,y,v):
    print(f"t+{time.time()-T0:5.1f}s {time.strftime('%H:%M:%S')}   {label}", flush=True)
    rj.xfer(data=mv(0,y,v), ext=bytes([0x10,0x2C,0x2E])); t0=time.time()
    while time.time()-t0<30:
        p=pos()
        if p["y"]==y and not p["status"].startswith("04"): break
        time.sleep(0.05)
    t=time.time()
    while time.time()-t<3: pos(); time.sleep(0.2)
tests=[(1,10,4000),(2,10,1500),(3,3,4000),(4,50,4000),(5,50,1500),(6,25,4000)]
try:
    for n,mm,v in tests:
        u=int(mm*200)
        print(f"TEST {n}: {mm} mm at {v} steps/s", flush=True)
        go(f"test {n} OUT", u, v); go(f"test {n} BACK", 0, v)
        time.sleep(3)
    print("done", flush=True)
finally: rj.close()
