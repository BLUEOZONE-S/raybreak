# Rayjet 50 - machine overview (our own wording)

Facts about the machine as we understand them, with our own observations marked.

## 1. Axis names used in this project
The beam assembly that carries the head, lens, mirror, belt and bearings is sometimes called the "X-axis" in the machine's own terminology and is the part you pull toward the front. That differs from common usage, so we do not use it.

| Our name | What moves | Serial protocol | Status on our machine |
|---|---|---|---|
| left-right axis | the head carriage along the beam | X, 0-475 mm | works |
| front-back axis | the whole beam assembly front to back | Y, 0-314 mm | does not move |
| Z / table | the work table, up and down, 145 mm travel | Z | works |

The protocol mapping is our inference from the travel limits and from what we saw when X was commanded (the head moved left and right).

## 2. Start-up behaviour
- On power-on the machine runs a reference routine: the table lowers to its lowest point and the machine beeps when it is ready. On our machine this works every time.
- All three axes are referenced at start-up, and only with the top lid and the other protective panels closed.
- Two protective covers are monitored: the top lid and the maintenance panel on the right side. Opening either stops motion and laser output. After closing, the machine needs about five seconds before it accepts commands again.
- If a cover is open during switch-on, the two status LEDs alternate between green and red and the machine sounds a warning instead of referencing. The lid carries two interlock switches.
- Our own observation: after power-on the machine can sit in a "not ready" state in which the Z buttons do nothing and the PC link refuses to start. Moving the front-back axis by hand a few millimetres ends that state. This suggests the reference routine is waiting for the front-back axis, and that axis cannot move itself.
- Both covers behave as expected on our machine, so the interlocks are treated as working and are not the cause of the not-ready state.

## 3. Front panel
Six controls: Z up, Z down, start/pause, stop, and two status LEDs. Z up/down move the table by hand and work only once start-up has finished. Start/pause starts or resumes a job; stop ends it. LED meanings: slow green flash = ready, fast green flash = a cover was opened, steady green = data waiting or paused, steady red = laser firing, alternating green/red = cover open at switch-on and no referencing.

## 4. Hardware facts
- Stepper motors. Engraving area 457 x 305 mm, table travel 145 mm, top speed about 1.5 m/s.
- USB connection to the PC through an FTDI serial bridge. Double interlock system, 30 W sealed CO2 tube.
- Mains fuses sit in the power inlet. The head module contains bearings, a focus lens, a mirror and a toothed belt. A second mirror sits at the right side behind the maintenance panel on magnetic mounts.
- Routine care: clean the interior and table daily and check the lens and mirrors regularly. Always power off and unplug first.
- Setup order: mains first, then the USB cable to the PC, then the exhaust connection; switch on the computer before the engraver.

## 5. Basic troubleshooting
- Machine dead after switch-on: check the mains connection and the mains fuses.
- No referencing and a warning sound: check that the lid is closed firmly and that the interlock circuit is closed.
- "Cannot connect": check the USB cable and the COM port.
- Exhaust does not start with a job: check its mains supply and the control cable.

Nothing in this list covers the controller cards, jumpers, reset button, firmware, motor wiring or the reference switches, which is why the board guide exists.

## 6. The controller cards (from our photos)
- CPU card: "Trotec Speedy2 CPU", revision 2.0, week 38 of 2014. Infineon C167 processor, external flash, a TI motion DSP, a UART, a reset button, two jumpers and several pin headers.
- Driver cards, silkscreen "SM-NG": Trinamic stepper driver chip, another TI DSP, eight status LEDs (30V, 5V, 3V3, CHA, CHB, TX, RX, ERR), a reset button, a glass fuse, JTAG and spare headers, a tall motor connector and two three-pin connectors, one marked ES2. A cable tag reads "Reference Switch-Z", so each axis probably has its own reference-switch cable.
- Meanings of the LEDs, jumpers and the rotary-switch-looking part are guesses until observed.
- Swapping two of these cards made the machine stop becoming ready; swapping them back restored it.

See `docs/Wiring-and-Card-Photos.md`.

## 7. Open questions
1. How a card learns which axis it drives (jumper, rotary switch, slot, or stored setting).
2. Where the reference switches are and how the controller reads them.
3. Why the front-back axis does not step even though the controller reports completing the move.
4. What the second state byte and the extra status flags in the packet protocol mean.

## 8. The rotary attachment connection (worth checking on the front-back fault)
- When a rotary engraving device is used, the machine's automatic Y-direction travel becomes rotation of the object instead. Y is the front-back direction, matching our naming.
- The rotary device plugs into a socket on the left inside the working area, and the machine is restarted before use, which hints that the controller checks for it at power-on (our inference).
- Hypothesis: if the controller wrongly believes a rotary device is connected (damaged or contaminated socket, shorted pin, wiring fault), it could send the front-back step pulses to the rotary output instead of the beam motor. That would give exactly what we see: a front-back move that is "completed" with no motion, no sound and no error. Unproven.
- Checks: look at that socket with the power off (empty? bent or dirty pins? stray cable?), and note where its wiring goes on the driver card.
- Related clue: the controller reports an options mask of 5 supported and 1 active. We do not know what the bits mean. If a rotary device is ever connected, see whether the active mask changes.
