# Hardware — M5Stack Dial v1.1

One dial per room, wall-mounted, powered over PoE (see `POE-WIRING.md`).

## Verified specs

Source: https://shop.m5stack.com/products/m5stack-dial-v1-1 — $34.90.

| Item | Spec |
|---|---|
| SoC | ESP32-S3FN8, dual-core Xtensa LX7 @ 240 MHz, 8 MB flash |
| Wi-Fi | 2.4 GHz |
| Display | 1.28" round TFT, 240×240, GC9A01 |
| Touch | FT3267 (ESPHome: `ft5x06`, I2C 0x38) |
| Rotary encoder | 16 positions, 64 pulses/rev — GPIO40 / GPIO41 |
| RFID | WS1850S, 13.56 MHz, ISO/IEC 14443 Type A/B (ESPHome: `rc522_i2c`, 0x28) |
| RTC | BM8563 (ESPHome: `pcf8563`, 0x51) |
| Buzzer | 80 dB — GPIO3 |
| Button | GPIO42 (under-screen buttons) |
| Power-hold | GPIO46 |
| Port A | Grove I2C — G13 SDA / G15 SCL |
| Port B | Grove GPIO — G1 / G2 |
| Power in | DC 6–36 V wide input (2.54 mm 2P terminal), USB-C 5 V, Li-ion battery interface + charging |
| Operating current | 5 V @ 88.19 mA (~0.44 W) |
| Size / weight | 51.0 × 51.0 × 32.3 mm, 46.2 g |
| Platforms | UiFlow2, Arduino IDE, ESP-IDF, PlatformIO |

## What it does NOT have

No Ethernet port and no native PoE. Power over Ethernet is delivered by
an external 802.3af/at splitter at the wall (see `POE-WIRING.md`); data
stays on 2.4 GHz Wi-Fi. There is no speaker (buzzer only) and no microphone.

## ESPHome pin map (used in `firmware/esphome/m5dial.yaml`)

- Encoder: `rotary_encoder`, GPIO40 / GPIO41
- Display: `gc9a01`, model `M5STACK_DIAL`
- Touch: `ft5x06`, address 0x38
- RTC: `pcf8563`, address 0x51
- RFID: `rc522_i2c`, address 0x28
- Button: GPIO42 · Buzzer: GPIO3 (via `rtttl`)
- I2C bus: SDA GPIO13, SCL GPIO15
