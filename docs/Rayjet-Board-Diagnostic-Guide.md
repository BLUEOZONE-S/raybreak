# Rayjet 50 - controller cards, LEDs, jumpers and referencing (what is known)

## What the photos show (CPU card, "TROTEC SPEEDY2 CPU T00005 REV 2.0", label RV14.0045-009, week 38/2014)
- Plugs into the machine's backplane through the grey 3-row DIN connector on its right edge. The green board it sits next to is a separate card.
- Red tact switch beside the 9-pin D-sub on the front edge = reset button (not confirmed by any document).
- Two jumpers: green one on a 2-pin header beside the UART chip and the C167, yellow one on a 3-pin header near the DSP at the lower edge.
- Pin headers: a 2x3 header at the top-left with silkscreen "CPU 2 1 0", a 2x3 header near the DSP, and an 8-pin row on the DSP side. A row of 10 bare holes beside the reset button is unpopulated.
- At least one yellow LED is lit steady while powered (next to the 5.000 MHz crystal). A second dim one may be visible; the angle of the photos is not good enough to tell.
- NO public document was found for this board's jumpers, LEDs or reset behaviour. Everything about them has to be learned by observation (below).

## Documented start-up behaviour
- On power-up the machine references X, Y and Z by itself, then beeps once and the front LED flashes green slowly = ready.
- It will NOT reference if the top lid, maintenance panel or interlocks are open: LEDs flash green/red alternately and a beep sounds.
- After the lid closes it is not ready for 5 seconds.
- Troubleshooting page only says: no referencing + beep = check the lid is tight and the interlock circuit is closed.
- No jumper, card-LED, reset-button or limit-switch documentation exists that we know of.

## What our own testing shows
- Not-ready state: ASCII console says GS=1, Z reads 0, TS; handshake ignored. Ready: GS=0, Z reads a real number, handshake works.
- Nudging the Y gantry ~5 mm flips it from not-ready to ready. This only fits if referencing is stuck waiting on Y.
- Most likely story (inference): at power-on the gantry sits ON the Y reference switch; the controller must drive Y off it to finish referencing; the Y motor does not drive, so it waits forever. Your hand does what the motor should.
- The head (X) moves on command, so the X driver and motor work. The gantry (Y) shows no motion and no sound when commanded.
- When the cards were swapped the machine would no longer become ready; swapped back it worked again.

## How to tell the cause apart
1. Power-on test: close the lid, switch on, watch and listen for 30 s. Does X move at start-up? Does Y? Does it beep? (Nothing moved last time = referencing never started its first axis, or the first axis is Y.)
2. Y motor test with power OFF: unplug the Y motor cable at the motor and measure each coil pair with a multimeter (a few ohms). Open = broken wire or motor.
3. Y motor test with power ON, motor unplugged from the board: touch nothing; with a scope or multimeter on AC volts you cannot safely do this - skip unless you have a scope.
4. Switch test: with power on and ready, run `python rayjet_survey.py watch` while you slowly push Y toward and away from the rear stop. The flag tags it prints should change at the switch. (Read-only.)
5. Card swap: swapping changed the behaviour, so the cards are not identical in position. Photograph each card and label it. Note the LED colours on each card at power-on, ready, and while a Y move is being commanded.

## LED log to fill in (write down for each card)
| Card | LED colour | Power on | Not ready | Ready | During Y command |
|---|---|---|---|---|---|

## ADDED 2026-11-13: the green "SM-NG" card (from your photo) - this is the motor/switch card, not the CPU card
Silkscreen "trotec SM-NG TOP", date code H07019. Chips: Trinamic TMC249A-SA stepper driver (top left), a second TI TMS320LF2407 DSP (centre),
4 small 8-pin power/driver ICs on the right, 74-series latches and level shifters on the left. Backplane connector on the left edge.
- Right edge: one tall white connector (6 positions, almost certainly the motor outputs) and two 3-pin white connectors, the lower one labelled "ES2".
  "ES" is very likely German "Endschalter" = limit/reference switch inputs. Inference, not documented.
- Cable label in your third photo: "H&S Kabeltechnik, Cable Reference Switch-Z, 31387, 220.01-66" - the reference switches have their own cables
  that plug into those ES connectors, so X, Y and Z each probably have a reference-switch cable.
- LEDs along the right edge, top to bottom: 30V, 5V, 3V3, CHA, CHB, TX, RX, ERR. Red reset button at bottom right, JTAG header and a "RESERVE" header at the bottom.
  Probable meaning (inference): 30V/5V/3V3 = supply rails OK; CHA/CHB = the two phases or the encoder channels; TX/RX = traffic with the CPU card; ERR = fault.
- Glass fuse at the top right of this card (clip holder). A blown fuse here would kill the 30 V motor supply and give exactly "motor silent, no error".
- Do not touch the many jumpers (JP2, JP4, JP8-JP13, yellow one near the crystal) until we know what they do; note their positions with photos.

### Checks, in order (power OFF and unplugged for 1-3 and 5; power on only for 4)
1. Fuse: pull it and measure continuity. No beep = blown.
2. Compare the two ES connectors and the motor connector seating on the card for Y against the X card.
3. Reference-switch cable for Y: look for a pinched or cut cable where the gantry moves.
4. LEDs with power on, per card: are 30V, 5V, 3V3 all lit? Is ERR lit? Do CHA/CHB/TX/RX flicker when X is commanded? Then command Y and compare.
5. If both axes share ONE green card: the Y fault is in the motor cable/motor/driver output, not the card. If there are TWO green cards, swap test is meaningful.

## ADDED 2026-11-13: more start-up and naming notes
- Start-up: switch on -> THE TABLE (Z) TRAVELS DOWN to its lowest position -> beep -> "calibrated", ready.
  So the machine's own reference run starts with Z going down. On this machine nothing moves at power-on, so the reference run is not even starting.
- Lid: if the lid is open at power-on, the keypad LED blinks rapidly and the machine does not respond; closing the lid starts the
  table moving down, then the beep. The lid has TWO interlock switches ("circuit breakers").
- Naming trap: in the machine's own terminology "the X-axis" is the beam assembly that is pulled toward the FRONT (it carries the head, lens, mirror, belt,
  bearings; it has a cable on the left). In our serial protocol X (0-475 mm) is the left-right head travel and Y (0-314 mm) is the front-back beam travel.
  Cards or cables labelled X/Y may follow that naming, not ours. Verify with the LED test before trusting any label.
- Mains fuses are at the power socket - separate from the glass fuse on the green motor card.
- Nothing we know of covers the cards, jumpers, LEDs, reset button, firmware or reference switches.

## Read-only test to separate "lid interlocks" from "Y reference switch" (machine on, COM3 present)
Poll the ASCII status flag GS (1 = not ready, 0 = ready) once a second while you do, one at a time, with ~10 s between: open the lid, close the lid,
nudge Y 5 mm, nudge it back. The action that flips GS is what the controller is waiting for.

## ADDED 2026-11-13: cable and connector identification worksheet
No cable colours, pin-outs or connector names are documented anywhere we know of. What the photos show so far:
- A grey round cable with a printed tag: "H&S Kabeltechnik GmbH, Cable Reference Switch-Z, 31387, 220.01-66". That tag text is a good search key.
- A black round cable next to it, a cream/white thick round cable crossing in front of the cards in several photos (purpose unknown).
- Green motor card (SM-NG): one tall white 6-position connector, two white 3-position connectors (one marked ES2).
- Nothing in our photos shows the individual wire colours of the motor or switch cables.

General colour conventions that MAY apply (not Trotec-specific, verify with a meter):
- 3-wire sensor / reference switch: brown = +supply, blue = 0 V, black = signal (standard for proximity sensors). A 3-pin connector on the card fits this.
- Stepper motor: 4 wires = two coil pairs; colours vary by maker. Identify pairs by measuring resistance with the power off (a few ohms across a pair, open between pairs).

Worksheet - fill one row per connector on each card, ideally with a straight-on photo of the plug in place and one of the cable's tag:
| Card (slot, label) | Connector (marking, pins) | Cable tag text | Wire colours pin 1 -> last | Goes to (motor / switch / which axis) |
|---|---|---|---|---|
| | | | | |

## ADDED 2026-11-13: owner's LED observations and the card stack photos
Observed by the owner with the machine powered:
- All power LEDs (30V, 5V, 3V3) are green on every driver card, so the supplies are fine.
- CHA and CHB are ORANGE (the others are green). They are lit when an axis sits at its zero/home position and go dark as soon as the axis
  is moved a short distance away. They behave like reference-sensor inputs, not motor phases. Z card: they go out as soon as the table leaves its zero.
- At power-on the front-back axis sits at zero, so its CHA/CHB are lit. Moving it a few mm forward turns them off; then the machine becomes ready and Z buttons work.
- The middle card's CHA/CHB went dark when the front-back axis was moved -> the middle card is the front-back card.
=> The reference sensors and their cable for the front-back axis work. The fault is on the DRIVE side (card output, motor cable, motor), not the sensing side.

Card stack, from the CPU card outward (from the photos; confirm by eye):
| Slot | Card sticker | Cable at its top connector | Axis |
|---|---|---|---|
| A (first driver) | 02991A 43/14 RV14.0045-018, no. 000204 | thick green-jacket cable under black heat-shrink; many wires incl. red, purple, black, blue, pink, grey | left-right (by elimination, unconfirmed) |
| B (middle) | 02991A 43/14 RV14.0045-018, no. 000208 | beige cable under blue heat-shrink; wires incl. yellow, black, brown, green, white | front-back (confirmed by LEDs) |
| C (last) | 02991A 17/09 RV17.0025-001, no. 000076 | grey shielded cable (LiYCY) under red heat-shrink, an inspection tag | Z / table (owner) |
IMPORTANT: card C is a different board type and age (RV17.0025, week 17 of 2009) than A and B (RV14.0045-018, week 43 of 2014). A and B look interchangeable;
C is not. If C was ever swapped with A or B, that alone explains why Z stopped responding. Keep C in its slot.

### Next tests (power off for the swap)
1. Photograph the jumpers and the pink rotary-looking part on A and B, close up, and compare them.
2. Swap only the MOTOR plugs of A and B (cards stay put; A and B are the same type), power on, nudge front-back to get ready, then command a left-right move and a front-back move.
   Whichever motor moves with which card shows whether the fault is card B's driver or the beam motor / its cable.
3. With the machine ready, run `python rayjet_survey.py watch` while the beam is moved in and out of its zero zone, to see the sensor state in software.

### Shorthand used by the owner (2026-11-13), by cable heat-shrink colour
- RED = Z / table (last card).
- BLUE = front-back (middle card; confirmed by its CHA/CHB LEDs going dark when the beam leaves zero).
- GREEN = left-right (first card; thick green-jacket cable with black heat-shrink; by elimination - still to confirm with the LEDs by pushing the head away from its home end).

## ADDED 2026-11-13 (late): the blue card reacts to front-back commands
- Owner saw the blue (middle) card's CHA/CHB LEDs blink in time with our front-back-only moves (13 cycles of 10 mm at 16:52:17-16:53:02), and on earlier runs.
  CHA/CHB therefore are not only home-position indicators: they also follow commanded motion on that card.
- The controller reports the moves as completed, status never shows an error; parameter table matches a Rayjet 50 (see Rayjet-Parameter-Table.md).
- Conclusion: the command reaches the blue card and its logic acts on it. The fault is downstream: motor driver output stage, motor current setting,
  the motor cable and plug, the motor winding, or the mechanics (coupling, pulley set-screw, belt).
- New candidate: the small pink square part on each green card may be a current-setting trimmer (not a rotary code switch). A card whose trimmer is turned to
  minimum would show LED activity but deliver no motor current. Compare its screwdriver-slot orientation on the blue card against the green card WITHOUT adjusting it.
- Tests, power off unless stated:
  1. Photograph the pink part and the jumpers on blue and green side by side, same angle.
  2. Reseat the blue card's motor connector and tug each wire gently to confirm it is clamped.
  3. Measure each motor winding at the plug (a few ohms per pair; open = broken).
  4. Swap only the motor plugs between blue and green, power on, nudge to ready, command each axis.
  5. Power on and ready: push the beam by hand; stiff = motor energised, free = no current.

## ADDED 2026-11-13 (late): LED polarity per axis - possible explanation of the nudge
Owner: with Z fully down, the right (Z) card's CHA/CHB are OFF. (Earlier note said they went off when Z LEFT zero - the two statements conflict; the latest is used here, to be re-confirmed.)
Beam (blue card): CHA/CHB are LIT at the power-on resting position and go OFF after the ~5 mm nudge, after which the machine becomes ready.
Hypothesis (unproven): for every axis the sensor LEDs read OFF when the axis is AT HOME. Z reaches that state by itself at power-on (its motor works). The beam rests where its LEDs
are lit, i.e. NOT at home by sensor logic, so the firmware tries to drive it home, the beam motor does not turn, and start-up never completes. The hand nudge moves it into the
"off = home" zone, which satisfies the routine. Test: after getting ready by nudging, power off WITHOUT touching the beam, power on again; if it becomes ready without a nudge, the theory holds.

## ADDED 2026-11-13 (late): CHA/CHB observations, Z card and a slow-move camera test
Owner, Z (right card): fully down = CHA and CHB off; anywhere in the middle = CHA lit; all the way up = CHA off. (CHB behaviour in the middle not stated.)
Owner, beam (blue card): both lit at the power-on rest position, both off after the ~5 mm nudge; blinks with our front-back commands.
Camera test (0.5 mm front-back move over 10 s, only that axis commanded): the middle column's two lower LEDs stepped through a repeating pattern
(both lit -> only the lower -> only the upper -> both lit) while the other columns stayed mostly steady. Frames were low resolution; not conclusive.
Two readings, not yet separated:
  A. CHA/CHB = end-stop / home switch circuits shown "lit = not tripped, off = tripped" (Z: off at both ends). Then the beam rests NOT at home, the firmware tries to drive it home at
     power-on, the beam motor does not turn, and the nudge trips the home switch by hand.
  B. CHA/CHB = drive-phase indicators whose pattern depends on step position (they blink on commands). Then the blue card is generating motor steps and the fault is downstream.
Deciding test (power on, ready, no commands): push the beam by hand a few mm each way and watch the blue card. LEDs that change only when the beam physically moves = switch/position (A).
Then run a slow commanded move while holding the beam still: LEDs that still cycle = drive indicators (B).

## ADDED 2026-11-13 (late): owner confirms the blue card LEDs alternate during a slow move
Owner watching the slow front-back test: the middle card's lights alternated CHA, CHB, CHA, CHB. Our camera frames showed the same one-then-the-other pattern.
=> Reading B is supported for the blue card: CHA/CHB are drive-phase indicators; the card is producing an alternating two-phase step sequence for the front-back motor.
The command path (PC -> controller -> blue card) therefore works. Remaining suspects, in order: motor plug/cable, motor winding, motor current (trimmer or stored parameter), coupling/pulley/belt.
Tests: (1) power off, unplug the beam motor plug, measure each winding (two pairs, a few ohms each, open between pairs) and compare with the left-right motor;
(2) swap only the motor plugs of the blue and green cards; (3) with power on and ready, run `python slow_fb.py` and feel/listen at the motor.

## ADDED 2026-11-13 (late): left-right re-verified, green card LED behaviour
- Owner confirmed the left-right head still moves as yesterday (two rounds of 50 mm out and back at 16:58:37-16:58:55; controller reported X 0 -> 10000 -> 0 each time).
- Camera, slow 30 mm left-right move: on the green card one of the two lower LEDs lit briefly during each move (twice in total) and was otherwise off; the other stayed steady.
  The owner describes the same: lights come on, the head moves, lights go off, repeat on the way back.
- The green (working) and blue (not moving) cards both show LED activity that follows commanded moves. LED activity therefore tells us the card is being driven,
  not that the axis physically moves. The difference between the two axes lies after the card: motor plug/cable, winding, current setting, or mechanics.

## ADDED 2026-11-13 (late): left-right scale and direction confirmed by the owner
10000 steps of the move command = 50 mm, from the left 0 position to 50 mm toward the right and back. So X: 5 um per step (matches parameter 3 = 5000 nm), positive X = rightwards.
Y scale could not be checked (the beam does not move). The stored Y step is 3.75 um (parameter 4 = 3750 nm), so the 5 um assumption may not hold for Y.

## ADDED 2026-11-13 (late): controller view of front-back vs left-right (17:08:32-17:09:07, 400 steps/s, 12 mm each way)
Logged every status tag, flag and diagnostic id 0-8 at 4 Hz. Front-back and left-right look identical to the controller: positions advance smoothly at about 390-400 steps/s
and return to 0, state 03 -> 04 -> 03, no flag tags, diagnostics unchanged (ids 0-8 = 0, id 8 = 1023), no unknown tags.
=> The controller reports no fault or limit condition for the front-back axis. Positions are open-loop (counted steps). The beep and the CHB change are NOT visible in any status data.
Owner observation after the speed ladder: CHB went off and the machine beeped while front-back moves were commanded; suggestion: direction may be reversed.
Untested idea: move the beam by hand to mid-travel first, then command front-back moves; if the beam then moves, the rest position is blocked in the commanded direction (limit or direction problem); if not, motor/drive.
