# Rayjet 50 parameter table, read from our machine on 2026-11-13 (read-only dump, 256 entries)

Source file: `params_dump_20261113_164121.json`. Request `20 idx` in the packet ext part; the machine answers `21 idx <be32> <be32>` in the same reply (second number = value).

## Entries we can explain

| Index | Value | Meaning | Evidence |
|---|---|---|---|
| 0x03 | 5000 | X step 5.000 um | matches the standard Rayjet 50 setting (5) |
| 0x04 | 3750 | Y step 3.750 um | matches the standard setting (3.75) |
| 0x05 | 192 | Z step 0.192 um | matches the standard setting (0.192) |
| 0x07 | 94400 | X travel in 5 um units (472 mm) | close to the specified 475 mm |
| 0x08 | 62800 | Y travel in 5 um units (314 mm) | equals the specified 314 mm |
| 0x4A | 350 | tickle delay | standard tickle delay 350 |
| 0x4C | 50 | minimum tickle power | standard minimum tickle power 50 |
| 0x0B-0x0E | 100000 / 304800 / 100000 / 40000 | four settings (acceleration-like) | meaning unconfirmed |
| 0xBE-0xF9 | equal to their own index | not stored settings: padding/system area | the same ranges look like padding in every dump |

## What this tells us

- The stored engraver settings match a Rayjet 50 (step sizes and travel agree with the Rayjet 50 specification), so the stored table was NOT wiped by the firmware change.
- The front-back axis has its own step size (3.75 um) and travel, so the table is not obviously wrong for that axis.
- Four repeating blocks (indices 0x61, 0x78, 0x8F, 0xA6, each starting with 32640) look like four laser-source or channel parameter sets, not axes.
- No axis-enable or axis-disable flag is visible; zeros are scattered but without a reference dump we cannot say which one is wrong.

## Full table (index = value)

`00=21  01=0  02=1  03=5000  04=3750  05=192  06=5000  07=94400`  
`08=62800  09=765625  0A=218237380  0B=100000  0C=304800  0D=100000  0E=40000  0F=2`  
`10=2  11=1  12=1  13=7  14=1  15=0  16=1  17=1`  
`18=1  19=2  1A=4  1B=6  1C=6  1D=8  1E=8  1F=10`  
`20=10  21=10  22=10  23=10  24=10  25=10  26=10  27=80`  
`28=40  29=60  2A=30  2B=60  2C=30  2D=60  2E=30  2F=60`  
`30=30  31=20  32=20  33=40  34=40  35=40  36=40  37=0`  
`38=15  39=0  3A=0  3B=2600  3C=800  3D=0  3E=0  3F=0`  
`40=0  41=0  42=0  43=0  44=0  45=0  46=0  47=0`  
`48=0  49=0  4A=350  4B=5000  4C=50  4D=1000  4E=264583  4F=1000`  
`50=0  51=1500  52=961296  53=1579  54=0  55=0  56=8214123  57=3300238`  
`58=300  59=50  5A=3000  5B=700  5C=7000  5D=6500  5E=1000  5F=5000`  
`60=0  61=32640  62=400  63=300  64=5000  65=200  66=5000  67=500`  
`68=32784  69=100  6A=500  6B=255  6C=4  6D=20000  6E=0  6F=100`  
`70=100  71=100  72=500  73=28000  74=27000  75=1000  76=20000  77=0`  
`78=32640  79=400  7A=300  7B=5000  7C=200  7D=5000  7E=500  7F=32784`  
`80=100  81=500  82=255  83=4  84=25000  85=0  86=300  87=0`  
`88=4500  89=0  8A=0  8B=0  8C=1000  8D=20000  8E=0  8F=32640`  
`90=200  91=50  92=0  93=0  94=0  95=0  96=32784  97=0`  
`98=6098  99=255  9A=50  9B=15000  9C=0  9D=300  9E=50  9F=3000`  
`A0=700  A1=7000  A2=6500  A3=1000  A4=5000  A5=20  A6=32640  A7=400`  
`A8=300  A9=0  AA=38400  AB=0  AC=63800  AD=32784  AE=100  AF=500`  
`B0=255  B1=4  B2=25000  B3=0  B4=13797764  B5=0  B6=0  B7=0`  
`B8=21639848  B9=18800  BA=0  BB=10  BC=0  BD=0  BE=190  BF=191`  
`C0=192  C1=193  C2=194  C3=195  C4=196  C5=197  C6=198  C7=199`  
`C8=200  C9=201  CA=202  CB=203  CC=204  CD=205  CE=206  CF=207`  
`D0=208  D1=209  D2=210  D3=211  D4=212  D5=213  D6=214  D7=215`  
`D8=216  D9=217  DA=218  DB=219  DC=220  DD=221  DE=222  DF=223`  
`E0=0  E1=0  E2=0  E3=0  E4=100  E5=1000  E6=20  E7=2000`  
`E8=0  E9=255  EA=10000  EB=235  EC=236  ED=237  EE=238  EF=239`  
`F0=240  F1=241  F2=242  F3=243  F4=244  F5=245  F6=246  F7=247`  
`F8=248  F9=249  FA=1598  FB=1598  FC=1598  FD=1598  FE=1598  FF=0`  