# Phase 1: what the machine reports as it becomes ready (2026-11-14)

Read-only differential test. We logged every console getter and every packet value while the machine moved
from not-ready to ready, and compared stable snapshots. Nothing here changes the machine; all TESTED.

## 1. GQ is a readiness indicator (new)
The console getter `GQ;` was previously "meaning unknown". It tracks the machine's ready state:

| State | GQ reads |
|---|---|
| Not ready | 9997 |
| Referencing (about 6 seconds, right at the transition) | 9982 |
| Ready | 9998 |

Captured live, polling about 3x/second, at the moment the machine became ready:
```
t+32.9 s  GS=1  GQ=9997      (not ready)
t+33.5 s        GQ=9982      (referencing begins)
t+33.8 s  GS=0               (now ready)
...       GQ stays 9982 for ~6 s...
t+40.1 s        GQ=9998      (ready, settled)
```
So `GS;` (0/1) and `GQ;` (9998/9997) agree on readiness, and `GQ` additionally shows a distinct "referencing" value.

## 2. The not-ready state is completely stable
While not ready, nothing drifts: GS=1, GE=0, GX=GY=GZ=0, GQ=9997, the options masks unchanged, for minutes.
Only the console answers in this state; the packet protocol is unavailable (the handshake is refused).

## 3. The ready state's only self-changing values (the "noise floor")
Comparing stable ready snapshots, the only values that move on their own are:
- Z position (`GZ` / the `2F` poll) - only when the table is moved.
- Parameters 0x52, 0x56, 0x57, 0xB8 - slowly increasing counters.
- The low word of diagnostic value 8 - increments once per read.
Everything else (all other parameters, the 4 state bytes, X/Y counters, options masks) is constant. So any change
outside that list during a test is real signal.

## 4. The reference-switch plug behaves like an edge, not a level
Owner observation, tied to the log above:
- From not-ready, unplugging and re-plugging the Y reference-switch plug makes the machine reference and become ready
  (GS 1 -> 0, GQ 9997 -> 9982 -> 9998). This is the same effect as nudging the beam by hand.
- Doing it a **second time stops the machine** (back toward not-ready / halted).
So it is the **change of state** of that switch line that the controller reacts to, not a steady level. This fits the
idea that power-on referencing drives each axis until its reference switch changes; because the Y beam never moves,
the Y switch never changes on its own, so referencing waits forever. Toggling the plug supplies the missing change.

## 5. What this means for the goal
The activation we want to trigger from software is the controller completing the Y reference. `GQ` now gives us a clean,
read-only progress signal to watch while we look for a command that does the same thing. The not-ready state blocks the
packet protocol entirely, so any software activation must work over the ASCII console, which is the only channel alive
while not ready.

## 6. Console activation probe - negative result (2026-11-14)
From the not-ready state (GS=1, GQ=9997), we sent each known action verb once, with its accepted argument count,
and watched GS/GQ for ~7 s. None activated the machine; all left it unchanged and responsive (no lock-ups):

| Command sent | Result |
|---|---|
| `RS0,0,0,0` | no change |
| `ST0,0,0` | no change |
| `GO0,0,0,0,0` | no change |
| `GC` | no change |
| `PU0,0,0,0,0` | no change |

So the simple console action verbs do not complete the Y reference. Remaining untried options are the unknown
setters `ID` and `PS` (higher risk) and non-zero argument variations. Because the not-ready state exposes only the
console, and the readiness transition is driven by the reference-switch **edge** (section 4), the current best
understanding is that the firmware completes referencing on a physical switch event, and no plain console verb
substitutes for it.

## 7. Practical conclusion
Two separate problems were being conflated:
1. **Reaching "ready".** Caused by Y referencing never completing (the beam never moves, so its reference switch
   never trips). Worked around by toggling the Y switch plug. No simple console command reproduces it yet.
2. **Y not moving when commanded.** The motor-plug swap proved the Y motor, cable and power are good, so the Y
   **driver card output** is the suspect. This is a hardware fault; software cannot move a motor whose driver
   output is dead.
Even a software "force ready" would not fix problem 2. The decisive next steps for movement are hardware:
the thermal-camera and motor-voltage comparison of the Y card against the X card (TODO 7d/7e).
