#!/usr/bin/env python3
"""
Monk Clock GUI - A sun-based time system
Low-CPU alternative to the Rich TUI version.

Uses GTK4 for cross-platform GUI support.
Run directly: ./monkclock_gui.py
Dependencies: ephem, timezonefinder (install with pip if needed)
"""

import datetime
import sys
import os

# Add system site-packages for GTK
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib

# Constants
DEFAULT_LAT = "37.7749"
DEFAULT_LON = "-122.4194"
UPDATE_INTERVAL = 60000  # milliseconds between updates (1 minute)


def load_config():
    """Load location from config file or environment."""
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


class MonkClockGUI(Gtk.Application):
    def __init__(self, lat, lon):
        super().__init__(application_id='com.monkclock.app')
        self.lat = lat
        self.lon = lon
        
        # Colors
        self.bg_color = Gdk.RGBA(0.1, 0.1, 0.18, 1.0)
        self.day_color = Gdk.RGBA(0.957, 0.827, 0.369, 1.0)  # warm yellow
        self.night_color = Gdk.RGBA(0.482, 0.549, 0.871, 1.0)  # soft blue
        self.text_color = Gdk.RGBA(0.918, 0.918, 0.918, 1.0)
        self.dim_color = Gdk.RGBA(0.533, 0.533, 0.533, 1.0)
        self.bar_bg = Gdk.RGBA(0.24, 0.24, 0.36, 1.0)
        
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        self.window = Gtk.ApplicationWindow(application=app, title="Monk Clock")
        self.window.set_default_size(500, 400)
        self.window.set_resizable(False)
        
        # Set dark theme
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        
        self.setup_ui()
        self.update()
        
        # Add timeout for updates
        GLib.timeout_add(UPDATE_INTERVAL, self.tick)
        
        self.window.present()
    
    def setup_ui(self):
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_valign(Gtk.Align.CENTER)
        main_box.set_halign(Gtk.Align.CENTER)
        main_box.set_margin_top(40)
        main_box.set_margin_bottom(40)
        main_box.set_margin_start(40)
        main_box.set_margin_end(40)
        self.window.set_child(main_box)
        
        # Title
        self.title_label = Gtk.Label(label="MONK CLOCK")
        self.title_label.set_css_classes(["title"])
        self.title_label.add_css_class("title-24")
        main_box.append(self.title_label)
        
        # Hour display
        hour_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        hour_box.set_halign(Gtk.Align.CENTER)
        main_box.append(hour_box)
        
        self.hour_label = Gtk.Label()
        self.hour_label.set_halign(Gtk.Align.CENTER)
        main_box.append(self.hour_label)
        
        self.period_label = Gtk.Label()
        self.period_label.set_halign(Gtk.Align.CENTER)
        main_box.append(self.period_label)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_size_request(400, 20)
        main_box.append(self.progress_bar)
        
        self.progress_label = Gtk.Label()
        self.progress_label.set_halign(Gtk.Align.CENTER)
        main_box.append(self.progress_label)
        
        # Sunrise/sunset row
        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=40)
        time_box.set_halign(Gtk.Align.CENTER)
        main_box.append(time_box)
        
        self.sunrise_label = Gtk.Label()
        self.sunrise_label.set_halign(Gtk.Align.START)
        time_box.append(self.sunrise_label)
        
        self.sunset_label = Gtk.Label()
        self.sunset_label.set_halign(Gtk.Align.END)
        time_box.append(self.sunset_label)
        
        # Standard time
        self.standard_time_label = Gtk.Label()
        self.standard_time_label.set_halign(Gtk.Align.CENTER)
        main_box.append(self.standard_time_label)
        
        # Hour length
        self.hour_len_label = Gtk.Label()
        self.hour_len_label.set_halign(Gtk.Align.CENTER)
        main_box.append(self.hour_len_label)
        
        # Apply custom CSS
        self.apply_css()
    
    def apply_css(self):
        css_provider = Gtk.CssProvider()
        css = """
            label {
                color: rgba(235, 235, 235, 1.0);
                background: none;
            }
            .title-24 {
                font-size: 24px;
                font-weight: bold;
            }
            .hour-big {
                font-size: 48px;
                font-weight: bold;
            }
        """
        css_provider.load_from_string(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def tick(self):
        self.update()
        return True  # continue timeout
    
    def update(self):
        now = datetime.datetime.now()
        sunrise_local, sunset_local = get_sun_times(self.lat, self.lon, now)
        monk_info = get_monk_time(now, sunrise_local, sunset_local)
        
        ordinal = format_ordinal(monk_info["hour"])
        period = "Day" if monk_info["period"] == "day" else "Night"
        period_hex = "#f4d35e" if monk_info["period"] == "day" else "#7b8cde"
        
        # Hour display with markup
        self.hour_label.set_markup(f'<span foreground="{period_hex}" size="46000" weight="bold">{ordinal} Hour</span>')
        self.period_label.set_markup(f'<span foreground="{period_hex}" size="14000">of the {period}</span>')
        
        # Progress bar
        self.progress_bar.set_fraction(monk_info["progress"])
        
        pct = monk_info["progress"] * 100
        self.progress_label.set_text(f"{pct:.0f}% through this hour")
        
        # Details with colors
        self.sunrise_label.set_markup(f'<span foreground="#f4d35e">↑ Sunrise: {sunrise_local.strftime("%_I:%M %p")}</span>')
        self.sunset_label.set_markup(f'<span foreground="#e07040">↓ Sunset:  {sunset_local.strftime("%_I:%M %p")}</span>')
        self.standard_time_label.set_text(f"Standard: {now.strftime('%-I:%M:%S %p')}")
        
        hour_len = monk_info["hour_length_seconds"] / 60
        self.hour_len_label.set_text(f"This hour: {hour_len:.1f} min  |  {self.lat}, {self.lon}")


def main():
    lat, lon = load_config()
    if os.environ.get("MONKCLOCK_LAT"):
        lat = os.environ.get("MONKCLOCK_LAT", lat)
    if os.environ.get("MONKCLOCK_LON"):
        lon = os.environ.get("MONKCLOCK_LON", lon)
    
    app = MonkClockGUI(lat, lon)
    app.run(None)


if __name__ == "__main__":
    main()