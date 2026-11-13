#!/usr/bin/env python3
"""
rayjet_cmds.py -- ENCODERS ONLY for the Rayjet packet-protocol command stream (nothing here talks to the machine).

Every function returns the bytes that go in the data part of an SF packet.
Layouts worked out by analysis of the protocol. Status per command:
  TESTED   = sent to our machine and behaved as expected
  DECODED  = byte layout read from code, never sent
  OPAQUE   = layout read from code, meaning unknown
Multi-byte numbers are big-endian. Run this file to print a dry-run of each command.
"""

def be(v, n):
    return (int(v) & ((1 << (8 * n)) - 1)).to_bytes(n, "big")

# ---- generic "set / read a numbered parameter" families ------------------------------------------------
def set32(idx, value):   return bytes([0x1A, idx]) + be(value, 4)      # TESTED for idx 0xDA (move speed)
def set16(idx, value):   return bytes([0x1C, idx]) + be(value, 2)      # DECODED (idx 0xD3,0xD8,0xC4,0x4A,0xD4,0x4C,0xD6,0x4D,0xD7,0xDE)
def set8(idx, value):    return bytes([0x1E, idx, value & 255])        # DECODED (idx 0xC5,0xC8,0xCF,0xDF)
def read_param(idx):     return bytes([0x20, idx])                     # DECODED -> reply tag 0x21 <idx> <be32> <be32>
def store_params():      return bytes([0x85])                          # DECODED, WRITES TO NON-VOLATILE MEMORY

# ---- motion ---------------------------------------------------------------------------------------------
def select_46(n=0):      return bytes([0x46, n])                       # TESTED with n=0, used as prefix of every move we sent
def move_xy(x, y):       return bytes([0x9E]) + be(x, 4) + be(y, 4)    # TESTED. (0x9F is an alternate move; rule unknown)
def move_z(z):           return bytes([0xA6]) + be(z, 4)               # DECODED (Z move), never sent
def move_a8(v):          return bytes([0xA8]) + be(v, 4)               # DECODED (second Z-type move)
def end_block():         return bytes([0x86])                          # TESTED

# ---- status / diagnostics (these go in the packet's EXT part, not the data part) -----------------------
EXT_STATE, EXT_XY, EXT_Z = 0x10, 0x2C, 0x2E                            # TESTED   -> reply tags 0x11, 0x2D, 0x2F
def ext_diag(id16):      return bytes([0x87, id16 >> 8, id16 & 255])   # DECODED  -> reply tag 0x88 <id> <be32> <be32>

# ---- other decoded layouts (meaning unknown) --------------------------------------------------------------
OTHER = {
    0x80: [2],  0x44: ["1?", 2], 0x32: [], 0x88: [], 0xA2: [4, 4, 4],
    0x8A: [4], 0x8C: [4], 0x8E: [4], 0x90: [4],
    0x0A: [1], 0x0C: [1],                      # argument is a channel code: 1->4, 2->0x0D, 3->0x0E, 4->3
    0xC2: [], 0xC4: [], 0xC6: [], 0xC8: [],
    0xB3: [], 0xB1: [4], 0xB7: [], 0xB5: [2], 0xBB: [], 0xB9: [4], 0xBF: [], 0xBD: [4], 0xC3: [], 0xC1: [4],
    0xC7: [], 0xC5: [4], 0xCB: [], 0xC9: [1], 0xCD: [], 0xCF: [],
    0x16: ["1", 2], 0xB8: ["1?", 2],
    0xAA: [4, 4], 0xAB: [4, 4], 0xAC: ["1", "up to 1020 bytes"], 0xAE: [2],    # licence / pay-per-use area
}
def raw(op, *fields):
    """Encode an OTHER command from integers; each field is sized per the table above (1 or 2 or 4 bytes)."""
    sizes = OTHER[op]
    assert len(fields) == len(sizes), f"0x{op:02X} takes {len(sizes)} field(s)"
    out = bytes([op])
    for f, s in zip(fields, sizes):
        out += be(f, s if isinstance(s, int) else 1)
    return out

if __name__ == "__main__":
    demo = {
        "set speed 4000   (TESTED)":        set32(0xDA, 4000),
        "move to 2000,2000 (TESTED)":       move_xy(2000, 2000),
        "prefix + move + end (TESTED)":     select_46() + set32(0xDA, 4000) + move_xy(2000, 2000) + end_block(),
        "read parameter 0x21 (DECODED)":    read_param(0x21),
        "set 16-bit param 0xD3 = 5":        set16(0xD3, 5),
        "set 8-bit param 0xC5 = 1":         set8(0xC5, 1),
        "Z move to 100000 (DECODED)":       move_z(100000),
        "diag request id 0x0012 (ext)":     ext_diag(0x12),
        "store parameters (WRITES FRAM)":   store_params(),
    }
    for k, v in demo.items():
        print(f"{k:38} {v.hex(' ')}")
