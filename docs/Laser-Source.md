# The laser source: Synrad Firestar v30 (2026-11-14)

Identified from the laser's own labels. This is the sealed CO2 source inside our Rayjet 50.

## Identification
- Maker: Synrad. Series: Firestar v. Model: FSV30SAG. Made October 2014. Runs from a 30 V DC supply.
- Type: RF-excited, sealed CO2 laser, wavelength ~10.6 um (the 10200-10800 nm on the label is the CO2 band).
- Rated 30 W (the "75 WATTS MAX" sticker is a generic safety-label ceiling for the housing, not this unit's output;
  the v30 model and "tested at 30 V" identify it as the 30 W version). Class 4.
- (The unit's serial number is recorded privately and kept out of this repo.)

## The connector that looks like "ethernet"
- The cable is a modular RJ-style connector plugging into the jack labelled "Interface B" on the laser, with three
  status LEDs beside it: **PWR** (power), **RDY** (ready / armed), **LASE** (actively lasing).
- This is **not** a network/ethernet link. On the Firestar the interface connectors carry the laser's control and
  status signals. The Firestar v-series normally has two such jacks (Interface A and Interface B).
- Observed LED state while powered: PWR green on, RDY yellow on, LASE red off = the laser has power, is ready/armed,
  and is not firing. So the laser source itself is healthy. This supports the conclusion that our fault is the Y
  axis, not the laser.

## How it connects to the controller
- The Interface cable runs from the laser's Interface B jack to the Rayjet controller board (the main green board),
  not to the PC. The PC only reaches the controller over USB-serial; it has no link to the laser (the PC's ethernet
  port is disconnected - verified).
- So the controller is what drives the laser. On Synrad RF lasers the control is a 5 V **PWM command** signal
  (a low-duty "tickle" keeps the plasma primed; higher duty = more power) plus a gate/enable and an interlock. The
  controller generates these on the interface cable; there is no packet "handshake" on the control line.

## Is there a protocol we could talk to? (to verify from the Synrad manual)
- The Firestar series also supports an **RS-232 serial diagnostic/command interface** (ASCII command set) that can
  report status, case temperature, PWM duty, operating hours, model and faults, and in some modes command lasing.
  This is a real request/reply protocol - the kind of "handshake" we were looking for.
- NOT yet confirmed for this exact unit: which jack (A or B) carries the RS-232 lines, the pinout, the baud rate and
  the command bytes. These must come from the Synrad Firestar v-series operator's manual before anything is wired.
- Important: that interface is on the laser, which is currently cabled to the controller. Talking to it directly
  would mean tapping the laser's serial pins with a USB-RS232 adapter at the correct pinout - a separate, careful job.

## Safety note
- When RDY is lit the laser is armed: if the controller asserts the PWM command and gate, it WILL fire. Reading the
  laser's serial diagnostics is safe; sending any lase/gate command is not. Never command lasing without the beam
  contained, the key/interlock managed and people clear.
