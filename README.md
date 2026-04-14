# Monk Clock

**Sun-based time for the modern monk.**

A digital clock that tells time according to the position of the sun, not an arbitrary timezone. Daylight and nighttime are each divided into 12 equal hours—their lengths vary with the seasons.

![Monk Clock](https://img.shields.io/badge/Monk%20Time-Sunrise-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## The Idea

Traditional clocks force the sun to fit our schedule. Monk Clock inverts this: your day starts at sunrise and ends at sunset. In summer, daylight hours are longer (more time to work!). In winter, they're shorter (more time to rest!). The monks would approve.

```
Monk Time:  "7¼ hours after sunrise"
Standard:   2:05:23 PM
Daylight:   13h 6m
Monk Day Hours:   65.5 min each
Monk Night Hours: 54.5 min each
```

## Installation

```bash
git clone https://github.com/yourusername/monkclock.git
cd monkclock
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install ephem rich timezonefinder art
```

## Quick Start

```bash
# Basic display
python monkclock.py

# With sundial
python monkclock.py --clock

# Live updating TUI
python monkclock.py --live

# Live with sundial
python monkclock.py --live --clock

# Set your location (once, saved to ~/.config/monkclock/config)
python monkclock.py --set-location 36.367 -95.664

# Use different location (overrides saved)
python monkclock.py --lat 51.5074 --lon -0.1278
```

## How Monk Time Works

### The Basic Idea

1. **Sunrise** → The 1st Hour begins
2. **12 hours later** → The 12th Hour ends, sunset
3. **Sunset** → The 1st Hour of Night begins
4. **12 hours later** → The 12th Hour of Night ends, sunrise

### Variable Hour Lengths

In summer at mid-latitudes:
- Each **day hour** ≈ 65 minutes (long daylight)
- Each **night hour** ≈ 55 minutes (short night)

In winter at high latitudes (London, for example):
- Each **day hour** ≈ 39 minutes (short daylight)
- Each **night hour** ≈ 81 minutes (long night)

The earth doesn't care about our 60-minute hours—why should we?

### The Sundial Display

When using `--clock`, you see an ASCII sundial:
- **Roman numerals (I-XII)** mark the hours
- **Gnomon (^)** at center casts the shadow
- **Shadow (▒)** points to your current position in the day

The shadow moves continuously, showing progress through the current hour and across the day.

### Digital Readout

Instead of "2:30 PM", you see:
- `"7¼ hours after sunrise"` — how many monk hours have passed

This tells you how far through the sun-based day you are.

## Features

- **Sun-based hours**: No timezones, no DST, just the sun
- **Variable hour lengths**: Summer = long days, winter = long nights
- **Location-aware**: Set your latitude/longitude for accurate sun times
- **ASCII sundial display**: Traditional look with a modern monk twist
- **Live mode**: Watch the shadow move in real-time
- **Rich TUI**: Colorful terminal interface

## Configuration

Location is stored in `~/.config/monkclock/config`:
```
latitude=36.367
longitude=-95.664
```

Or use environment variables:
```bash
export MONKCLOCK_LAT=51.5074
export MONKCLOCK_LON=-0.1278
python monkclock.py
```

## Finding Your Coordinates

- [latlong.net](https://latlong.net) — click your location on the map
- Or just let Google know and search "my coordinates"

## Examples

### Your Location (Oklahoma, April)
```bash
$ python monkclock.py --lat 37.7749 --lon -122.4194
   __  ___  ____    _  __   __ __
  /  |/  / / __ \  / |/ /  / //_/
 / /|_/ / / /_/ / /    /  / ,<   
/_/  /_/  \____/ /_/|_/  /_/|_|  
                                 
  _____   __   ____   _____   __ __
 / ___/  / /  / __ \ / ___/  / //_/
/ /__   / /__/ /_/ // /__   / ,<   
\___/  /____/\____/ \___/  /_/|_|  

The 7th Hour of Day
of the Day

Approximate Digital: 6¾ hours after sunrise

Standard Time: 1:58:19 PM
Sunrise: 6:50 AM
Sunset: 7:56 PM
Daylight: 13h 6m
Monk Day Hours: 65.5 min each
Monk Night Hours: 54.5 min each
This hour: 65.5 min

Location: 37.7749, -122.4194
```

### With Sundial
```bash
$ python monkclock.py --clock

The 7th Hour of Day
of the Day

6¾ hours after sunrise

        ^
      · XII ·
    XI ·     · I
   ·   │     ·   ·
  X    │      ·   II
      │
  IX   │       ·   III
       │
   VIII        ·   IV
        ·   ·
          VII · V
            VI

═══ DAY ═══
  7th Hour
6¾ hours after sunrise

Standard: 2:01:57 PM
Sunrise: 6:50 AM
Sunset: 7:56 PM
Daylight: 13h 6m
Monk Day Hrs: 65.5 min
Monk Night Hrs: 54.5 min
```

### London (Winter!)
```bash
$ python monkclock.py --lat 51.5074 --lon -0.1278

The 10th Hour of Day
of the Day

Approximate Digital: 9 hours after sunrise

Standard Time: 1:50:28 PM
Sunrise: 8:03 AM
Sunset: 3:54 PM
Daylight: 7h 51m
Monk Day Hours: 39.3 min each
Monk Night Hours: 80.7 min each
This hour: 39.3 min

Location: 51.5074, -0.1278
```

Winter in London: each day hour is only 39 minutes! But each night hour is 81 minutes. The monks would have approved of long winter nights for prayer and rest.

## Philosophy

> "The sun does not accelerate for anyone."
> — Ancient monastic wisdom (probably)

Modern time is arbitrary: 60-minute hours, 24-hour days, timezone boundaries that cut through countries. Monk Clock reminds us that the sun doesn't negotiate.

This is a fun project, not a serious timekeeping system. Don't use it to schedule meetings unless you want confused colleagues.

## Dependencies

- **ephem**: Astronomical calculations for sunrise/sunset
- **rich**: Terminal UI framework
- **timezonefinder**: Convert coordinates to local timezone
- **art**: ASCII art for the splash screen

## License

MIT — Do whatever you want with it. May your hours be as variable as the seasons.

---

*"The 7th Hour of the Day, of the Day"* — Monk Clock