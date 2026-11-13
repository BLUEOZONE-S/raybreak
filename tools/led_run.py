import time, serial, sys
s=serial.Serial("COM3",19200,8,'N',1,timeout=0.3); s.dtr=True; s.rts=True; time.sleep(0.3)
s.reset_input_buffer(); s.write(b"\n\n\nGS;"); time.sleep(0.6); g=s.read(40).strip(); s.close()
print("GS =", g, flush=True)
if g!=b"0": print("NOT READY"); sys.exit(1)
T0=time.time()+8
print(time.strftime("%H:%M:%S"), "lead-in 8 s", flush=True)
time.sleep(8)
from rayjet_sf import Rayjet, be32
rj=Rayjet("COM3",verbose=False).connect()
def mv(x,y,v): return bytes([0x46,0,0x1A,0xDA])+be32(v)+bytes([0x9E])+be32(x)+be32(y)+bytes([0x86])
def hold(secs):
    t=time.time()
    while time.time()-t<secs: rj.xfer(data=b"\x00", ext=bytes([0x10,0x2C,0x2E])); time.sleep(0.1)
def go(label,x,y,v,secs):
    print(f"t+{time.time()-T0:5.1f}s {time.strftime('%H:%M:%S')} {label}", flush=True)
    rj.xfer(data=mv(x,y,v), ext=bytes([0x10,0x2C,0x2E])); hold(secs)
try:
    V=1500; D=6000
    go("LEFT-RIGHT OUT", D,0,V,6); go("LEFT-RIGHT BACK",0,0,V,6)
    go("FRONT-BACK OUT",0,D,V,6);  go("FRONT-BACK BACK",0,0,V,6)
    print("done", flush=True)
finally: rj.close()
