# Rayjet command reference - what the machine accepts and how to write it

Written in our own words from live tests on our Rayjet 50 (2026-11-13).
**Status key:** TESTED = sent to our machine and behaved as expected. DECODED = byte layout worked out, never sent.
OPAQUE = layout known, meaning unknown. INFERRED = a guess from context. Numbers longer than one byte are big-endian.
Encoders for everything here: `rayjet_cmds.py` (dry-run only; it does not talk to the machine).

---------------------------------------------------------------------------------------------------------
## 1. Two languages on one serial port
| Language | When available | Speed | Used for |
|---|---|---|---|
| ASCII console | right after power-on, always | 19200 8N1, DTR on | status reads only; the machine ignores everything useful |
| Packet protocol ("SF") | after `TS;` handshake, only when the machine is READY (status flag 0) | 460800 for our firmware | everything: moves, parameters, diagnostics, jobs |

Every console command is sent as `\n\n\n` + text + `;`. The console only looks at the **first two letters** as the verb and treats the rest
as arguments (`STATUS;` is answered like `ST`). Arguments are comma-separated numbers; spaces and other separators are rejected.

## 2. ASCII console (all TESTED live)
| Command | Arguments | Reply | Notes |
|---|---|---|---|
| `GP;` | none | 9-line block: CPU_ID, LASER_POWER, LASER_SOURCE, LOAD_COUNTER, END_DATE, CURRENT_DATE, JOBS_TO_ENGRAVE, TIME_TO_ENGRAVE, LICENSE_MODE | identity and licence data. Ours: CPU_ID <redacted>, LICENSE_MODE 40 |
| `GS;` | none | `0` or `1` | 1 = not ready (handshake ignored), 0 = ready |
| `GE;` | none | `0` | error code, 0 = none |
| `GF;` | none | `GetSupportedOptionsMask: 5` / `GetActiveOptionsMask: 1` | option bits, meaning unknown |
| `GQ;` | none | `9997` | meaning unknown |
| `GX;` `GY;` `GZ;` | none | integer | live position; X/Y read 0 until referenced; Z reads 0 in the not-ready state |
| `GO` | 0 or 5 | silent | accepted, no motion in the console |
| `PU` `PD` | 5 / unknown | silent | accepted, no motion. PD is "pen down" - treat as laser-enable, do not send |
| `ST` | 3 | silent | accepted, no effect |
| `RS` | 4 | silent | accepted, no effect (tried 7 argument patterns) |
| `ID` | 1 | silent | setter, effect unknown - avoid |
| `PS` | 2, or 5 and more | silent | the "set parameter `PS index,value`" file syntax; effect in the console unknown - avoid |
| `TS;` | none | `04.02-21.00-06.62` (only when ready) | the handshake; switches the port to packets |
| any other `G?` | none | silent | all 26 letters swept at 0 and 1 argument; the only verbs found are E F P Q S X Y Z (getters), O, C |
Wrong argument count gives `Illegal number of parameters! Command ignored.` and does nothing.

## 3. Packet protocol
### 3.1 Framing (TESTED)
```
'S' 'F'  seq  type  extLen  lenHi lenLo  crcHi crcLo        header: 9 bytes, crc covers the first 7
[ ext bytes (extLen)  crcHi crcLo ]                         only if extLen > 0
[ data bytes (len)    crcHi crcLo ]                         only if len > 0
+ 2 padding zero bytes
```
`type` 0x00 from the PC, 0x80 from the machine; the machine echoes the sequence number. CRC = CRC-16/ARC (poly 0xA001 reflected, start 0), stored big-endian.
Sequence starts at 0 and wraps at 255.
The **ext** part carries status requests, the **data** part carries commands.

### 3.2 Handshake and speed (TESTED)
`\n\n\nTS;` at 19200 -> 17 characters `NN.NN-NN.NN-NN.NN`. First field = protocol mode (04). The digit after its dot selects the new baud rate:
`1` = 230400, `2` = 460800, otherwise 115200. Reopen the port at that rate. The machine drops back to the console by itself some time after the last packet.

### 3.3 Idle poll (TESTED)
ext = `10 2C 2E`, data = one filler byte. Reply ext: `11 <4 state bytes>` `2D <be32 X> <be32 Y>` `2F <be32 Z>`.
State byte 0: `03` idle, `04` moving.

### 3.4 Status and diagnostic requests (ext part)
| Request | Meaning | Reply tag | Status |
|---|---|---|---|
| `10` | machine state | `11` + 4 bytes | TESTED |
| `2C` | X and Y position | `2D` + be32 + be32 | TESTED |
| `2E` | Z position | `2F` + be32 | TESTED |
| `87 hh ll` | diagnostic value number hhll | `88 hh ll <be32 a> <be32 b>` | DECODED (script: `rayjet_diag.py`) |
Other reply tags we parse: `0F` (index, flag), `21` parameter reply, `43` `A1` `AD` `AF` (one-byte flags, meaning unknown),
`A5` (2 bytes), `AB` (index + be32), `B4` `BC` `C0` `C4` `C8` (be32 each), `B8` (2 bytes), `CC` (1 byte). All licence / pay-per-use related except the flags.

## 4. Command stream (data part)
### 4.1 Numbered parameters
| Bytes | Meaning | Status |
|---|---|---|
| `1A idx v3 v2 v1 v0` | set 32-bit parameter `idx` | TESTED for idx 0xDA (move speed in steps/s) |
| `1C idx hi lo` | set 16-bit parameter | DECODED |
| `1E idx b` | set 8-bit parameter | DECODED |
| `20 idx` | read parameter `idx` -> reply `21 idx <be32> <be32>` (second number is the value) | DECODED (script: `rayjet_params.py`) |
| `85` | store all parameters to non-volatile memory | DECODED - **writes permanently, never send casually** |
Parameter indices known to be written: 32-bit `0x0B 0x0C 0x0D 0x0E 0xBD 0xDA 0xDB 0xDD 0x4E`; 16-bit `0xD3 0xC4 0x4A 0xD4 0x4C 0xD6 0xD8(x100) 0x4D(x100) 0xD7(x100) 0xDE(x100)`;
8-bit `0xC5 0xC8 0xCF 0xDF`. The routine that updates "tickle power / diode current" uses `1C 4A/D4`, `1C 4C/D6`, `1C 4D/D7`, `1C DE` (INFERRED: laser related).
`0x0B-0x0E` might be four per-axis acceleration settings (INFERRED: four values in the stored table look like per-axis acceleration settings). Everything else: unknown.
The table holds indices 0 to 0x12F.

### 4.2 Motion
| Bytes | Meaning | Status |
|---|---|---|
| `46 n` | select/prefix (we always send `46 00`) | TESTED |
| `9E xxxxxxxx yyyyyyyy` | move to X, Y in steps (5 micrometre per step assumed) | TESTED |
| `9F xxxxxxxx yyyyyyyy` | alternate move; chosen under conditions we do not know | DECODED |
| `A6 zzzzzzzz` | Z move | DECODED, never sent |
| `A8 vvvvvvvv` | second Z-type move (focus / offset) | DECODED |
| `86` | end of block | TESTED |

### 4.3 Other layouts read from code (meaning unknown, not all mode-4-only)
| Opcode | Fields after it | Opcode | Fields after it |
|---|---|---|---|
| `80` | be16 | `A2` | be32, be32, be32 |
| `44` | 1 byte, be16 | `8A` `8C` `8E` `90` | be32 each |
| `32` | none | `0A` `0C` | 1 channel byte (maps 1->04, 2->0D, 3->0E, 4->03) |
| `C2` `C4` `C6` `C8` | none | `B3` `B7` `BB` `BF` `C3` `C7` `CB` `CD` `CF` | none |
| `B1` `B9` `BD` `C1` `C5` | be32 | `B5` | be16 |
| `C9` | 1 byte | `16` | 1 byte, be16 |
| `B8` | 1 byte(?), be16 | `AA` `AB` | be32, be32 (+ more) |
| `AC` | 1 byte, then up to 1020 bytes | `AE` | be16 |
| `10` `2C` `2E` | none (status requests placed inside the command stream) | `87` | be16 (diagnostic request in the stream) |
Pairs like `B1/B3`, `B5/B7`, `B9/BB`, `BD/BF`, `C1/C3`, `C5/C7`, `C9/CB`, `CD/CF` look like "set value / enable" pairs for job parameters
such as power, speed and pulse settings (INFERRED). `AA AB AC AE` belong to the licence / pay-per-use area (seven licence blocks read with `AA n`, n = 0..6).

## 5. Risk classes
| Class | Commands | Rule |
|---|---|---|
| Read only | console getters, `10 2C 2E`, `87`, `20` | safe to send any time the machine is ready |
| Reversible | `1A 1C 1E` writes | change RAM only; a power cycle restores stored values; write one at a time and read back first |
| Persistent | `85` | permanently overwrites stored parameters; only after a full dump is saved |
| Unknown / licence | `AA AB AC AE`, all OPAQUE opcodes | do not send |
| Laser | `PD` in the console, job data in the stream | never while the laser is connected unless intended |

## 6. How the syntax was checked
- `python rayjet_cmds.py` reproduces byte for byte the packets we sent live (`46 00 1A DA 00 00 0F A0 9E 00 00 07 D0 00 00 07 D0 86`).
- Console verbs were confirmed with wrong-argument-count probes (the error text proves the verb exists without running it).
- Not yet possible: live checks of parameter reads and diagnostics, because they need the machine in the READY state.

## 7. Verb search results (2026-11-13)
- One-argument probe of every unused G-letter found only `GC`.
- Nine-argument probe of 18 candidate verbs (IN HM HO RF EN CE RE VS SP CL RT HE FH FE LS LO HI IM): none exist (no error text came back).
- Deliberately not probed: PS, PA, PR, ON, EX, PD, ID and the full 676-verb sweep, because an unknown verb that happens to accept the dummy arguments would run.
- Unproven claims we do NOT rely on: ST = set time (the GP date never changed after ST0,0,0), GF = interlock mask, GQ = queue slots, PU/PD/GO arguments = X,Y,Z,speed,power.

## 8. Live results from the ready state (2026-11-13)
- Parameter reads (`20 idx`) and diagnostic requests (`87 hh ll`) both go in the packet's **ext** part and are answered **in the same reply packet**, not on later polls.
- Parameter table dumped: 256 entries (see `Rayjet-Parameter-Table.md`). Diagnostic ids 0-8 return values (id 8 = 1023); higher ids return padding.
- The 676-verb console sweep was invalid: its reply wait was too short, and it stopped at verb 520. The status flag change during it was the owner nudging the beam, not a verb.
