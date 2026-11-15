# Laser command test matrix (auto-generated)

Generated 2026-11-14 21:46. Source: fuzz_logs/matrix.jsonl plus the earlier hand-logged results.

Legend: DONE = run and recorded | TODO = not yet run | DISTURB = run, disturbs the machine (recover by power cycle) | IRREVERSIBLE = listed, not auto-run.

| Section | Trial | Status | LASE light | Note |
|---|---|---|---|---|
| alone | C2 alone | TODO |  |  |
| alone | C4 alone | TODO |  |  |
| alone | C6 alone | TODO |  | contains a disturbing opcode |
| alone | C8 alone | TODO |  |  |
| alone | B3 alone | TODO |  | contains a disturbing opcode |
| alone | B7 alone | TODO |  | contains a disturbing opcode |
| alone | BB alone | TODO |  |  |
| alone | BF alone | TODO |  |  |
| alone | C3 alone | TODO |  |  |
| alone | C7 alone | TODO |  |  |
| alone | CB alone | TODO |  |  |
| alone | CD alone | TODO |  | contains a disturbing opcode |
| alone | CF alone | TODO |  |  |
| alone | 32 alone | TODO |  |  |
| alone | B1 alone | TODO |  | contains a disturbing opcode |
| alone | B9 alone | TODO |  |  |
| alone | BD alone | TODO |  |  |
| alone | C1 alone | TODO |  |  |
| alone | C5 alone | TODO |  |  |
| alone | 8A alone | TODO |  |  |
| alone | 8C alone | TODO |  |  |
| alone | 8E alone | TODO |  |  |
| alone | 90 alone | TODO |  |  |
| alone | B5 alone | TODO |  |  |
| alone | 80 alone | TODO |  |  |
| alone | AE alone | TODO |  |  |
| alone | C9 alone | TODO |  | contains a disturbing opcode |
| alone | 0A ch1 alone | TODO |  |  |
| alone | 0A ch2 alone | TODO |  |  |
| alone | 0A ch3 alone | TODO |  |  |
| alone | 0A ch4 alone | TODO |  | contains a disturbing opcode |
| alone | 0C ch1 alone | TODO |  |  |
| alone | 0C ch2 alone | TODO |  |  |
| alone | 0C ch3 alone | TODO |  |  |
| alone | 0C ch4 alone | TODO |  |  |
| move | C2 then 9F move | TODO |  |  |
| move | C4 then 9F move | TODO |  |  |
| move | C6 then 9F move | TODO |  | contains a disturbing opcode |
| move | C8 then 9F move | TODO |  |  |
| move | B3 then 9F move | TODO |  | contains a disturbing opcode |
| move | B7 then 9F move | TODO |  | contains a disturbing opcode |
| move | BB then 9F move | TODO |  |  |
| move | BF then 9F move | TODO |  |  |
| move | C3 then 9F move | TODO |  |  |
| move | C7 then 9F move | TODO |  |  |
| move | CB then 9F move | TODO |  |  |
| move | CD then 9F move | TODO |  | contains a disturbing opcode |
| move | CF then 9F move | TODO |  |  |
| move | 32 then 9F move | TODO |  |  |
| pair | B5(+16) + B7 alone | TODO |  |  |
| pair | B5(+16) + B7 then 9F move | TODO |  |  |
| pair | B9(+32) + BB alone | TODO |  |  |
| pair | B9(+32) + BB then 9F move | TODO |  |  |
| pair | BD(+32) + BF alone | TODO |  |  |
| pair | BD(+32) + BF then 9F move | TODO |  |  |
| pair | C1(+32) + C3 alone | TODO |  |  |
| pair | C1(+32) + C3 then 9F move | TODO |  |  |
| pair | C5(+32) + C7 alone | TODO |  |  |
| pair | C5(+32) + C7 then 9F move | TODO |  |  |
| job | B5=1 + B7 + 9F move | TODO |  |  |
| job | B9=1 + BB + 9F move | TODO |  |  |
| job | BD=1 + BF + 9F move | TODO |  |  |
| job | C1=1 + C3 + 9F move | TODO |  |  |
| job | C5=1 + C7 + 9F move | TODO |  |  |
| value | write param 4A=1 then 9F move | TODO |  |  |
| value | write param 4B=1 then 9F move | TODO |  |  |
| value | write param 4C=1 then 9F move | TODO |  |  |
| value | write param 4D=1 then 9F move | TODO |  |  |
| value | write param 4E=1 then 9F move | TODO |  |  |
| value | write param 4F=1 then 9F move | TODO |  |  |
| value | write param DE=1 then 9F move | TODO |  |  |

## Irreversible (listed, not auto-run)

| Opcode | Meaning | Why excluded from sweeps |
|---|---|---|
| 85 | store parameters to flash | permanent; overwrites stored settings |
| AA AB AC AE | licence / pay-per-use | permanent; licence data |