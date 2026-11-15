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

## Result of the test (2026-11-14, 19:20)
Three RAM writes were made with the table write command (`46 00 1A <index> <value, 4 bytes> 86`), each read back correctly and
followed by a passing left-right canary:

| Entry | Was | Written |
|---|---|---|
| 0x89 | 0 | 500 |
| 0x8A | 0 | 28000 |
| 0x8B | 0 | 27000 |

Nothing else in the table changed. A 2 mm Y move was then commanded and the Y counter reached 400 and returned to 0, but
the owner saw **no physical movement** of the beam. So filling those three zero entries with X's values does not make the
Y axis move; they are either unused fields or not the missing piece. (Side result: the table write command works and is
reversible by a power cycle; nothing was ever stored.)

Differences between the X and Y blocks that were NOT tested: entries +12, +14, +15 and +16 (0x84, 0x86, 0x87, 0x88), where Y has
25000, 300, 0 and 4500 against X's 20000, 100, 100 and 100. Those may simply be genuine X/Y differences, so copying them
blindly is a weak lead.

## Better discriminator (hardware)
The earlier motor-plug swap showed the X electronics can drive the beam motor. The reverse was not recorded: with the plugs
swapped, does commanding Y make the **head** move? Yes = the Y card's output stage works and the fault is in how it is
enabled or configured. No = the Y output stage itself is dead.
