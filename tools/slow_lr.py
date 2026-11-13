import time, serial, sys
s=serial.Serial("COM3",19200,8,'N',1,timeout=0.3); s.dtr=True; s.rts=True; time.sleep(0.3)
s.reset_input_buffer(); s.write(b"\n\n\nGS;"); time.sleep(0.6); g=s.read(40).strip(); s.close()
print("GS =", g, flush=True)
if g!=b"0": print("NOT READY"); sys.exit(1)
T0=time.time()+6
print(time.strftime("%H:%M:%S"), "lead-in 6 s", flush=True); time.sleep(6)
from rayjet_sf import Rayjet, be32
rj=Rayjet("COM3",verbose=False).connect()
def mv(x,y,v): return bytes([0x46,0,0x1A,0xDA])+be32(v)+bytes([0x9E])+be32(x)+be32(y)+bytes([0x86])
def hold(secs):
    t=time.time()
    while time.time()-t<secs: rj.xfer(data=b"\x00", ext=bytes([0x10,0x2C,0x2E])); time.sleep(0.2)
try:
    print(f"t+{time.time()-T0:4.1f} {time.strftime('%H:%M:%S')} LEFT-RIGHT out 30 mm (about 4 s)", flush=True)
    rj.xfer(data=mv(6000,0,1500), ext=bytes([0x10,0x2C,0x2E])); hold(10)
    print(f"t+{time.time()-T0:4.1f} {time.strftime('%H:%M:%S')} LEFT-RIGHT back (about 4 s)", flush=True)
    rj.xfer(data=mv(0,0,1500), ext=bytes([0x10,0x2C,0x2E])); hold(10)
    print("done", flush=True)
finally: rj.close()
