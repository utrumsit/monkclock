# Monk Clock

**Sun-based time for the modern monk.**

A digital clock that follows the sun instead of your phone's clock. Daylight and nighttime are each divided into 12 hours—but those hours change length with the seasons. In summer, each daylight hour is longer. In winter, each daylight hour is shorter.

---

## Two Ways to Run Monk Clock

### 🖼️ Window Mode (Easiest for Beginners)
Opens a clock window on your computer. Just looks at it and closes when you're done.

```
python monkclock_gui.py
```

### 💻 Terminal Mode (For Power Users)
Shows colorful time information in your command prompt. Can also display a live-updating sundial.

```
python monkclock.py                # Quick check
python monkclock.py --live         # Updates every second
python monkclock.py --live --clock # Live sundial!
```

---

## Installation (One-Time Setup)

### 1. Install Python 3.13

Download from [python.org](https://www.python.org/downloads/) if you don't have it. (Python 3.13 includes the graphics library needed for the window mode.)

### 2. Set Up Monk Clock

```bash
# Navigate to the Monk Clock folder
cd monkclock

# Create a virtual environment (keeps Monk Clock's files separate)
python3.13 -m venv venv

# Turn it on (do this every time you open a new terminal)
source venv/bin/activate

# Install everything Monk Clock needs
pip install ephem rich timezonefinder art
```

### 3. Tell Monk Clock Where You Are

```bash
python monkclock.py --set-location 37.7749 -122.4194
```

Replace those numbers with your own latitude and longitude (find them at [latlong.net](https://latlong.net)).

Your location is saved and remembered—you only need to do this once.

---

## How to Run

### Window Mode (Recommended for Most People)

```bash
source venv/bin/activate
python monkclock_gui.py
```

A clock window opens showing:
- **The current monk hour** (e.g., "5th Hour")
- **Day or Night** (color changes—warm yellow for day, soft blue for night)
- **Progress bar** showing how far you are through the current hour
- **Sunrise and sunset times** for today
- **Standard clock time** for comparison

Close the window when you're done.

### Terminal Mode

**One-time check:**
```bash
python monkclock.py
```

**Live display (updates automatically):**
```bash
python monkclock.py --live
```

**With ASCII sundial:**
```bash
python monkclock.py --live --clock
```

The sundial shows a shadow that moves continuously, pointing to your current position in the day.

---

## Understanding the Display

### The Monk Hour

Monk time divides the day into 12 hours and the night into 12 hours. Each "monk hour" can be any length from 30 minutes to 90 minutes, depending on the season and where you live.

You don't see "2:30 PM." Instead, you see something like:

- **"7¼ hours after sunrise"** — how far through the daylight you are
- **"3rd Hour of Day"** — you're in the third hour since sunrise

### The Progress Bar

The progress bar shows how far you are through the current hour:

```
[████████░░░░░░░░] 67%
```

If the bar fills up, a new monk hour has begun.

### Variable-Length Hours

In summer (long days):
- Each daylight hour might be **65-75 minutes**
- Each night hour might be **50-60 minutes**

In winter (short days):
- Each daylight hour might be **40-50 minutes**
- Each night hour might be **65-80 minutes**

At extreme latitudes (like northern Scandinavia), this effect is even more dramatic. The monks would have approved—they prayed when the sun was up, whatever "hour" that happened to be.

---

## How Monk Time Works

1. **Sunrise** → The 1st Hour of Day begins
2. **12 hours later** → The 12th Hour of Day ends (sunset)
3. **Sunset** → The 1st Hour of Night begins
4. **12 hours later** → The 12th Hour of Night ends (sunrise)

The sun doesn't care about your 60-minute hours. Neither does Monk Clock.

---

## Finding Your Coordinates

1. Go to [latlong.net](https://latlong.net)
2. Click on your location on the map
3. Copy the numbers shown as "Latitude" and "Longitude"

Or search Google for "my coordinates" and look for the numbers.

---

## Setting Your Location

**One-time setup:**
```bash
python monkclock.py --set-location 37.7749 -122.4194
```

**Override for one session:**
```bash
python monkclock.py --lat 51.5074 --lon -0.1278
```

**Using environment variables:**
```bash
export MONKCLOCK_LAT=51.5074
export MONKCLOCK_LON=-0.1278
python monkclock.py
```

Your saved location is stored in `~/.config/monkclock/config`.

---

## Troubleshooting

### "Module not found" error

Make sure you've activated the virtual environment:

```bash
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### Window doesn't open (macOS)

Make sure you're using the GUI version:

```bash
python monkclock_gui.py
```

If it still doesn't work, check that you installed Python 3.13 (not 3.12 or 3.14).

### Times seem wrong

Make sure your latitude and longitude are correct. [latlong.net](https://latlong.net) is the easiest way to find them.

### "ephem" not found even after install

Try reinstalling:

```bash
pip install --upgrade ephem timezonefinder
```

---

## Example Output

### Window Mode
Opens a window with a large clock display, progress bar, and today's sun times.

### Terminal Mode
```
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

Standard Time: 2:05:23 PM
Sunrise: 6:50 AM
Sunset: 7:56 PM
Daylight: 13h 6m
Monk Day Hours: 65.5 min each
Monk Night Hours: 54.5 min each
```

### With Sundial
```
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
```

### London in Winter
```
The 10th Hour of Day
of the Day

Approximate Digital: 9 hours after sunrise

Standard Time: 1:50:28 PM
Sunrise: 8:03 AM
Sunset: 3:54 PM
Daylight: 7h 51m
Monk Day Hours: 39.3 min each
Monk Night Hours: 80.7 min each
```

Winter in London: each day hour is only 39 minutes! But each night hour is 81 minutes. The monks would have approved of long winter nights for prayer and rest.

---

## Philosophy

> "The sun does not accelerate for anyone."
> — Ancient monastic wisdom (probably)

Modern time is arbitrary: 60-minute hours, 24-hour days, timezone boundaries that cut through countries. Monk Clock reminds us that the sun doesn't negotiate.

This is a fun project, not a serious timekeeping system. Don't use it to schedule meetings unless you want confused colleagues.

---

## Dependencies

- **ephem**: Calculates sunrise and sunset times
- **rich**: Colorful terminal display
- **timezonefinder**: Converts your location to local time
- **art**: ASCII art title
- **tkinter**: Graphics for window mode (included with Python 3.13)

---

## Quick Reference

| What you want | Command |
|---------------|---------|
| Open clock window | `python monkclock_gui.py` |
| Quick time check | `python monkclock.py` |
| Live updating display | `python monkclock.py --live` |
| Live with sundial | `python monkclock.py --live --clock` |
| Set your location | `python monkclock.py --set-location LAT LON` |

*All commands run from the monkclock folder with `source venv/bin/activate` first.*

---

*"The 7th Hour of the Day, of the Day"* — Monk Clock