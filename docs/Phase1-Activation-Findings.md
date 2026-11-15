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

## 8. Full diagnostic-channel scan (2026-11-14)
Every diagnostic id from 0x0000 to 0xFFFF was requested (read-only, 16 per packet). Result:
- Only **ids 0 to 8** carry real data: ids 0-7 read [0, 0] and id 8 reads [counter, 1023] (the first number ticks up on
  each read; the second is a constant 1023, the full-scale value of a 10-bit quantity, so it may be an analog reading
  sitting at its maximum - unconfirmed).
- Every other id returns padding: the second value is always 0xFFFFFFFF and the first is the id's low byte (plus 0x10000
  for most of the range). There are no hidden regions of data in the diagnostic channel.
So the diagnostic channel is fully mapped and is not a window onto the controller's memory or code.

## 9. The second state byte follows the Y beam (2026-11-14, 19:09-19:10)
The machine's state reply (`11` plus 4 bytes) reads `03 03 04 00` when idle. While watching it and four status flags
(requests `42`, `A0`, `AC`, `AE`) during a hand nudge of the Y beam:
- Request `42` is answered with tag `43` (flag present); `A0`, `AC` and `AE` are answered with nothing (flag absent).
  None of them changed during the test.
- The **second state byte changed from `03` to `02`** at 19:09:54 while the beam was displaced by hand, and returned to
  `03` at 19:10:13 when it was put back. No commanded move was involved.

Reading (INFERRED, one test): bit 0 of state byte 1 follows the Y beam position, most likely the Y reference/zero
switch (set at the rest position, clear when the beam is moved away). That means the controller's own report shows
whether the Y switch is active, which gives a read-only way to watch the thing the start-up logic depends on.
Not yet known: whether bit 1 of the same byte is the X head's switch (the head moved 10 mm during canaries without
the byte changing), and what bytes 2 and 3 (`04`, `00`) encode (interlock and the lid are the obvious candidates).

## 10. Correction to section 9: that state bit most likely follows the door, not the Y beam (2026-11-14, 19:14)
A second watch, this time for an X-head nudge, showed the second state byte drop from `03` to `02` at t+3.3 s, before the head
could have been touched, and the link then dropped at t+11 s. The owner confirmed the lid has to be opened to reach the
head or beam by hand. So in both tests the byte most likely changed because **the lid was opened**, and returned to `03` when
the lid was closed again (about 19 s later in the first test). The conclusion of section 9 ("bit 0 follows the Y beam") was
drawn from one test in which the lid state was not recorded and is **withdrawn**.

Working reading now (INFERRED): **bit 0 of state byte 1 = lid/interlock closed** (1 = closed, 0 = open). Opening the lid
also drops the machine's communication within a few seconds, which fits the documented behaviour that opening a cover stops
the machine and takes a few seconds to recover after closing.

Method note for the next test: record the lid state explicitly. To see the Y or X switch bits, the beam/head would need
to be moved without opening the lid (not possible by hand), so those switches are probably only observable when the
machine moves them itself.
