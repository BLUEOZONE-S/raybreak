import time, sys
from rayjet_sf import Rayjet, be32
from laser_sweep import poll, stamp, PARK
from laser_seq import mvblock, wait_at, TARGET
rj=Rayjet("COM4",verbose=False).connect()
try:
    rj.xfer(data=mvblock(0x9E,PARK,3000),ext=bytes([0x10,0x2C,0x2E])); print(stamp(),"parked:",wait_at(rj,PARK),flush=True)
    base=poll(rj); print(stamp(),"baseline:",base,flush=True)
    blk=mvblock(0x9F,TARGET,1500,bytes([0xC6]))
    print(f"{stamp()}  SENDING C6 then 9F move NOW  {blk.hex(' ')}",flush=True)
    rj.xfer(data=blk,ext=bytes([0x10,0x2C,0x2E]),timeout=1.5)
    t0=time.time(); last=None
    while time.time()-t0<12:
        p=poll(rj)
        key=None if p is None else (p.get("status"),p.get("x"),p.get("y"),p.get("z"))
        if key!=last:
            print(f"{stamp()}  t+{time.time()-t0:5.1f}s  {p}",flush=True); last=key
        if p is None: print("  no reply: stopping"); break
        time.sleep(0.3)
    print(stamp(),"final:",poll(rj),flush=True)
    try:
        rj.xfer(data=mvblock(0x9E,0,3000),ext=bytes([0x10,0x2C,0x2E]),timeout=1.5); print(stamp(),"return to 0:",wait_at(rj,0,25),flush=True)
    except Exception as e: print("return failed:",e)
finally:
    rj.close()
