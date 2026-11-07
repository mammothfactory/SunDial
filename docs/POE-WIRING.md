# PoE wiring — read this first

## The honest bit

The M5Stack Dial v1.1 has **no native PoE and no Ethernet port**. It is
powered by USB-C 5 V or by DC 6–36 V into its 2.54 mm terminal, and it
talks to the hub over 2.4 GHz Wi-Fi.

PoE in SunDial therefore means: **one Cat6 cable to each room, carrying
power only, terminated in a PoE splitter at the wall.** The splitter
extracts power from the cable and hands the Dial clean 5 V (or 12 V).
You still get the single-cable, no-wall-wart, always-on benefit — the
data path is Wi-Fi, not the cable.

## Parts per room

| Part | Notes |
|---|---|
| PoE switch, 802.3af/at | Any managed/unmanaged 802.3af (15.4 W/port) switch; at is fine too |
| Cat6 cable, switch → room | Run to a low-voltage wall box / keystone behind the dial |
| PoE splitter, 802.3af/at → 5 V USB-C | **Certified** splitter, 5 V / ≥1 A USB-C out (preferred route) |
| — or splitter → 12 V DC | Into the Dial's 6–36 V DC terminal, if you prefer the terminal input |
| Short USB-C cable (or 2-wire DC lead) | Splitter → Dial; keep it short and tidy behind the mount |

## Wiring

```
PoE switch (802.3af/at) ── Cat6 ──► PoE splitter ── 5V USB-C ──► M5Stack Dial
                                    (at the wall)              (Wi-Fi to hub)
```

## Power budget

- One Dial draws 5 V @ 88.19 mA ≈ **0.44 W** operating.
- Budget **1 W per dial** to be safe (screen bright, buzzer, Wi-Fi TX).
- A houseful — say 8 dials — is ~8 W total. A single 24-port 802.3af
  switch (370 W budget is typical) powers that with enormous headroom,
  plus cameras/APs. No per-room power supply is needed.

## Safety

- Use a **certified 802.3af/at splitter**. Never feed a passive 48 V
  injector straight into USB-C, and never wire raw PoE pairs to the
  Dial's DC terminal — the splitter's DC-DC stage is what makes the
  voltage safe for the Dial.
- Keep low-voltage Cat6 / USB-C wiring separate from mains wiring and
  out of mains boxes. If in doubt, get an electrician for the cable run;
  the splitter and Dial connections are low-voltage DIY.
- The Dial's DC input accepts 6–36 V; a 12 V splitter output is inside
  that range, a 48 V output is not — check the splitter's output label
  before connecting.
