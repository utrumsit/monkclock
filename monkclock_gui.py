#!/opt/homebrew/bin/python3.13
"""
Monk Clock GUI - A sun-based time system
Low-CPU alternative to the Rich TUI version.

Requires: Python 3.13 (has tkinter built-in; 3.14 does not)
Run directly: ./monkclock_gui.py
Dependencies: ephem, timezonefinder (install with pip if needed)
"""

import datetime
import math
import tkinter as tk
from tkinter import font as tkfont

# Constants
DEFAULT_LAT = "37.7749"
DEFAULT_LON = "-122.4194"
UPDATE_INTERVAL = 60000  # milliseconds between updates (1 minute)


def load_config():
    """Load location from config file or environment."""
    import os
    config_path = os.path.expanduser("~/.config/monkclock/config")
    
    if os.path.exists(config_path):
        lat = lon = None
        with open(config_path) as f:
            for line in f:
                if line.startswith("latitude="):
                    lat = line.split("=", 1)[1].strip()
                elif line.startswith("longitude="):
                    lon = line.split("=", 1)[1].strip()
        if lat and lon:
            return lat, lon
    
    lat = os.environ.get("MONKCLOCK_LAT", DEFAULT_LAT)
    lon = os.environ.get("MONKCLOCK_LON", DEFAULT_LON)
    return lat, lon


def get_sun_times(lat, lon, date=None):
    """Calculate sunrise and sunset times."""
    import ephem
    import zoneinfo
    
    if date is None:
        date = datetime.datetime.now()
    
    obs = ephem.Observer()
    obs.lat = lat
    obs.lon = lon
    obs.horizon = '0'
    
    # Get timezone
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=float(lat), lng=float(lon))
        if tz_name:
            target_tz = zoneinfo.ZoneInfo(tz_name)
        else:
            target_tz = datetime.timezone.utc
    except:
        target_tz = datetime.timezone.utc
    
    # Find sunrise
    obs.date = (date.replace(hour=12) - datetime.timedelta(days=1)).strftime("%Y/%m/%d 12:00:00")
    sr_raw = obs.next_rising(ephem.Sun(), start=obs.date)
    sr_utc = sr_raw.datetime().replace(tzinfo=datetime.timezone.utc)
    sunrise_local = sr_utc.astimezone(target_tz)
    
    # Find sunset
    obs.date = sr_raw
    ss_raw = obs.next_setting(ephem.Sun(), start=obs.date)
    ss_utc = ss_raw.datetime().replace(tzinfo=datetime.timezone.utc)
    sunset_local = ss_utc.astimezone(target_tz)
    
    return sunrise_local, sunset_local


def get_monk_time(now, sunrise, sunset):
    """Calculate current monk hour."""
    # Make naive for comparison
    if hasattr(now, 'tzinfo') and now.tzinfo:
        now = now.replace(tzinfo=None)
    if hasattr(sunrise, 'tzinfo') and sunrise.tzinfo:
        sunrise = sunrise.replace(tzinfo=None)
    if hasattr(sunset, 'tzinfo') and sunset.tzinfo:
        sunset = sunset.replace(tzinfo=None)
    
    day_seconds = (sunset - sunrise).total_seconds()
    night_seconds = 86400 - day_seconds
    day_hour_seconds = day_seconds / 12
    night_hour_seconds = night_seconds / 12
    
    if sunrise <= now <= sunset:
        seconds_since_sunrise = (now - sunrise).total_seconds()
        hour_number = min(int(seconds_since_sunrise / day_hour_seconds) + 1, 12)
        progress = (seconds_since_sunrise % day_hour_seconds) / day_hour_seconds
        hour_seconds = day_hour_seconds
        period = "day"
    else:
        if now >= sunset:
            seconds_since_sunset = (now - sunset).total_seconds()
        else:
            seconds_since_sunset = (now + datetime.timedelta(days=1) - sunset).total_seconds()
        hour_number = min(int(seconds_since_sunset / night_hour_seconds) + 1, 12)
        progress = (seconds_since_sunset % night_hour_seconds) / night_hour_seconds
        hour_seconds = night_hour_seconds
        period = "night"
    
    return {
        "period": period,
        "hour": hour_number,
        "progress": progress,
        "hour_length_seconds": hour_seconds
    }


def format_ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


class MonkClockGUI:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.root = tk.Tk()
        self.root.title("Monk Clock")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)
        
        # Colors
        self.bg_color = "#1a1a2e"
        self.day_color = "#f4d35e"      # warm yellow for day
        self.night_color = "#7b8cde"     # soft blue for night
        self.text_color = "#eaeaea"
        self.dim_color = "#888888"
        self.bar_bg = "#3d3d5c"
        
        self.setup_fonts()
        self.setup_widgets()
        self.update()
        self.root.after(UPDATE_INTERVAL, self.tick)
    
    def setup_fonts(self):
        self.title_font = tkfont.Font(family="Helvetica", size=24, weight="bold")
        self.hour_font = tkfont.Font(family="Helvetica", size=48, weight="bold")
        self.label_font = tkfont.Font(family="Helvetica", size=14)
        self.detail_font = tkfont.Font(family="Menlo", size=12)
    
    def setup_widgets(self):
        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.bg_color, padx=40, pady=30)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        self.title_label = tk.Label(
            self.main_frame, text="MONK CLOCK",
            font=self.title_font, fg=self.day_color, bg=self.bg_color
        )
        self.title_label.pack(pady=(0, 20))
        
        # Hour display
        self.hour_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.hour_frame.pack(pady=10)
        
        self.hour_label = tk.Label(
            self.hour_frame, text="",
            font=self.hour_font, fg=self.text_color, bg=self.bg_color
        )
        self.hour_label.pack()
        
        self.period_label = tk.Label(
            self.hour_frame, text="",
            font=self.label_font, fg=self.dim_color, bg=self.bg_color
        )
        self.period_label.pack()
        
        # Progress bar
        self.progress_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.progress_frame.pack(pady=20, fill=tk.X, padx=20)
        
        self.progress_bar = tk.Canvas(
            self.progress_frame, width=400, height=20,
            bg=self.bar_bg, highlightthickness=0
        )
        self.progress_bar.pack()
        self.progress_rect = None
        
        self.progress_label = tk.Label(
            self.progress_frame, text="",
            font=self.label_font, fg=self.dim_color, bg=self.bg_color
        )
        self.progress_label.pack(pady=(5, 0))
        
        # Details frame
        self.details_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.details_frame.pack(pady=20, fill=tk.X)
        
        self.left_frame = tk.Frame(self.details_frame, bg=self.bg_color)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = tk.Frame(self.details_frame, bg=self.bg_color)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.sunrise_label = tk.Label(
            self.left_frame, text="", font=self.detail_font,
            fg=self.day_color, bg=self.bg_color, anchor="w"
        )
        self.sunrise_label.pack(pady=3, fill=tk.X)
        
        self.sunset_label = tk.Label(
            self.right_frame, text="", font=self.detail_font,
            fg="#e07040", bg=self.bg_color, anchor="w"
        )
        self.sunset_label.pack(pady=3, fill=tk.X)
        
        self.standard_time_label = tk.Label(
            self.main_frame, text="", font=self.detail_font,
            fg=self.dim_color, bg=self.bg_color
        )
        self.standard_time_label.pack(pady=(10, 0))
        
        self.hour_len_label = tk.Label(
            self.main_frame, text="", font=self.detail_font,
            fg=self.dim_color, bg=self.bg_color
        )
        self.hour_len_label.pack()
    
    def tick(self):
        self.update()
        self.root.after(UPDATE_INTERVAL, self.tick)
    
    def update(self):
        now = datetime.datetime.now()
        sunrise_local, sunset_local = get_sun_times(self.lat, self.lon, now)
        monk_info = get_monk_time(now, sunrise_local, sunset_local)
        
        ordinal = format_ordinal(monk_info["hour"])
        period = "Day" if monk_info["period"] == "day" else "Night"
        period_color = self.day_color if monk_info["period"] == "day" else self.night_color
        
        # Update colors based on period
        self.hour_label.config(fg=period_color)
        self.title_label.config(fg=period_color)
        
        # Hour display
        self.hour_label.config(text=f"{ordinal} Hour")
        self.period_label.config(text=f"of the {period}", fg=period_color)
        
        # Progress bar
        self.progress_bar.delete("all")
        bar_width = 400
        bar_height = 20
        filled = int(bar_width * monk_info["progress"])
        
        self.progress_bar.create_rectangle(
            0, 0, filled, bar_height,
            fill=period_color, outline=""
        )
        
        pct = monk_info["progress"] * 100
        self.progress_label.config(text=f"{pct:.0f}% through this hour")
        
        # Details
        self.sunrise_label.config(text=f"↑ Sunrise: {sunrise_local.strftime('%-I:%M %p')}")
        self.sunset_label.config(text=f"↓ Sunset:  {sunset_local.strftime('%-I:%M %p')}")
        self.standard_time_label.config(text=f"Standard: {now.strftime('%-I:%M:%S %p')}")
        
        hour_len = monk_info["hour_length_seconds"] / 60
        self.hour_len_label.config(
            text=f"This hour: {hour_len:.1f} min  |  {self.lat}, {self.lon}"
        )


def main():
    lat, lon = load_config()
    import os
    if os.environ.get("MONKCLOCK_LAT"):
        lat = os.environ.get("MONKCLOCK_LAT", lat)
    if os.environ.get("MONKCLOCK_LON"):
        lon = os.environ.get("MONKCLOCK_LON", lon)
    
    app = MonkClockGUI(lat, lon)
    app.root.mainloop()


if __name__ == "__main__":
    main()