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
