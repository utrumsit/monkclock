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
    Calculate sunrise and sunset times for a given location and date.
    Returns naive UTC datetimes for consistent calculations.
    """
    if date is None:
        date_local = datetime.datetime.now()
    else:
        date_local = date
    
    date_utc = date_local.astimezone(datetime.timezone.utc)
    
    obs = ephem.Observer()
    obs.lat = lat
    obs.lon = lon
    obs.horizon = '0'  # Standard horizon
    
    # Find sunrise: search from midnight today (UTC)
    midnight_utc = date_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    obs.date = midnight_utc.strftime("%Y/%m/%d 00:00:00")
    
    sr_raw = obs.next_rising(ephem.Sun(), start=obs.date)
    sunrise_dt = sr_raw.datetime()  # Get datetime from ephem
    
    # Find sunset: search from the sunrise we found
    obs.date = sr_raw
    ss_raw = obs.next_setting(ephem.Sun(), start=obs.date)
    sunset_dt = ss_raw.datetime()  # Get datetime from ephem
    
    # Check if sunset is before sunrise (date edge case)
    if sunset_dt < sunrise_dt:
        # Sunset is tomorrow morning, we need today's sunset
        # This happens near the summer solstice at high latitudes
        obs.date = midnight_utc.strftime("%Y/%m/%d 12:00:00")
        ss_raw = obs.next_setting(ephem.Sun(), start=obs.date)
        sunset_dt = ss_raw.datetime()
    
    # Return as naive UTC datetimes (ephem already gives us UTC)
    return sunrise_dt, sunset_dt


def get_display_times(sunrise_utc, sunset_utc, lat, lon):
    """Convert UTC times to the target location's local timezone."""
    # Get the timezone for this location
    try:
        tz_name = tf.timezone_at(lat=float(lat), lng=float(lon))
        if tz_name:
            import zoneinfo
            target_tz = zoneinfo.ZoneInfo(tz_name)
        else:
            target_tz = None
    except Exception:
        target_tz = None
    
    # These are naive UTC datetimes from ephem
    sunrise_aware = sunrise_utc.replace(tzinfo=datetime.timezone.utc)
    sunset_aware = sunset_utc.replace(tzinfo=datetime.timezone.utc)
    
    if target_tz:
        sunrise_local = sunrise_aware.astimezone(target_tz)
        sunset_local = sunset_aware.astimezone(target_tz)
    else:
        sunrise_local = sunrise_aware.astimezone()
        sunset_local = sunset_aware.astimezone()
    
    return sunrise_local, sunset_local


def get_monk_time(now, sunrise, sunset):
    """
    Calculate the current monk hour.
    
    Args:
        now: datetime (naive or aware, assumed local)
        sunrise: sunrise time (local, naive)
        sunset: sunset time (local, naive)
    
    Returns:
        dict with:
        - period: "day" or "night"
        - hour: 1-12
        - progress: 0.0 to 1.0 within current hour
        - hour_start: datetime when current hour began
        - hour_end: datetime when current hour ends
    """
    # Normalize to naive datetimes for comparison
    if hasattr(sunrise, 'tzinfo') and sunrise.tzinfo:
        sunrise = sunrise.replace(tzinfo=None)
    if hasattr(sunset, 'tzinfo') and sunset.tzinfo:
        sunset = sunset.replace(tzinfo=None)
    if hasattr(now, 'tzinfo') and now.tzinfo:
        now = now.replace(tzinfo=None)
    
    # Normalize to same day for comparison
    today = now.date()
    sunrise_today = sunrise.replace(year=today.year, month=today.month, day=today.day)
    sunset_today = sunset.replace(year=today.year, month=today.month, day=today.day)
    
    # Handle crossing
    if sunset_today <= sunrise_today:
        sunset_today += datetime.timedelta(days=1)
    if sunrise_today > now:
        sunrise_today -= datetime.timedelta(days=1)
    
    day_seconds = (sunset_today - sunrise_today).total_seconds()
    night_seconds = 86400 - day_seconds
    
    day_hour_seconds = day_seconds / 12
    night_hour_seconds = night_seconds / 12
    
    if sunrise_today <= now < sunset_today:
        # Daytime
        seconds_since_sunrise = (now - sunrise_today).total_seconds()
        hour_number = int(seconds_since_sunrise / day_hour_seconds) + 1
        hour_number = min(hour_number, 12)
        progress = (seconds_since_sunrise % day_hour_seconds) / day_hour_seconds
        
        hour_start = sunrise_today + datetime.timedelta(seconds=(hour_number - 1) * day_hour_seconds)
        hour_end = hour_start + datetime.timedelta(seconds=day_hour_seconds)
        
        return {
            "period": "day",
            "hour": hour_number,
            "progress": progress,
            "hour_start": hour_start,
            "hour_end": hour_end,
            "hour_length_seconds": day_hour_seconds
        }
    else:
        # Nighttime
        if now >= sunset_today:
            seconds_since_sunset = (now - sunset_today).total_seconds()
        else:
            seconds_since_sunset = (now + datetime.timedelta(days=1) - sunset_today).total_seconds()
        
        hour_number = int(seconds_since_sunset / night_hour_seconds) + 1
        hour_number = min(hour_number, 12)
        progress = (seconds_since_sunset % night_hour_seconds) / night_hour_seconds
        
        hour_start = sunset_today + datetime.timedelta(seconds=(hour_number - 1) * night_hour_seconds)
        hour_end = hour_start + datetime.timedelta(seconds=night_hour_seconds)
        
        return {
            "period": "night",
            "hour": hour_number,
            "progress": progress,
            "hour_start": hour_start,
            "hour_end": hour_end,
            "hour_length_seconds": night_hour_seconds
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
    Get monk time as hours after sunrise.
    
    Shows how many monk hours have passed since sunrise,
    with the fraction showing progress through the current hour.
    e.g., "7.9 hours after sunrise" = 7 complete hours + 90% of current hour
    """
    hour = monk_info["hour"]
    progress = monk_info["progress"]
    
    # Total hours after sunrise (in monk hours, which may be != 60 min)
    total_hours = (hour - 1) + progress
    
    # Format nicely
    if total_hours == int(total_hours):
        return f"{int(total_hours)} hours after sunrise"
    else:
        # Show fraction
        frac = total_hours - int(total_hours)
        # Convert to common fractions
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
        
        if frac_str:
            return f"{int(total_hours)}{frac_str} hours after sunrise"
        else:
            return f"{total_hours:.1f} hours after sunrise"


def get_approx_digital_simple(monk_info):
    """
    Simple monk digital time: hours after sunrise as a decimal.
    """
    total_hours = (monk_info["hour"] - 1) + monk_info["progress"]
    return f"{total_hours:.2f}h after sunrise"


def get_daylight_duration(sunrise, sunset):
    """Return daylight duration as hours and minutes."""
    delta = sunset - sunrise
    hours = int(delta.total_seconds() / 3600)
    minutes = int((delta.total_seconds() % 3600) / 60)
    return hours, minutes


def draw_analog_clock(monk_info):
    """
    Draw an ASCII sundial showing the current monk hour.
    
    A horizontal sundial with:
    - Roman numeral hour marks
    - A gnomon (style) casting a shadow
    - The shadow points to the current hour position
    """
    hour = monk_info["hour"]
    progress = monk_info["progress"]
    period = monk_info["period"]
    
    # Sundial dimensions
    r = 10
    cx, cy = r + 1, r + 1
    
    # Build the grid
    width = (r + 1) * 2 + 2
    height = (r + 1) * 2 + 2
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Roman numerals
    roman = {
        1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
        7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII'
    }
    
    # Hour positions on the sundial
    # 12 at top (y=1), hours go clockwise
    def get_hour_pos(h):
        angle = (h - 3) * 30  # 12 at top
        rad = math.radians(angle)
        return (cx + r * math.cos(rad), cy + r * math.sin(rad))
    
    hour_positions = {h: get_hour_pos(h) for h in range(1, 13)}
    
    # Draw the outer circle (dial edge)
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        px = cx + r * math.cos(rad)
        py = cy + r * math.sin(rad)
        ix, iy = int(round(px)), int(round(py))
        if 0 <= iy < height and 0 <= ix < width:
            if grid[iy][ix] == ' ':
                grid[iy][ix] = '·'
    
    # Draw hour numbers
    for h, (hx, hy) in hour_positions.items():
        ix, iy = int(round(hx)), int(round(hy))
        if 0 <= iy < height and 0 <= ix < width:
            grid[iy][ix] = roman[h]
    
    # Draw the gnomon (style) - vertical pointer at center
    # Top half (above center, pointing up)
    for i in range(r - 2):
        iy = cy - 1 - i
        if 0 <= iy < height:
            grid[iy][cx] = '│'
    
    # Gnomon tip
    if 0 <= cy - r - 1 < height:
        grid[cy - r - 1][cx] = '^'
    
    # Gnomon base (at center)
    if 0 <= cy < height:
        grid[cy][cx - 1] = '╰'
        grid[cy][cx + 1] = '╯'
    
    # Draw the shadow - it points to hour + progress
    # At start of hour N, shadow at hour N
    # At end of hour N (just before N+1), shadow at hour N+1
    
    # Shadow position = hour + progress
    # e.g., 9th hour, 0.5 progress = shadow at 9.5 (between IX and X)
    shadow_clock_pos = hour + progress
    
    # Interpolate between hour positions
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
    
    # Draw shadow from gnomon base outward
    # The shadow is a triangle growing wider
    for i in range(r - 1):
        t = i / (r - 2)  # 0 at center, 1 at edge
        shad_x = cx + (shadow_x - cx) * t
        shad_y = cy + (shadow_y - cy) * t
        
        # Shadow width increases with distance
        width_half = int(1 + t * 1.5)
        for dx in range(-width_half, width_half + 1):
            ix = int(shad_x + dx)
            iy = int(shad_y)
            if 0 <= iy < height and 0 <= ix < width:
                if grid[iy][ix] == ' ':
                    grid[iy][ix] = '▒'
    
    # Draw center point
    if 0 <= cy < height and 0 <= cx < width:
        grid[cy][cx] = '*'
    
    # Build output
    lines = []
    for row in grid:
        line = ''.join(row)
        lines.append(line.rstrip())
    
    # Add info below
    lines.append('')
    
    period_str = period.upper()
    ordinal = format_ordinal(hour)
    
    lines.append(f" ═══ {period_str} ═══")
    lines.append(f"   {ordinal} Hour")
    lines.append(f"  {get_approx_digital(monk_info)}")
    
    return '\n'.join(lines)


from art import text2art


def get_splash_art():
    """Generate ASCII art for MONK CLOCK."""
    try:
        monk = text2art("MONK", font='smslant')
        clock = text2art("CLOCK", font='smslant')
    except:
        return """\nMONK
CLOCK
"""
    return f"\n{monk}{clock}\n"
    """
    Draw a mini analog clock (16 characters wide).
    """
    hour = monk_info["hour"]
    progress = monk_info["progress"]
    
    # Clock face
    #     12    
    # 11      1  
    # 10      2  
    #     6    
    # 9       3  
    # 8       4  
    #     6    
    
    positions = [
        "    12    ",
        " 11    1  ",
        "10      2 ",
        "          ",
        "9        3 ",
        " 8      4 ",
        "    67   ",
    ]
    
    return '\n'.join(positions)


def format_time(dt):
    """Format a datetime for display."""
    return dt.strftime('%-I:%M %p')


def create_display(lat, lon, console, show_clock=False):
    """Create the display content."""
    now = datetime.datetime.now()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    sunrise_utc, sunset_utc = get_sun_times(lat, lon, now)
    sunrise_local, sunset_local = get_display_times(sunrise_utc, sunset_utc, lat, lon)
    monk_info = get_monk_time(now_utc, sunrise_utc, sunset_utc)
    
    # Calculate daylight duration
    daylight_delta = sunset_utc - sunrise_utc
    daylight_seconds = daylight_delta.total_seconds()
    daylight_h = int(daylight_seconds / 3600)
    daylight_m = int((daylight_seconds % 3600) / 60)
    
    # Calculate monk hour lengths
    day_hour_seconds = daylight_seconds / 12
    night_seconds = 86400 - daylight_seconds
    night_hour_seconds = night_seconds / 12
    day_hour_min = day_hour_seconds / 60
    night_hour_min = night_hour_seconds / 60
    
    # Build content
    period_name = "Day" if monk_info["period"] == "day" else "Night"
    ordinal = format_ordinal(monk_info["hour"])
    
    # Main time display
    main_time = Text()
    main_time.append(f"The {ordinal} Hour of {period_name}\n", style="bold white")
    main_time.append(f"of the {'Day' if monk_info['period'] == 'day' else 'Night'}\n\n", style="dim")
    main_time.append(f"Approximate Digital: {get_approx_digital(monk_info)}", style="cyan")
    
    # Progress bar
    bar_width = 30
    filled = int(bar_width * monk_info["progress"])
    empty = bar_width - filled
    bar = "█" * filled + "░" * empty
    progress_text = Text(f"\nProgress: [{bar}] {monk_info['progress']*100:.0f}%", style="white")
    
    # Details panel
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
                # Build layout with analog clock
                layout = Layout(name="root")
                
                # Create splash + header panel
                header_text = Text()
                header_text.append("M O N K   C L O C K", style="bold magenta")
                header_text.append("\n")
                header_text.append("Sun-based time for the modern monk", style="dim magenta")
                
                header_panel = Panel(header_text, border_style="magenta")
                
                # Create clock panel
                clock_lines = clock_str.split('\n')
                clock_text = Text()
                for i, line in enumerate(clock_lines):
                    if i > 0:
                        clock_text.append('\n')
                    clock_text.append(line)
                
                clock_panel = Panel(
                    clock_text,
                    border_style="magenta"
                )
                
                # Create info panel
                info_text = Text()
                info_text.append(f"The {ordinal} Hour of {period}\n", style="bold white")
                info_text.append(f"of the {period}\n\n", style="dim")
                info_text.append(f"{get_approx_digital(monk_info)}\n", style="cyan bold")
                info_text.append(f"{progress_text}\n\n", style="white")
                info_text.append(details)
                
                info_panel = Panel(
                    info_text,
                    title=f"{period} Hours",
                    border_style="green" if monk_info["period"] == "day" else "blue"
                )
                
                # Layout with header on top, clock and info below
                layout.split_column(
                    Layout(header_panel, name="header", ratio=1),
                    Layout(name="body", ratio=4),
                )
                
                layout["body"].split_row(
                    Layout(clock_panel, name="clock"),
                    Layout(info_panel, name="info"),
                )
                
            else:
                # Standard layout without clock
                layout = Layout(name="root")
                layout.split_column(
                    Layout(name="header"),
                    Layout(name="main"),
                    Layout(name="footer"),
                )
                
                # Add splash to header
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
    
    period_name = "Day" if monk_info["period"] == "day" else "Night"
    ordinal = format_ordinal(monk_info["hour"])
    hour_len = monk_info["hour_length_seconds"] / 60
    
    now = datetime.datetime.now()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    sunrise_utc, sunset_utc = get_sun_times(lat, lon, now)
    sunrise_local, sunset_local = get_display_times(sunrise_utc, sunset_utc, lat, lon)
    
    # Calculate daylight duration
    daylight_delta = sunset_utc - sunrise_utc
    daylight_seconds = daylight_delta.total_seconds()
    daylight_h = int(daylight_seconds / 3600)
    daylight_m = int((daylight_seconds % 3600) / 60)
    
    # Calculate monk hour lengths
    day_hour_min = daylight_seconds / 12 / 60
    night_seconds = 86400 - daylight_seconds
    night_hour_min = night_seconds / 12 / 60
    
    console.print()
    
    if show_clock and clock_str:
        # Print analog clock with details
        clock_lines = clock_str.split('\n')
        console.print(f"[bold white]The {ordinal} Hour of {period_name}[/bold white]")
        console.print(f"[dim]of the {'Day' if monk_info['period'] == 'day' else 'Night'}[/dim]")
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
        console.print(f"[dim]of the {'Day' if monk_info['period'] == 'day' else 'Night'}[/dim]")
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
    parser.add_argument("--live", "-l", action="store_true", help="Run live display (updates every second)")
    parser.add_argument("--clock", "-c", action="store_true", help="Show ASCII analog clock")
    parser.add_argument("--lat", help=f"Latitude (default: from config or {DEFAULT_LAT})")
    parser.add_argument("--lon", help=f"Longitude (default: from config or {DEFAULT_LON})")
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
    
    # Show splash screen
    console.print(get_splash_art(), style="bold magenta")
    
    if args.live:
        run_live(console, lat, lon, args.clock)
    else:
        run_once(console, lat, lon, args.clock)


if __name__ == "__main__":
    main()
