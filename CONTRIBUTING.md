# Contributing to raybreak

Thanks for helping! You do **not** need to be a programmer. The most valuable thing right now is **test results from real machines**.

## Ways to help (easiest first)
1. **Run the read-only report** on your Rayjet and open a "Compatibility report" issue. See the README quick start.
2. **Tell us what you know**: CHA/CHB LED behaviour on your cards, jumper settings, motor wiring, photos of your cards (see `docs/Wiring-and-Card-Photos.md`).
3. **Work through `TODO.md`** if you have the same machine: multimeter checks, the motor-plug swap, mid-travel test.
4. **Improve docs**: fix mistakes, clarify wording, add diagrams.
5. **Code**: other axes, jobs/laser control (carefully), a nicer GUI, Linux/macOS support, tests.

## Ground rules
- **Safety first.** Scripts move real hardware. Keep the laser tube disconnected while testing motion. Power off and unplug before touching connectors. Never send the persistent-store opcode (`85`) unless you have saved a full parameter dump first.
- **Say how sure you are.** Mark claims as TESTED, DECODED, INFERRED or guess, as the docs do. Please do not present guesses as facts.
- **Write in your own words.** Do not paste copyrighted documents, binaries, firmware, install media or licence data. Do not post your machine serial number or CPU id.
- **No tools that require weakening Windows security** (test-signing, disabling driver signature checks, turning off Smart App Control). Windows 11 compatible methods only.
- Be kind. See `CODE_OF_CONDUCT.md`.

## Reporting results
Use the issue templates. Include the model, firmware string from the handshake, what you did, what happened, and photos if helpful. Negative results ("did not move") are just as useful as positive ones.

## Pull requests
Small, focused changes are easiest to review. Describe what you tested and on which machine. Docs changes need no hardware.

## License of contributions
By contributing you agree that your contribution is released under the project license (MIT, see `LICENSE`).
