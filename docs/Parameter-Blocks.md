# The repeating parameter blocks: X and Y differ (2026-11-14)

Source: the 256-entry parameter table read from the ready machine (read-only). Four blocks of 23 entries repeat
at table indices 0x61, 0x78, 0x8F and 0xA6. Each starts with 32640 (0x7F80) and has 32784 (0x8010) at offset +7, which marks
them as the same record type. We read them as per-axis parameter sets.

| Offset | Block 0x61 | Block 0x78 | Block 0x8F | Block 0xA6 |
|---|---|---|---|---|
| +0 | 32640 | 32640 | 32640 | 32640 |
| +1 | 400 | 400 | 200 | 400 |
| +2 | 300 | 300 | 50 | 300 |
| +3 | 5000 | 5000 | 0 | 0 |
| +4 | 200 | 200 | 0 | 38400 |
| +5 | 5000 | 5000 | 0 | 0 |
| +6 | 500 | 500 | 0 | 63800 |
| +7 | 32784 | 32784 | 32784 | 32784 |
| +8 | 100 | 100 | 0 | 100 |
| +9 | 500 | 500 | 6098 | 500 |
| +10 | 255 | 255 | 255 | 255 |
| +11 | 4 | 4 | 50 | 4 |
| +12 | 20000 | 25000 | 15000 | 25000 |
| +14 | 100 | 300 | 300 | (live counter) |
| +15 | 100 | 0 | 50 | 0 |
| +16 | 100 | 4500 | 3000 | 19239 (live) |
| +17 | 500 | **0** | 700 | 0 |
| +18 | 28000 | **0** | 7000 | (live counter) |
| +19 | 27000 | **0** | 6500 | 18800 |

## Reading (INFERRED, not tested)
- **Block 0xA6 contains live values** (the table position that drifts, plus counters). It is probably the Z block, since
  Z is the axis whose position we saw change.
- **Blocks 0x61 and 0x78 are almost identical for entries +0 to +11**, so they are most likely X and Y.
- They differ from +12 on. **The Y block has zeros at +17, +18 and +19 where the X block has 500, 28000 and 27000.**
  These look like reference-run or limit parameters that are filled in for X and **empty for Y**.
- That is a software-visible difference between the working axis and the one that does not move, which we did not
  have before. It would fit "the controller counts the Y steps, reports done, never moves" and "Y never completes its
  reference run": an axis whose reference or limit values are zero may be clamped or never driven.

## Test idea (needs the owner's go-ahead, RAM only, reverts on power cycle)
Write X-like values into the Y block entries at 0x89, 0x8A and 0x8B (500, 28000, 27000), read them back, then try a small
Y move. If the beam moves, the missing Y entries are the cause. If nothing changes, the zeros are just unused fields.
Writing parameters is the kind of change that earlier hung or disturbed the machine in other opcodes, so each write
would be read back and followed by the canary, one at a time.
