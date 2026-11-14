# Root cause of the front-back (Y) fault - working explanation (2026-11-14)

This ties together the start-up behaviour, the activation trick and the "Y counts but never moves" symptom into one
explanation. Parts are TESTED; the final hardware distinction is still to be confirmed (marked).

## The chain of events
1. **Start-up references every axis by driving it to its zero (reference) switch.** The controller moves each axis
   until that axis's switch changes state, which marks it referenced.
2. **X references normally.** The X card drives the head, the head reaches the X zero switch, the switch trips, X is
   referenced. (TESTED: X moves on command and the machine references with X working.)
3. **Y never references on its own.** The Y beam does not move, so the Y zero switch is never reached, so Y
   referencing never completes. The whole machine stays "not ready" (GS=1, GQ=9997) waiting for Y. (TESTED.)
4. **Manually toggling the Y zero-switch plug fakes the trip.** Unplugging and re-plugging it supplies the state
   change the controller was waiting for, Y is marked referenced, and the machine becomes ready
   (GS 1->0, GQ 9997 -> 9982 -> 9998). (TESTED.)
5. **A second toggle stops the machine.** Once referenced and running, an unexpected change on a zero-switch line
   reads as a fault or limit hit, so the machine halts. This is the same reason toggling the X switch (an already
   referenced axis) trips safe mode. (TESTED / owner-observed.)

So a single fact - *the Y beam never moves to its zero switch* - explains the not-ready hang, why the plug trick
works, and why doing it twice stops the machine.

## Why the Y beam never moves - the remaining fork
The motor-plug swap proved the Y **motor, cable and power are good** (the X card drove the Y motor and the beam
moved). So the problem is on the Y card side. Two possibilities remain, and they need different fixes:
- **(a) Dead or weak motor-drive output on the Y card.** It counts steps and reports the move complete, but never
  actually drives the motor. The beam never moves, so it never references.
- **(b) The Y card never enables its drive** (e.g. it refuses to drive until referenced, or a faulty Y zero switch /
  its wiring never lets it believe it is referenced). Note the Y card has only 2 thin switch wires where the X card
  has 3.

Evidence leaning toward (a): after we fake-activate the machine, commanding Y *still* produces no beam movement,
even though the system is now "ready". A card that was merely waiting to reference might be expected to drive once
the system is ready; this one does not.

## The test that decides it (NOT yet done)
Thermal camera, or a meter/scope on the Y card's motor output pins, while commanding a Y move:
- Y driver chip cold, no output -> dead output stage (a). Fix: repair or replace the Y card.
- Y driver chip switching but the motor does not hold/turn -> enable or drive-strength problem (b). Fix: look at the
  Y reference-switch circuit and the card's enable logic before condemning the card.

## Consequence for software
A software "force ready" (if one existed) would remove the unplug-each-time annoyance but would **not** make Y move,
because the beam not moving is a hardware fault on the Y card, not a missing command. The known console action
verbs (RS, ST, GO, GC, PU) do not force ready anyway (see Phase1-Activation-Findings.md).
