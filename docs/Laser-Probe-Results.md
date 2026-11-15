# Laser power-command probe: results so far (2026-11-14)

Method: send one candidate "set value" command alone (no enable, no move), then compare the parameter table,
diagnostics, status and the console `GP;` fields (LASER_POWER, LASER_SOURCE, ...) before and after, with a left-right
canary move before and after each stage. Every stage is RAM-only and sent with the machine ready.

| Stage | Command sent | Result |
|---|---|---|
| S0 | nothing (noise baseline) | clean: no changes, canary pass |
| W1 | `1C 4A 01 5E` (write the current tickle-delay value 350) | no change, canary pass (write path is harmless) |
| P-B5 | `B5 00 25` (16-bit, 37) | no visible change, canary pass |
| P-B9 | `B9 00 00 00 25` (32-bit, 37) | no visible change, canary pass |
| P-BD | `BD 00 00 00 25` (32-bit, 37) | no visible change, canary pass |
| P-C1 | `C1 00 00 00 25` (32-bit, 37) | no visible change, canary pass |
| P-C5 | `C5 00 00 00 25` (32-bit, 37) | no visible change, canary pass |
| P-C9 | `C9 25` (8-bit, 37) | **machine stopped answering** (no console reply for 70+ s) |

In every stage that completed, `GP` stayed at LASER_POWER 0 and LASER_SOURCE 0, so none of those opcodes set the
laser power in a way `GP` reports. Either they set something else, or their effect only shows during a job.

`C9` with an 8-bit argument is the first opcode in this series that hung the machine; it joins the `B1` pair from the
earlier stacked test as an opcode to avoid until understood. P-B1 was not run.

Takeaway: the "set value then read GP" idea found no power setter among B5/B9/BD/C1/C5. Power is probably set as part
of a job block, or via an opcode we have not tried, and `GP`'s laser fields may only update during an actual job.

---

## Slow command sweep (head parked at X = 10 mm), 2026-11-14 17:01-17:03
Method: one command per trial, about 3.5 s apart, with the head parked 10 mm right of zero, status checked after every
trial, an in-session left-right canary every 6 trials, and an owner watching the laser's LASE light. Each trial is
a block `46 00 <command> 86`. Excluded and never sent: 85, AA, AB, AC, AE, B1, C9 (hangs), 88, and any console command.

| Trials | Commands | Result |
|---|---|---|
| 1-11 | C2, C4, C6, C8, B3, B7, BB, BF, C3, C7, CB | no state change; canary passed at trial 6 |
| 12 | CD | **canary failed**; settings 0xBE-0xF9 (padding area) changed; console silent afterwards |
| 13-36 | CF, 32, 0A ch1-4, 0C ch1-4, 80, 8A, 8C, 8E, 90, A2, 44, 16, B8, and the value+enable pairs B5+B7, B9+BB, BD+BF, C1+C3, C5+C7 | **not tested** |

LASE-light observations: none reported at the time of writing; to be confirmed against the trial times above.

### Commands to avoid (each disturbed or hung the machine)
| Command | Effect |
|---|---|
| `C9 <byte>` | machine stopped answering |
| `CD` (no argument) | canary failed, padding-area settings changed, console silent |
| `B1` (+ `B3`) | Z counter jumped and moves stopped in the earlier stacked test |

### Status
- Tested and harmless: the same-value parameter write, B5, B9, BD, C1, C5 (alone), C2, C4, C6, C8, B3, B7, BB, BF, C3, C7, CB.
- Untested: everything listed under trials 13-36, plus any move with the laser-flagged variant.
- `GP` LASER_POWER stayed 0 throughout. No command found so far sets laser power.
- Recovery each time: power-cycle; afterwards a read-only snapshot matched the earlier baseline.

---

## Resumed sweep, trials 13-18 (17:15, gap 1 s), owner watching the LASE light: no light seen
| Trial | Command | Result |
|---|---|---|
| 13 | `CF` | no change in status or position |
| 14 | `32` | no change |
| 15-17 | `0A` channel 1, 2, 3 | no change |
| 18 | `0A` channel 4 (`46 00 0A 04 86`) | the in-session canary failed straight after; the console then went silent and, after ~25 s, came back **with GS=1 (machine no longer ready)** |

Observations that sharpen the picture:
- The silent link is not a permanent hang: after `CD` and after `0A 04` the console recovered by itself or after a power
  cycle, and the machine itself stayed alive (the owner could still move Z).
- What actually changes is the **ready state**: after the trip the machine reports not ready (GS=1), the same state it
  shows at power-on before the Y reference is completed. So these commands can drop the controller out of "ready".
- No command so far has lit the laser's LASE light (owner), and `LASER_POWER` has stayed 0.

Updated avoid list: `C9`, `CD`, `B1`, and `0A` with channel 4 (suspected trigger, trials 13-17 were clean).
Still untested: trials 19-36 (`0C` channels 1-4, `80`, `8A`, `8C`, `8E`, `90`, `A2`, `44`, `16`, `B8`, and the five value+enable pairs).
Speed note: a 1 s gap between trials works; each run still costs ~35 s of start-up checks.

---

## Sweep completed, 2026-11-14 17:19-17:22 (owner watching the LASE light)
- Trials 19-24 (`0C` channels 1-4, `80`, `8A`): no change.
- Trial 25 (`8C`) first looked like it moved the Z counter; that was the owner moving Z by hand to check activity. Repeated
  with no manual Z move it changed nothing.
- Trials 25-36 (`8C`, `8E`, `90`, `A2`, `44`, `16`, `B8`, and the pairs B5+B7, B9+BB, BD+BF, C1+C3, C5+C7): no status,
  position or parameter changes; both in-session canaries passed.

## Where the command search stands
| Group | Result |
|---|---|
| Tried, harmless | C2 C4 C6 C8 B3 B7 BB BF C3 C7 CB CF 32; 0A ch1-3; 0C ch1-4; 80 8A 8C 8E 90 A2 44 16 B8; B5 B9 BD C1 C5 alone; the five value+enable pairs |
| Disturb or hang the machine (avoid) | C9, CD, B1, 0A with channel 4 |
| Laser indicator | **never lit** during any trial (owner); `GP` LASER_POWER stayed 0 |

Conclusion so far: none of the opcodes in the known layout table, sent with a small value, turns the laser on or changes
what the controller reports about it. Not yet tried: the laser-flagged move variant `9F` after each enable, larger/other
values, longer enable sequences, and any opcode outside the layout table.

---

## 9F laser-flag move tests, head parked at X = 10 mm, 2026-11-14 17:28 (owner watching the LASE light)
Each trial: a 10 mm move to the right with the alternate move opcode `9F` (no power set), alone or preceded in the
same block by one harmless no-argument command; then an ordinary `9E` move back.

| Trial | Block | Result |
|---|---|---|
| 1-3 | `46 00 1A DA <speed> 9F X Y 86`, speeds 3000 / 1500 / 600 | moved normally, state byte 03 afterwards |
| 4-5 | `C2` or `C4` then the `9F` move | moved normally |
| 6 | `C6` then the `9F` move (`46 00 C6 1A DA 00 00 05 DC 9F 00 00 0F A0 00 00 00 00 86`) | the move finished at X=20 mm but the **state byte read `06`** (never seen before; 03 = idle, 04 = moving), the return move did not complete at first, and the console later went silent |

Observations:
- `06` is a new machine state, reached only after `C6` plus a laser-flag move. It is the first sign that any command combination changes the controller's mode in a way the status reports. What `06` means is unknown (an operating, armed or error mode are all possible); whether the laser's LASE light came on at that moment still needs the owner's report.
- Trials 7-16 (`C8`, `B3`, `B7`, `BB`, `BF`, `C3`, `C7`, `CB`, `CF`, `32` then `9F`) were not run.
- `C6` before a move joins the commands that disturb the machine until understood.

---

## C6 repeated alone, 2026-11-14 18:11 (owner watching the LASE light: nothing lit)
Sequence logged at 0.3 s resolution after a clean start (state 03, head parked at X = 10 mm):
1. `46 00 C6 1A DA <1500> 9F <X=20 mm> 86` was accepted; the head moved 10 mm normally and the state returned to 03.
2. The next ordinary move (`9E`, back to X = 10 mm) was **not executed**: the state byte read `06` and X stayed at 20 mm.
3. Afterwards the link went silent (no handshake reply for ~90 s); a power cycle was required.

Reading: it is repeatable. After `C6` (+ a `9F` move) the controller refuses the following move with state `06` and the
communication layer stops answering. So `06` looks like a "refused / waiting" state that follows `C6`, not an
operating mode that lights the laser. `C6` stays on the avoid list.

State byte values seen so far: `03` idle, `04` moving, `06` refusing the next command after `C6`.

---

## Console PD and the remaining 9F trials, 2026-11-14 19:29-19:34 (owner watching the LASE light: nothing came on)
- Console `PD` with no arguments was accepted without an error (0 args is the accepted count), followed by `PU`: no light, machine unchanged.
- `PD`, then a `9F` packet move (+10 mm), then `PU`: all accepted, state stayed 03, no light.
- Trial 7 (`C8` then `9F`): moved normally.
- **Trial 8 (`B3` then `9F`): the move did not run (X stayed at 10 mm for the 20 s wait).** The Z counter also changed
  (111092 to 143771), but the owner confirmed that was a **manual Z move**, so the Z change says nothing about `B3`.

Correction: an earlier version of this note read the Z change as `B3` being a Z/autofocus command. That is **withdrawn**: it was
the owner moving Z by hand (this happened in other tests too, so earlier "Z jumped" observations from stacked opcode tests
may also have been manual). What stands is only that `B3` placed before a `9F` move was followed by a move that did not
execute; this needs repeating without any hand movement before drawing a conclusion. Trials 9-16 remain untested.
