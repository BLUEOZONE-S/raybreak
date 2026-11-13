#!/usr/bin/env python3
"""
rayjet_report.py -- READ-ONLY compatibility report you can paste into a GitHub issue.

Collects: console status (GS, GE, GF), the handshake string, one status poll, and the 256-entry parameter table.
It never moves anything, never writes a parameter, never sends the store opcode, and deliberately does NOT call GP
(that reply contains your CPU id / licence data).  Check the output before posting it anyway.

    python rayjet_report.py --port COM3          # needs the machine switched on and READY (GS = 0)
Output: rayjet_report_<time>.md
"""
import argparse, sys, time, serial
from rayjet_sf import Rayjet, parse_status
from rayjet_params import walk, be32


def console(port, cmd, wait=0.5):
    s = serial.Serial(port, 19200, 8, 'N', 1, timeout=0.3); s.dtr = True; s.rts = True
    try:
        time.sleep(0.3); s.reset_input_buffer()
        s.write(b"\n\n\n" + cmd + b";"); time.sleep(wait)
        return s.read(200).decode(errors="replace").strip()
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM3")
    a = ap.parse_args()
    out = ["# Rayjet compatibility report", "", f"Date: {time.strftime('%Y-%m-%d')}", ""]
    out.append("## Console (read-only)")
    gs = console(a.port, b"GS")
    out += [f"- GS: `{gs}`", f"- GE: `{console(a.port, b'GE')}`", f"- GF: `{console(a.port, b'GF')!r}`", ""]
    if gs != "0":
        out += ["Machine is NOT ready (GS != 0); packet protocol skipped.", ""]
        print("Machine not ready (GS != 0). Wrote console part only.")
    else:
        rj = Rayjet(a.port, verbose=False).connect()
        try:
            out += ["## Handshake", f"- reply: `{rj.fw}`", ""]
            r = rj.xfer()
            out += ["## One status poll", f"- {parse_status(r['ext']) if r and r.get('type') is not None else 'no reply'}", ""]
            params = {}
            for base in range(0, 256, 16):
                reads = b"".join(bytes([0x20, i]) for i in range(base, base + 16))
                r = rj.xfer(data=b"\x00", ext=reads)
                for tag, pay in (walk(r["ext"]) if r and r.get("type") is not None else []):
                    if tag == 0x21:
                        params[pay[0]] = be32(pay[5:9])
            out += ["## Parameter table (index=value, hex index)", "", "```"]
            row = []
            for i in sorted(params):
                row.append(f"{i:02X}={params[i]}")
                if len(row) == 8: out.append("  ".join(row)); row = []
            if row: out.append("  ".join(row))
            out += ["```", f"{len(params)} of 256 entries read."]
        finally:
            rj.close()
    out += ["", "## Please also tell us", "- Machine model and approximate year:", "- Which axes move and which do not:", "- Windows version:", ""]
    fn = f"rayjet_report_{time.strftime('%Y%m%d_%H%M%S')}.md"
    open(fn, "w", encoding="utf-8").write("\n".join(out))
    print("wrote", fn)


if __name__ == "__main__":
    main()
