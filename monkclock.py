#!/usr/bin/env python3
"""
Monk Clock - A sun-based time system

Divides daylight and nighttime each into 12 equal hours.
During winter, night hours are longer; in summer, they are shorter.
"""

import datetime
import math
import sys
import os

try:
    import ephem
except ImportError:
    print("This script requires the 'ephem' library.")
    print("Install with: pip install ephem")
    sys.exit(1)

try:
    from timezonefinder import TimezoneFinder
    tf = TimezoneFinder()
except ImportError:
    print("This script requires the 'timezonefinder' library.")
    print("Install with: pip install timezonefinder")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich.live import Live
except ImportError:
    print("This script requires the 'rich' library.")
    print("Install with: pip install rich")
    sys.exit(1)

try:
    from art import text2art
except ImportError:
    text2art = None

# Default location (San Francisco)
DEFAULT_LAT = "37.7749"
DEFAULT_LON = "-122.4194"


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
    
    # Fall back to environment or default
    lat = os.environ.get("MONKCLOCK_LAT", DEFAULT_LAT)
    lon = os.environ.get("MONKCLOCK_LON", DEFAULT_LON)
    return lat, lon


def save_config(lat, lon):
    """Save location to config file."""
    config_dir = os.path.expanduser("~/.config/monkclock")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config")
    with open(config_path, "w") as f:
        f.write(f"latitude={lat}\n")
        f.write(f"longitude={lon}\n")
    print(f"Saved location: {lat}, {lon}")


def get_sun_times(lat, lon, date=None):
    """
    Calculate sunrise and sunset times for a given location.
    Returns local datetimes based on the location's timezone.
    """
    if date is None:
        date = datetime.datetime.now()
    
    obs = ephem.Observer()
    obs.lat = lat
    obs.lon = lon
    obs.horizon = '0'
    
    # Get timezone for this location
    try:
        import zoneinfo
        tz_name = tf.timezone_at(lat=float(lat), lng=float(lon))
        if tz_name:
            target_tz = zoneinfo.ZoneInfo(tz_name)
        else:
            target_tz = datetime.timezone.utc
    except:
        target_tz = datetime.timezone.utc
    
    # Search from noon yesterday to find today's sunrise
    obs.date = (date.replace(hour=12) - datetime.timedelta(days=1)).strftime("%Y/%m/%d 12:00:00")
    
    # Find sunrise
    sr_raw = obs.next_rising(ephem.Sun(), start=obs.date)
    sr_utc = sr_raw.datetime().replace(tzinfo=datetime.timezone.utc)
    sunrise_local = sr_utc.astimezone(target_tz)
    
    # Find sunset after sunrise
    obs.date = sr_raw
    ss_raw = obs.next_setting(ephem.Sun(), start=obs.date)
    ss_utc = ss_raw.datetime().replace(tzinfo=datetime.timezone.utc)
    sunset_local = ss_utc.astimezone(target_tz)
    
    return sunrise_local, sunset_local


def get_monk_time(now, sunrise, sunset):
    """
    Calculate the current monk hour using LOCAL times.
    
    Simple logic:
    - If now is between sunrise and sunset -> it's day
    - Otherwise -> it's night
    
    All datetimes should be in the same local timezone.
    """
    # Make sure everything is naive for comparison
    if hasattr(now, 'tzinfo') and now.tzinfo:
        now = now.replace(tzinfo=None)
    if hasattr(sunrise, 'tzinfo') and sunrise.tzinfo:
        sunrise = sunrise.replace(tzinfo=None)
    if hasattr(sunset, 'tzinfo') and sunset.tzinfo:
        sunset = sunset.replace(tzinfo=None)
    
    # Calculate day and night durations
    day_seconds = (sunset - sunrise).total_seconds()
    night_seconds = 86400 - day_seconds
    day_hour_seconds = day_seconds / 12
    night_hour_seconds = night_seconds / 12
    
    if sunrise <= now <= sunset:
        # Daytime
        seconds_since_sunrise = (now - sunrise).total_seconds()
        hour_number = int(seconds_since_sunrise / day_hour_seconds) + 1
        hour_number = min(hour_number, 12)
        progress = (seconds_since_sunrise % day_hour_seconds) / day_hour_seconds
        hour_seconds = day_hour_seconds
    else:
        # Nighttime
        if now >= sunset:
            seconds_since_sunset = (now - sunset).total_seconds()
        else:
            # Past midnight, before today's sunrise
            seconds_since_sunset = (now + datetime.timedelta(days=1) - sunset).total_seconds()
        hour_number = int(seconds_since_sunset / night_hour_seconds) + 1
        hour_number = min(hour_number, 12)
        progress = (seconds_since_sunset % night_hour_seconds) / night_hour_seconds
        hour_seconds = night_hour_seconds
    
    return {
        "period": "day" if sunrise <= now <= sunset else "night",
        "hour": hour_number,
        "progress": progress,
        "hour_length_seconds": hour_seconds
    }


def format_ordinal(n):
    """Return ordinal string (1st, 2nd, 3rd, etc.)"""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def get_approx_digital(monk_info):
    """
    Get monk time as hours after sunrise (day) or after sunset (night).
    """
    hour = monk_info["hour"]
    progress = monk_info["progress"]
    total_hours = (hour - 1) + progress
    
    if total_hours == int(total_hours):
        total_str = f"{int(total_hours)}"
    else:
        frac = total_hours - int(total_hours)
        frac_str = ""
        if frac < 0.125:
            frac_str = ""
        elif frac < 0.25:
            frac_str = "⅛"
        elif frac < 0.375:
            frac_str = "¼"
        elif frac < 0.5:
            frac_str = "⅜"
        elif frac < 0.625:
            frac_str = "½"
        elif frac < 0.75:
            frac_str = "⅝"
        elif frac < 0.875:
            frac_str = "¾"
        else:
            frac_str = "⅞"
        total_str = f"{int(total_hours)}{frac_str}"
    
    if monk_info["period"] == "night":
        return f"{total_str} hours after sunset"
    else:
        return f"{total_str} hours after sunrise"


def format_time(dt):
    """Format a datetime for display."""
    return dt.strftime("%-I:%M %p")


def get_splash_art():
    """Generate ASCII art for MONK CLOCK."""
    if text2art:
        try:
            monk = text2art("MONK", font="smslant")
            clock = text2art("CLOCK", font="smslant")
            return f"\n{monk}{clock}\n"
        except:
            pass
    return ""


def draw_analog_clock(monk_info):
    """
    Draw an ASCII sundial showing the current monk hour.
    """
    hour = monk_info["hour"]
    progress = monk_info["progress"]
    
    r = 10
    cx, cy = r + 1, r + 1
    width = (r + 1) * 2 + 2
    height = (r + 1) * 2 + 2
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    roman = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
             7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"}
    
    def get_hour_pos(h):
        angle = (h - 3) * 30
        rad = math.radians(angle)
        return (cx + r * math.cos(rad), cy + r * math.sin(rad))
    
    hour_positions = {h: get_hour_pos(h) for h in range(1, 13)}
    
    # Draw outer circle
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        px = cx + r * math.cos(rad)
        py = cy + r * math.sin(rad)
        ix, iy = int(round(px)), int(round(py))
        if 0 <= iy < height and 0 <= ix < width:
            if grid[iy][ix] == " ":
                grid[iy][ix] = "·"
    
    # Draw hour numbers
    for h, (hx, hy) in hour_positions.items():
        ix, iy = int(round(hx)), int(round(hy))
        if 0 <= iy < height and 0 <= ix < width:
            grid[iy][ix] = roman[h]
    
    # Draw gnomon
    for i in range(r - 2):
        iy = cy - 1 - i
        if 0 <= iy < height:
            grid[iy][cx] = "│"
    if 0 <= cy - r - 1 < height:
        grid[cy - r - 1][cx] = "^"
    if 0 <= cy < height:
        grid[cy][cx - 1] = "╰"
        grid[cy][cx + 1] = "╯"
    
    # Draw shadow
    shadow_clock_pos = hour + progress
    base_hour = int(shadow_clock_pos) % 12
    if base_hour == 0:
        base_hour = 12
    next_hour = base_hour % 12 + 1
    if next_hour == 0:
        next_hour = 12
    
    frac = shadow_clock_pos % 1
    start_pos = hour_positions[base_hour]
    end_pos = hour_positions[next_hour]
    shadow_x = start_pos[0] + (end_pos[0] - start_pos[0]) * frac
    shadow_y = start_pos[1] + (end_pos[1] - start_pos[1]) * frac
    
    for i in range(r - 1):
        t = i / (r - 2)
        shad_x = cx + (shadow_x - cx) * t
        shad_y = cy + (shadow_y - cy) * t
        width_half = int(1 + t * 1.5)
        for dx in range(-width_half, width_half + 1):
            ix = int(shad_x + dx)
            iy = int(shad_y)
            if 0 <= iy < height and 0 <= ix < width:
                if grid[iy][ix] == " ":
                    grid[iy][ix] = "▒"
    
    if 0 <= cy < height and 0 <= cx < width:
        grid[cy][cx] = "*"
    
    lines = []
    for row in grid:
        lines.append("".join(row).rstrip())
    lines.append("")
    
    period_str = monk_info["period"].upper()
    ordinal = format_ordinal(hour)
    lines.append(f" ═══ {period_str} ═══")
    lines.append(f"   {ordinal} Hour")
    lines.append(f"  {get_approx_digital(monk_info)}")
    
    return "\n".join(lines)


def create_display(lat, lon, console, show_clock=False):
    """Create the display content."""
    now = datetime.datetime.now()
    sunrise_local, sunset_local = get_sun_times(lat, lon, now)
    monk_info = get_monk_time(now, sunrise_local, sunset_local)
    
    # Calculate daylight duration
    day_seconds = (sunset_local - sunrise_local).total_seconds()
    night_seconds = 86400 - day_seconds
    day_hour_min = day_seconds / 12 / 60
    night_hour_min = night_seconds / 12 / 60
    daylight_h = int(day_seconds / 3600)
    daylight_m = int((day_seconds % 3600) / 60)
    
    period_name = "Day" if monk_info["period"] == "day" else "Night"
    ordinal = format_ordinal(monk_info["hour"])
    
    main_time = Text()
    main_time.append(f"The {ordinal} Hour of {period_name}\n", style="bold white")
    main_time.append(f"of the {period_name}\n\n", style="dim")
    main_time.append(f"Approximate Digital: {get_approx_digital(monk_info)}", style="cyan")
    
    bar_width = 30
    filled = int(bar_width * monk_info["progress"])
    bar = "█" * filled + "░" * (bar_width - filled)
    progress_text = Text(f"\nProgress: [{bar}] {monk_info['progress']*100:.0f}%", style="white")
    
    details = Text()
    hour_len = monk_info["hour_length_seconds"] / 60
    details.append(f"Standard Time: {now.strftime('%-I:%M:%S %p')}\n", style="yellow")
    details.append(f"Sunrise: {format_time(sunrise_local)}\n")
    details.append(f"Sunset: {format_time(sunset_local)}\n")
    details.append(f"Daylight: {daylight_h}h {daylight_m}m\n")
    details.append(f"\nMonk Day Hours: {day_hour_min:.1f} min each\n", style="green")
    details.append(f"Monk Night Hours: {night_hour_min:.1f} min each\n", style="blue")
    details.append(f"\nThis hour: {hour_len:.1f} min\n", style="dim")
    details.append(f"Location: {lat}, {lon}", style="dim")
    
    return main_time, progress_text, details, monk_info, show_clock and draw_analog_clock(monk_info)


def run_live(console, lat, lon, show_clock=False):
    """Run the live display."""
    with Live(console=console, screen=True, refresh_per_second=1) as live:
        while True:
            main_time, progress_text, details, monk_info, clock_str = create_display(lat, lon, console, show_clock)
            
            now = datetime.datetime.now()
            ordinal = format_ordinal(monk_info["hour"])
            period = "Day" if monk_info["period"] == "day" else "Night"
            
            if show_clock and clock_str:
                layout = Layout(name="root")
                
                header_text = Text()
                header_text.append("M O N K   C L O C K", style="bold magenta")
                header_text.append("\n")
                header_text.append("Sun-based time for the modern monk", style="dim magenta")
                header_panel = Panel(header_text, border_style="magenta")
                
                clock_lines = clock_str.split("\n")
                clock_text = Text()
                for i, line in enumerate(clock_lines):
                    if i > 0:
                        clock_text.append("\n")
                    clock_text.append(line)
                clock_panel = Panel(clock_text, border_style="magenta")
                
                info_text = Text()
                info_text.append(f"The {ordinal} Hour of {period}\n", style="bold white")
                info_text.append(f"of the {period}\n\n", style="dim")
                info_text.append(f"{get_approx_digital(monk_info)}\n", style="cyan bold")
                info_text.append(f"{progress_text}\n\n", style="white")
                info_text.append(details)
                
                info_panel = Panel(info_text, title=f"{period} Hours",
                                  border_style="green" if monk_info["period"] == "day" else "blue")
                
                layout.split_column(
                    Layout(header_panel, name="header", ratio=1),
                    Layout(name="body", ratio=4),
                )
                layout["body"].split_row(
                    Layout(clock_panel, name="clock"),
                    Layout(info_panel, name="info"),
                )
            else:
                layout = Layout(name="root")
                layout.split_column(
                    Layout(name="header"),
                    Layout(name="main"),
                    Layout(name="footer"),
                )
                
                header_text = Text()
                header_text.append("M O N K   C L O C K", style="bold magenta")
                header_text.append("\n")
                header_text.append("Sun-based time for the modern monk", style="dim magenta")
                layout["header"].update(Panel(header_text, border_style="magenta"))
                layout["main"].update(Panel(
                    main_time + progress_text,
                    title=f"{period} Hours",
                    border_style="green" if monk_info["period"] == "day" else "blue"
                ))
                layout["footer"].update(Panel(details, title="Details", border_style="white"))
            
            live.update(layout)


def run_once(console, lat, lon, show_clock=False):
    """Run once and print the time."""
    main_time, progress_text, details, monk_info, clock_str = create_display(lat, lon, console, show_clock)
    
    now = datetime.datetime.now()
    sunrise_local, sunset_local = get_sun_times(lat, lon, now)
    monk_info = get_monk_time(now, sunrise_local, sunset_local)
    
    period_name = "Day" if monk_info["period"] == "day" else "Night"
    ordinal = format_ordinal(monk_info["hour"])
    hour_len = monk_info["hour_length_seconds"] / 60
    
    day_seconds = (sunset_local - sunrise_local).total_seconds()
    night_seconds = 86400 - day_seconds
    day_hour_min = day_seconds / 12 / 60
    night_hour_min = night_seconds / 12 / 60
    daylight_h = int(day_seconds / 3600)
    daylight_m = int((day_seconds % 3600) / 60)
    
    console.print()
    
    if show_clock and clock_str:
        clock_lines = clock_str.split("\n")
        console.print(f"[bold white]The {ordinal} Hour of {period_name}[/bold white]")
        console.print(f"[dim]of the {period_name}[/dim]")
        console.print()
        console.print(f"[cyan]{get_approx_digital(monk_info)}[/cyan]")
        console.print()
        for line in clock_lines:
            console.print(f"  {line}")
        console.print()
        console.print(f"[yellow]Standard:[/yellow] {now.strftime('%-I:%M:%S %p')}")
        console.print(f"Sunrise: {format_time(sunrise_local)}")
        console.print(f"Sunset: {format_time(sunset_local)}")
        console.print(f"Daylight: {daylight_h}h {daylight_m}m")
        console.print(f"[green]Monk Day Hrs:[/green] {day_hour_min:.1f} min")
        console.print(f"[blue]Monk Night Hrs:[/blue] {night_hour_min:.1f} min")
        console.print(f"[dim]This hr: {hour_len:.1f} min | {lat}, {lon}[/dim]")
    else:
        console.print(f"[bold white]The {ordinal} Hour of {period_name}[/bold white]")
        console.print(f"[dim]of the {period_name}[/dim]")
        console.print()
        console.print(f"[cyan]Approximate Digital:[/cyan] {get_approx_digital(monk_info)}")
        console.print()
        console.print(f"[yellow]Standard Time:[/yellow] {now.strftime('%-I:%M:%S %p')}")
        console.print(f"Sunrise: {format_time(sunrise_local)}")
        console.print(f"Sunset: {format_time(sunset_local)}")
        console.print(f"Daylight: {daylight_h}h {daylight_m}m")
        console.print(f"[green]Monk Day Hours:[/green] {day_hour_min:.1f} min each")
        console.print(f"[blue]Monk Night Hours:[/blue] {night_hour_min:.1f} min each")
        console.print(f"This hour: {hour_len:.1f} min")
        console.print()
        console.print(f"[dim]Location: {lat}, {lon}[/dim]")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monk Clock - A sun-based time system")
    parser.add_argument("--live", "-l", action="store_true", help="Run live display")
    parser.add_argument("--clock", "-c", action="store_true", help="Show ASCII sundial")
    parser.add_argument("--lat", help="Latitude")
    parser.add_argument("--lon", help="Longitude")
    parser.add_argument("--set-location", nargs=2, metavar=("LAT", "LON"),
                        help="Save location to config file")
    
    args = parser.parse_args()
    
    if args.set_location:
        lat, lon = args.set_location
        save_config(lat, lon)
        return
    
    lat, lon = load_config()
    if args.lat:
        lat = args.lat
    if args.lon:
        lon = args.lon
    
    console = Console()
    
    splash = get_splash_art()
    if splash:
        console.print(splash, style="bold magenta")
    
    if args.live:
        run_live(console, lat, lon, args.clock)
    else:
        run_once(console, lat, lon, args.clock)


if __name__ == "__main__":
    main()
