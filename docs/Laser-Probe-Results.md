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
