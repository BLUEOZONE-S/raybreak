# raybreak - test to-do list (front-back axis fault)

Status key: [ ] not started, [~] in progress, [x] done. Record the date and the result under each item, then commit and push.
Last updated: 2026-11-13 (list created; section 1b added after the return-wire observation; nothing run yet).

Safety: steps marked POWER OFF need the machine switched off AND unplugged. Photograph every connector before touching it (see `docs/Wiring-and-Card-Photos.md`).

## 1. Read-only checks (power on)
- [ ] 1a. Measure the voltages at the PS5 / PS6 pads and the 30 V rail on the blue card (000208) and the left-right card (000204); compare.
  - Result:
- [ ] 1b. Visually check the blue card's motor plug and wires (bent/burnt pins, loose wire); reseat it; compare with the left-right card's connector.
  - Result:

## 1b. Return-wire and reference-switch tests (new, see docs/Reference-Switch-Hypothesis.md)
- [x] 1c. Lower connector blocks photographed 2026-11-13: left-right has 3 thin wires (blue, pink, grey), front-back has 2 (pink, grey), Z has 2 (brown, white) on its tagged "Reference Switch-Z" cable. Counts confirmed.
  - Result: confirmed; see docs/Reference-Switch-Hypothesis.md
- [ ] 1d. Hand-push test (power on, ready): push the left-right head and the front-back beam slowly by hand and watch CHA/CHB; note any position where an LED flips.
  - Result:
- [ ] 1e. Z switch test: table at mid-travel (CHA lit), press the Z reference switch by hand; does CHA go off?
  - Result:
- [ ] 1f. Continuity test (POWER OFF): multimeter across the front-back card's two return wires while pushing the beam end to end; repeat on the left-right card (three wires) and Z card (two wires).
  - Result:
- [ ] 1g. Trace where the front-back pink/grey return wires go (which switch, at which end of the beam travel) and photograph both ends.
  - Result:

## 2. Mid-travel test (power on)
- [ ] 2a. Push the beam by hand to mid-travel, make the machine ready (`GS;` = 0), run 50 mm front-back moves.
  - Result (moved / did not move):
- [ ] 2b. Repeat from the "both CHA/CHB off" and "CHB on" LED states; note the starting state and result.
  - Result:

## 3. Motor winding resistance (POWER OFF)
- [ ] 3a. Unplug the beam motor; measure each winding pair (expect two pairs of a few ohms, no continuity between pairs).
  - Result (ohms per pair):

## 4. Motor plug swap (POWER OFF) - the decisive test
- [ ] 4a. Photograph both connector blocks (blue card 000208, left-right card 000204).
- [x] 4b. Motor plugs of X and Y swapped (owner, 2026-11-14): commanding X then moved the front-back beam.
  - Result: the beam motor, its cable and the motor power are good; the fault stays on the Y card / its enabling. Card swaps between slots failed (cards seem slot-specific).
- [ ] 4c. Restore the original connections and confirm the left-right axis still works.

## 7. Activation problem (new 2026-11-14, see docs/Card-Swaps-and-Activation.md)
Goal: make the machine reach "ready" without unplugging the Y reference-switch plug.
- [x] 7a. Baseline recorded; the only self-changing values are Z, params 52/56/57/B8 and diag8 low word (2026-11-14).
- [ ] 7a-old. Record a baseline while ready: console GS/GE/GF, status bytes, diagnostic ids 0-8, full parameter table (use `tools/rayjet_report.py` plus `tools/rayjet_diag.py`).
  - Result:
- [ ] 7b. Reproduce the activation: start not ready, unplug and re-plug the Y reference-switch plug, and log what the console reports (GS) before and after.
  - Result:
- [x] 7b/7c. DONE: GQ tracks readiness (9997 not ready, 9982 referencing, 9998 ready); GS flips 1->0. Second plug-pull stops the machine, so it is the switch EDGE that matters. See docs/Phase1-Activation-Findings.md.
- [ ] 7c-old. Once ready, record the baseline again and diff it with 7a. Does any value differ between "ready by nudge" and "ready by plug trick"?
  - Result:
- [ ] 7d. Thermal camera: compare the Y card's driver chip with the X card's while the machine is ready and holding.
  - Result:
- [ ] 7e. Hold test and motor-side voltage on the Y card vs the X card (same motor on both).
  - Result:
- [ ] 7f. Z reference switch: what does unplugging it do? (Be ready to hard-reset. Do NOT repeat on X: it locks the machine into safe mode.)
  - Result:
- [ ] 7g. Is the RGV-ACHSE slot populated? Photograph it.
  - Result:
- [ ] 7h. JTAG: identify the header pinout and adapter; read-only dump of one driver card for comparison. Nothing is ever written.
  - Result:

## 5. If it is the card
- [ ] 5a. Compare the pink rotary part, jumpers (JP8, JP9, yellow jumper) and the ES2 connector between the blue card and the left-right card.
  - Result:
- [ ] 5b. Check whether swapping the card slots moves the fault (a card swap earlier stopped the machine becoming ready; swapped back it recovered).
  - Result:

## 6. Software follow-ups (only after the hardware is cleared)
- [ ] 6a. Run `tools/rayjet_survey.py` (read-only, never run yet).
- [ ] 6b. Run `tools/gs_watch.py` (read-only, never run yet).
- [ ] 6c. Read, then write ONE parameter in RAM (`1A`, never `85`), e.g. the 0x0B-0x0E values; test; power cycle to restore.
- [ ] 6d. Inspect the rotary-attachment socket (left inside the working area) for bent pins or contamination.

## Interpreting results
| Result | Conclusion |
|---|---|
| Voltage low on the blue card only | the card's supply |
| Front-back pink/grey return wires open, shorted or erratic | reference-switch circuit fault (new lead) |
| Winding open or very different | motor or its cable |
| Moves from mid-travel | limit, rest-position or direction condition |
| Fault follows the motor in the swap | motor, cable or coupling |
| Fault stays on the card in the swap | the card (pink part, jumpers, stored config) |

## Session log
| Date | What was done | Outcome |
|---|---|---|
| 2026-11-13 | Protocol decoded; left-right and Z verified; front-back tested at 3/10/25/50 mm and two speeds with camera on the LEDs; docs, photos and this list published | front-back still does not move |
| 2026-11-13 (later) | Owner counted thin return wires: left-right 3, front-back 2, Z 2; outside CHA/CHB explanations compared with evidence; steps 1c-1g added; wire counts confirmed from new photos (front-back has pink+grey) | switch tests not yet run |
| 2026-11-14 | Slot labels found (X-ACHSE black, Y-ACHSE/RGV blue, Z-ACHSE red); card swaps failed; motor-plug swap showed motor and wiring good; Y reference-switch unplug/replug enables the machine, X version locks safe mode; section 7 added | Y card or its activation is the suspect |
| 2026-11-14 (Phase 1) | Found GQ = readiness indicator (9997/9982/9998); not-ready state is console-only and stable; Y reference-switch plug acts as an edge trigger (2nd pull stops machine) | software activation must go over the ASCII console |
