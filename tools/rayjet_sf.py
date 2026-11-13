#!/usr/bin/env python3
"""
rayjet_sf.py -- Trotec Rayjet "SF" packet protocol (protocol mode 4).
Handshake at 19200 with "\n\n\nTS;", then the link
switches to a faster baud and a CRC-framed packet protocol.

Packet (both directions):
    'S' 'F'  seq  type  extlen  lenHi lenLo  crcHi crcLo      <- CRC16 over the 7 bytes before it
    [ext bytes (extlen)  crcHi crcLo]                         <- host: status tags requested
    [data bytes (len)    crcHi crcLo]                         <- host: command stream
CRC = CRC-16/ARC (poly 0xA001 reflected, init 0), stored big-endian.
"""
import sys, time
import serial

def crc16(data, crc=0):
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF

def be16(v): return bytes([(v >> 8) & 0xFF, v & 0xFF])
def be32(v): return (v & 0xFFFFFFFF).to_bytes(4, "big")

# status tags the host may request in the ext block (reply tag = request tag + 1)
REQ_STATUS, REQ_XY, REQ_Z = 0x10, 0x2C, 0x2E

class Rayjet:
    def __init__(self, port="COM3", verbose=True):
        self.port, self.verbose = port, verbose
        self.ser = None
        self.seq = 0xFF          # first packet goes out as seq 0
        self.fw = None

    def log(self, *a):
        if self.verbose: print(*a, flush=True)

    # ---- connection -------------------------------------------------------
    def connect(self):
        s = serial.Serial(self.port, 19200, bytesize=8, parity='N', stopbits=1, timeout=0.2)
        s.dtr = True; s.rts = True
        self.ser = s
        time.sleep(0.3)
        reply = b""
        for _ in range(120):   # the machine stays in packet mode for a while after a session; keep retrying
            s.reset_input_buffer()
            s.write(b"\n\n\nTS;"); s.flush()
            time.sleep(0.7)
            reply = s.read(64).strip()
            if len(reply) == 17: break
        if len(reply) != 17 or reply[2:3] != b'.' or reply[5:6] != b'-':
            raise RuntimeError("no TS; handshake reply (machine not ready / still in packet mode): %r" % reply)
        self.fw = reply.decode()
        mode = int(self.fw[0:2])
        baud = {'1': 230400, '2': 460800}.get(self.fw[4], 115200) if mode == 4 else 57600
        self.log(f"[handshake] {self.fw}  -> protocol mode {mode}, switching to {baud} baud")
        if mode != 4:
            raise RuntimeError("only protocol mode 4 is implemented")
        time.sleep(0.05)
        s.baudrate = baud
        s.reset_input_buffer()
        return self

    def close(self):
        if self.ser: self.ser.close()

    # ---- packets ------------------------------------------------------------
    def build(self, data=b"", ext=b"", pad=2):
        self.seq = (self.seq + 1) & 0xFF
        hdr = b"SF" + bytes([self.seq, 0x00, len(ext)]) + be16(len(data))
        pkt = hdr + be16(crc16(hdr))
        if ext:  pkt += ext + be16(crc16(ext))
        if data: pkt += data + be16(crc16(data))
        return pkt + bytes(pad)

    def read_packet(self, timeout=1.0):
        """Return dict(seq,type,ext,data,raw) or None."""
        s = self.ser; end = time.time() + timeout; buf = b""
        while time.time() < end:
            buf += s.read(256)
            i = buf.find(b"SF")
            if i < 0 or len(buf) < i + 9: continue
            h = buf[i:i+9]
            if crc16(h[:7]) != (h[7] << 8 | h[8]):
                buf = buf[i+2:]; continue
            extlen, dlen = h[4], (h[5] << 8 | h[6])
            need = i + 9 + (extlen + 2 if extlen else 0) + (dlen + 2 if dlen else 0)
            while len(buf) < need and time.time() < end: buf += s.read(need - len(buf))
            p = i + 9
            ext = buf[p:p+extlen]; p += extlen + (2 if extlen else 0)
            data = buf[p:p+dlen]
            return dict(seq=h[2], type=h[3], ext=ext, data=data, raw=buf[i:need], junk=buf[:i])
        return dict(raw=buf, type=None) if buf else None

    def xfer(self, data=b"\x00", ext=bytes([REQ_STATUS, REQ_XY, REQ_Z]), timeout=1.0, pad=2):
        pkt = self.build(data, ext, pad)
        self.log("  TX", pkt.hex(" "))
        self.ser.write(pkt); self.ser.flush()
        r = self.read_packet(timeout)
        if r: self.log("  RX", r["raw"].hex(" "))
        else: self.log("  RX (nothing)")
        return r

def parse_status(ext):
    """Decode status items the machine returns in its ext block."""
    out, i = {}, 0
    while i < len(ext):
        t = ext[i]; i += 1
        if t == 0x11: out["status"] = ext[i:i+4].hex(" "); i += 4
        elif t == 0x2D:
            out["x"] = int.from_bytes(ext[i:i+4], "big"); out["y"] = int.from_bytes(ext[i+4:i+8], "big"); i += 8
        elif t == 0x2F: out["z"] = int.from_bytes(ext[i:i+4], "big"); i += 4
        else: out.setdefault("other", []).append(hex(t))
    return out

if __name__ == "__main__":
    rj = Rayjet(sys.argv[1] if len(sys.argv) > 1 else "COM3").connect()
    try:
        for n in range(3):
            r = rj.xfer()
            if r and r.get("type") is not None:
                print("   type=%#x seq=%d ext=%s data=%s -> %s" % (r["type"], r["seq"], r["ext"].hex(" "), r["data"].hex(" "), parse_status(r["ext"])))
            time.sleep(0.3)
    finally:
        rj.close()
