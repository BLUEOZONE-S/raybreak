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
