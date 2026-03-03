#!/usr/bin/env python3
"""
The World -- OC Demo (Offline Simulation)

3 Original Characters x 24 Game Hours x Starter Town
Run:  cd backend && uv run python scripts/oc_demo.py
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Ensure the package is importable when running from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from the_world.simulation.engine import SimulationEngine
from the_world.simulation.needs import NEED_NAMES
from the_world.simulation.world_seed import _LOCATIONS

# Silence engine logs so our terminal output stays clean
logging.getLogger("the_world").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GRAY = "\033[90m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

CHAR_COLORS: dict[str, str] = {
    "Luna": MAGENTA,
    "Marcus": CYAN,
    "Mei": YELLOW,
}

WEATHER_ICON: dict[str, str] = {
    "clear": "sun", "cloudy": "cloud", "rain": "rain",
    "storm": "storm", "snow": "snow", "hot": "HOT",
}

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)

# ---------------------------------------------------------------------------
# OC definitions
# ---------------------------------------------------------------------------
OCS = [
    {
        "name": "Luna Brightwood",
        "short": "Luna",
        "bio": "Introverted artist. Finds beauty in solitude -- prefers books and meditation over crowds.",
        "personality": {
            "openness": 0.9, "conscientiousness": 0.4,
            "extraversion": 0.2, "agreeableness": 0.7, "neuroticism": 0.6,
        },
    },
    {
        "name": "Marcus Steele",
        "short": "Marcus",
        "bio": "Boisterous fitness enthusiast. Thrives in the spotlight, hates being alone.",
        "personality": {
            "openness": 0.4, "conscientiousness": 0.8,
            "extraversion": 0.9, "agreeableness": 0.5, "neuroticism": 0.2,
        },
    },
    {
        "name": "Mei Chen",
        "short": "Mei",
        "bio": "Warm social butterfly. Flows naturally between places, always up for coffee or a chat.",
        "personality": {
            "openness": 0.6, "conscientiousness": 0.5,
            "extraversion": 0.7, "agreeableness": 0.8, "neuroticism": 0.3,
        },
    },
]

# ---------------------------------------------------------------------------
# Personality-activity validation mappings
# ---------------------------------------------------------------------------
OPENNESS_ACTIVITIES = {"read", "study", "meditate", "deep_talk"}
SOCIAL_ACTIVITIES = {"hangout", "group_hangout", "chat", "deep_talk"}
# Activities to ignore in frequency analysis (movement / idle)
SKIP_ACTIVITIES = {"idle", "arrived", "walk_to"}

# ---------------------------------------------------------------------------
# Simulation log
# ---------------------------------------------------------------------------

@dataclass
class SimLog:
    """Collects simulation data for post-run analysis."""
    # activity change events: char_short -> [(tick, activity), ...]
    activity_changes: dict[str, list[tuple[int, str]]] = field(
        default_factory=lambda: defaultdict(list))
    # per-tick location count: char_short -> Counter{location: tick_count}
    location_ticks: dict[str, Counter] = field(
        default_factory=lambda: defaultdict(Counter))
    # location transitions: char_short -> count
    location_transitions: dict[str, int] = field(
        default_factory=lambda: defaultdict(int))
    # needs snapshots (every N ticks): char_short -> [(tick, needs_dict), ...]
    needs_snapshots: dict[str, list[tuple[int, dict]]] = field(
        default_factory=lambda: defaultdict(list))
    # mood snapshots: char_short -> [(tick, mood_score), ...]
    mood_snapshots: dict[str, list[tuple[int, float]]] = field(
        default_factory=lambda: defaultdict(list))
    # events: [(tick, event_type, char_name, description), ...]
    events: list[tuple[int, str, str, str]] = field(default_factory=list)
    # encounters: [(tick, [char_names], location), ...]
    encounters: list[tuple[int, list[str], str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def need_bar(value: float, width: int = 10) -> str:
    filled = round(value / 100 * width)
    color = GREEN if value >= 60 else YELLOW if value >= 30 else RED
    return f"{color}{'#' * filled}{DIM}{'.' * (width - filled)}{RESET}"


def color_for(name: str) -> str:
    for key, c in CHAR_COLORS.items():
        if key in name:
            return c
    return WHITE


def format_time(clock: dict) -> str:
    h = clock["currentHour"]
    m = clock["currentTick"] % 60
    day = clock["currentDay"]
    season = clock["currentSeason"].capitalize()
    period = "day" if 6 <= h < 22 else "night"
    return f"Day {day} | {h:02d}:{m:02d} | {season} ({period})"


def bar_chart(count: int, total: int, width: int = 20) -> str:
    """Return a plain-text bar for analysis report."""
    if total == 0:
        return ""
    filled = round(count / total * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------

TOTAL_TICKS = 1440  # 24 game hours
PANEL_INTERVAL = 120  # print full panel every 2 game hours
NEEDS_SNAPSHOT_INTERVAL = 30  # snapshot needs every 30 ticks
DIVIDER = f"{GRAY}{'=' * 62}{RESET}"
THIN_DIVIDER = f"{GRAY}{'-' * 62}{RESET}"


class DemoRunner:
    def __init__(self) -> None:
        self.engine: SimulationEngine | None = None
        self.id_to_short: dict[str, str] = {}
        self.last_panel_tick = -PANEL_INTERVAL
        self.last_activities: dict[str, str] = {}
        self.last_locations: dict[str, str] = {}
        self.encounter_keys: set[str] = set()
        self.encounter_count = 0
        self.start_time = 0.0
        self.stopped = False
        self.log = SimLog()

    # -- Banner & intro ----------------------------------------------------

    def print_banner(self) -> None:
        print(f"""
{BOLD}{BLUE}================================================================
     T H E   W O R L D  --  OC Demo  (Offline Simulation)
        3 Characters  |  24 Game Hours  |  Starter Town
================================================================{RESET}
""")

    def print_characters(self) -> None:
        print(f"{BOLD}-- Meet the Characters --{RESET}\n")
        for oc in OCS:
            c = color_for(oc["name"])
            p = oc["personality"]
            traits = (f"O={p['openness']:.1f} C={p['conscientiousness']:.1f} "
                      f"E={p['extraversion']:.1f} A={p['agreeableness']:.1f} "
                      f"N={p['neuroticism']:.1f}")
            print(f"  {c}{BOLD}{oc['name']}{RESET}")
            print(f"  {DIM}{oc['bio']}{RESET}")
            print(f"  {GRAY}Big Five: {traits}{RESET}\n")

    # -- Panel (full status snapshot) --------------------------------------

    def print_panel(self, payload: dict) -> None:
        clock = payload["clock"]
        weather = payload.get("weather", {})
        w_type = weather.get("current", "clear")
        w_label = WEATHER_ICON.get(w_type, w_type)
        temp = weather.get("temperatureModifier", 0.0)
        temp_label = "cold" if temp < -0.3 else "hot" if temp > 0.3 else "mild"

        print(f"\n{DIVIDER}")
        print(f"  {BOLD}{format_time(clock)}{RESET}    "
              f"Weather: {w_label} ({temp_label})")
        print(DIVIDER)

        for char in payload["characters"]:
            cid = char["characterId"]
            short = self.id_to_short.get(cid, "???")
            clr = color_for(short)
            name = short
            for oc in OCS:
                if oc["short"] == short:
                    name = oc["name"]
                    break

            loc = char["currentLocation"]
            act = char["currentActivity"]
            mood = char["mood"]
            mood_score = char["moodScore"]
            needs = char["needs"]

            print(f"  {clr}{BOLD}{name:<20}{RESET} "
                  f"@ {loc:<18} [{act}]")

            # Needs - two rows of three
            for row_start in range(0, 6, 3):
                parts = []
                for n in list(NEED_NAMES)[row_start:row_start + 3]:
                    v = needs.get(n, 50)
                    bar = need_bar(v)
                    parts.append(f"{n[:3]:>3} {bar} {v:5.1f}")
                print(f"    {'  '.join(parts)}")

            mood_color = GREEN if mood_score >= 60 else YELLOW if mood_score >= 30 else RED
            print(f"    {mood_color}mood: {mood} ({mood_score}){RESET}")
            print()

        print(THIN_DIVIDER)

    # -- Tick callback -----------------------------------------------------

    async def on_tick(self, payload: dict) -> None:
        if self.stopped:
            return

        clock = payload["clock"]
        tick = clock["currentTick"]
        characters = payload["characters"]

        # Detect activity & location changes + record data
        for char in characters:
            cid = char["characterId"]
            short = self.id_to_short.get(cid, "???")
            name = next((oc["name"] for oc in OCS if oc["short"] == short), short)
            act = char["currentActivity"]
            loc = char["currentLocation"]
            old_act = self.last_activities.get(cid)
            old_loc = self.last_locations.get(cid)
            c = color_for(name)

            # --- Record location tick ---
            self.log.location_ticks[short][loc] += 1

            if old_loc and loc != old_loc:
                print(f"  {c}->{RESET} {name} moved to {BOLD}{loc}{RESET}"
                      f"  {DIM}(from {old_loc}){RESET}")
                self.log.location_transitions[short] += 1

            if old_act and act != old_act and act not in SKIP_ACTIVITIES:
                print(f"  {c}*{RESET}  {name} started {BOLD}{act}{RESET}")
                # --- Record activity change ---
                self.log.activity_changes[short].append((tick, act))

            # First tick: record initial activity if meaningful
            if old_act is None and act not in SKIP_ACTIVITIES:
                self.log.activity_changes[short].append((tick, act))

            self.last_activities[cid] = act
            self.last_locations[cid] = loc

        # --- Record needs & mood snapshots ---
        if tick % NEEDS_SNAPSHOT_INTERVAL == 0:
            for char in characters:
                cid = char["characterId"]
                short = self.id_to_short.get(cid, "???")
                self.log.needs_snapshots[short].append(
                    (tick, dict(char["needs"])))
                self.log.mood_snapshots[short].append(
                    (tick, char["moodScore"]))

        # Encounter detection (same location)
        loc_chars: dict[str, list[str]] = {}
        for char in characters:
            loc = char["currentLocation"]
            cid = char["characterId"]
            short = self.id_to_short.get(cid, "???")
            name = next((oc["name"] for oc in OCS if oc["short"] == short), short)
            loc_chars.setdefault(loc, []).append(name)

        for loc, names in loc_chars.items():
            if len(names) >= 2:
                key = f"{tuple(sorted(names))}@{loc}"
                if key not in self.encounter_keys:
                    self.encounter_keys.add(key)
                    self.encounter_count += 1
                    joined = " & ".join(names)
                    print(f"  {BOLD}{YELLOW}!! ENCOUNTER: {joined}"
                          f" at {loc}{RESET}")
                    self.log.encounters.append((tick, sorted(names), loc))

        # Full panel every PANEL_INTERVAL minutes
        if tick - self.last_panel_tick >= PANEL_INTERVAL:
            self.last_panel_tick = tick
            self.print_panel(payload)

        # Auto-stop
        if tick >= TOTAL_TICKS:
            self.stopped = True
            if self.engine:
                self.engine.stop()

    # -- Event callback ----------------------------------------------------

    async def on_event(self, event: dict) -> None:
        if self.stopped:
            return
        etype = event.get("type", "")
        desc = event.get("description", "")
        name = event.get("characterName", "")

        # --- Record event ---
        tick = 0
        if self.engine:
            tick = self.engine.clock.tick
        self.log.events.append((tick, etype, name, desc))

        if etype == "need_critical":
            need = event.get("data", {}).get("need", "?")
            val = event.get("data", {}).get("value", 0)
            print(f"  {RED}{BOLD}!! CRITICAL: {name}'s {need} "
                  f"is at {val:.0f}!{RESET}")
        elif etype == "random_event":
            print(f"  {GREEN}{BOLD}** EVENT: {desc}{RESET}")
        # activity_start and location_change handled in on_tick

    # -- Analysis Report ---------------------------------------------------

    def _activity_counts(self, short: str) -> Counter:
        """Count how many times each activity was started."""
        return Counter(act for _, act in self.log.activity_changes[short])

    def _get_oc(self, short: str) -> dict:
        return next(oc for oc in OCS if oc["short"] == short)

    def print_analysis_report(self) -> list[str]:
        """Print structured analysis and return lines for file saving."""
        lines: list[str] = []

        def out(s: str = "") -> None:
            print(s)
            lines.append(s)

        elapsed = time.time() - self.start_time
        tick = self.engine.clock.tick if self.engine else 0
        shorts = [oc["short"] for oc in OCS]

        out(f"\n{BOLD}{BLUE}{'=' * 64}")
        out(f"              SIMULATION ANALYSIS REPORT")
        out(f"{'=' * 64}{RESET}")
        out()
        out(f"  Real time : {elapsed:.1f}s")
        out(f"  Game time : {tick} minutes ({tick // 60}h {tick % 60}m)")
        out(f"  Encounters: {self.encounter_count}")
        out()

        # -- A. Activity Frequency ------------------------------------------
        out(f"{BOLD}-- A. Activity Frequency --{RESET}")
        out()

        all_counts: dict[str, Counter] = {}
        for short in shorts:
            counts = self._activity_counts(short)
            all_counts[short] = counts
            total = sum(counts.values())
            oc = self._get_oc(short)
            c = color_for(oc["name"])
            out(f"  {c}{BOLD}{oc['name']}{RESET}  "
                f"({total} activity changes, {len(counts)} unique)")

            for act, cnt in counts.most_common(10):
                pct = cnt / total * 100 if total else 0
                barchart = bar_chart(cnt, total, 16)
                marker = ""
                if act in OPENNESS_ACTIVITIES:
                    marker = f" {MAGENTA}[O]{RESET}"
                elif act in SOCIAL_ACTIVITIES:
                    marker = f" {CYAN}[E]{RESET}"
                out(f"    {act:<16} {barchart} {cnt:>3}x ({pct:4.1f}%){marker}")

            out()

        # -- B. Location Preferences ----------------------------------------
        out(f"{BOLD}-- B. Location Preferences --{RESET}")
        out()

        for short in shorts:
            oc = self._get_oc(short)
            c = color_for(oc["name"])
            loc_counts = self.log.location_ticks[short]
            total_ticks = sum(loc_counts.values())
            transitions = self.log.location_transitions[short]
            unique_locs = len(loc_counts)

            out(f"  {c}{BOLD}{oc['short']}{RESET}  "
                f"({unique_locs} locations, {transitions} moves)")

            for loc, ticks in loc_counts.most_common():
                pct = ticks / total_ticks * 100 if total_ticks else 0
                barchart = bar_chart(ticks, total_ticks, 16)
                out(f"    {loc:<18} {barchart} {pct:5.1f}%  ({ticks} ticks)")

            out()

        # -- C. Needs Summary -----------------------------------------------
        out(f"{BOLD}-- C. Needs Summary --{RESET}")
        out()

        for short in shorts:
            oc = self._get_oc(short)
            c = color_for(oc["name"])
            snapshots = self.log.needs_snapshots[short]
            mood_snaps = self.log.mood_snapshots[short]

            if not snapshots:
                out(f"  {c}{BOLD}{oc['short']}{RESET}: no data")
                continue

            out(f"  {c}{BOLD}{oc['name']}{RESET}")

            first_needs = snapshots[0][1]
            last_needs = snapshots[-1][1]

            for need in NEED_NAMES:
                vals = [s[1].get(need, 50) for s in snapshots]
                start_v = first_needs.get(need, 50)
                end_v = last_needs.get(need, 50)
                min_v = min(vals)
                avg_v = sum(vals) / len(vals)

                # Check if value dropped below critical-ish threshold
                critical_ticks = [s[0] for s in snapshots
                                  if s[1].get(need, 50) < 20]
                crit_marker = ""
                if critical_ticks:
                    crit_marker = (f"  {RED}CRITICAL @ tick "
                                   f"{critical_ticks[0]}{RESET}")

                out(f"    {need:<8} {start_v:5.1f} -> {end_v:5.1f}  "
                    f"(min={min_v:5.1f}  avg={avg_v:5.1f}){crit_marker}")

            # Mood summary
            if mood_snaps:
                mood_vals = [m[1] for m in mood_snaps]
                avg_mood = sum(mood_vals) / len(mood_vals)
                min_mood = min(mood_vals)
                max_mood = max(mood_vals)
                out(f"    {'mood':<8} avg={avg_mood:5.1f}  "
                    f"min={min_mood:5.1f}  max={max_mood:5.1f}")

            out()

        # -- D. Character Comparison ----------------------------------------
        out(f"{BOLD}-- D. Character Comparison --{RESET}")
        out()

        # Build comparison data
        comp: dict[str, dict] = {}
        for short in shorts:
            counts = all_counts[short]
            top_acts = counts.most_common(3)
            loc_counts = self.log.location_ticks[short]
            top_locs = loc_counts.most_common(2)
            total_loc = sum(loc_counts.values())
            mood_snaps = self.log.mood_snapshots[short]
            avg_mood = (sum(m[1] for m in mood_snaps) / len(mood_snaps)
                        if mood_snaps else 0)

            comp[short] = {
                "top_acts": top_acts,
                "top_locs": top_locs,
                "total_loc": total_loc,
                "avg_mood": avg_mood,
                "unique_acts": len(counts),
                "unique_locs": len(loc_counts),
                "transitions": self.log.location_transitions[short],
            }

        # Table header
        header = f"  {'Metric':<20}"
        for short in shorts:
            header += f" | {color_for(short)}{BOLD}{short:<14}{RESET}"
        out(header)
        out(f"  {'-' * 20}" + (" | " + "-" * 14) * len(shorts))

        # Top Activity
        row = f"  {'Top Activity':<20}"
        for short in shorts:
            acts = comp[short]["top_acts"]
            label = acts[0][0] if acts else "-"
            row += f" | {label:<14}"
        out(row)

        # 2nd Activity
        row = f"  {'2nd Activity':<20}"
        for short in shorts:
            acts = comp[short]["top_acts"]
            label = acts[1][0] if len(acts) > 1 else "-"
            row += f" | {label:<14}"
        out(row)

        # 3rd Activity
        row = f"  {'3rd Activity':<20}"
        for short in shorts:
            acts = comp[short]["top_acts"]
            label = acts[2][0] if len(acts) > 2 else "-"
            row += f" | {label:<14}"
        out(row)

        # Top Location
        row = f"  {'Top Location':<20}"
        for short in shorts:
            locs = comp[short]["top_locs"]
            total = comp[short]["total_loc"]
            if locs:
                pct = locs[0][1] / total * 100 if total else 0
                label = f"{locs[0][0][:10]} ({pct:.0f}%)"
            else:
                label = "-"
            row += f" | {label:<14}"
        out(row)

        # Avg Mood
        row = f"  {'Avg Mood':<20}"
        for short in shorts:
            row += f" | {comp[short]['avg_mood']:<14.1f}"
        out(row)

        # Unique Activities
        row = f"  {'Activities Used':<20}"
        for short in shorts:
            row += f" | {comp[short]['unique_acts']:<14}"
        out(row)

        # Unique Locations
        row = f"  {'Locations Visited':<20}"
        for short in shorts:
            row += f" | {comp[short]['unique_locs']:<14}"
        out(row)

        # Location Moves
        row = f"  {'Location Moves':<20}"
        for short in shorts:
            row += f" | {comp[short]['transitions']:<14}"
        out(row)

        out()

        # -- E. Personality Validation --------------------------------------
        out(f"{BOLD}-- E. Personality Validation --{RESET}")
        out()

        passes = 0
        total_checks = 3

        # Luna: openness activities > 40%
        luna_counts = all_counts["Luna"]
        luna_total = sum(luna_counts.values())
        luna_open = sum(luna_counts.get(a, 0) for a in OPENNESS_ACTIVITIES)
        luna_pct = luna_open / luna_total * 100 if luna_total else 0
        luna_pass = luna_pct > 40
        luna_p = self._get_oc("Luna")["personality"]
        status = (f"{GREEN}PASS \u2713{RESET}" if luna_pass
                  else f"{RED}WARN \u2717{RESET}")
        if luna_pass:
            passes += 1
        out(f"  {MAGENTA}Luna{RESET}   "
            f"(O={luna_p['openness']}, E={luna_p['extraversion']}): "
            f"openness activities = {luna_pct:.0f}%  -> {status}")

        # Marcus: social activities > 40% OR leaves Home significantly
        marcus_counts = all_counts["Marcus"]
        marcus_total = sum(marcus_counts.values())
        marcus_social = sum(marcus_counts.get(a, 0)
                            for a in SOCIAL_ACTIVITIES)
        marcus_pct = (marcus_social / marcus_total * 100
                      if marcus_total else 0)
        marcus_loc = self.log.location_ticks["Marcus"]
        marcus_total_ticks = sum(marcus_loc.values())
        marcus_home_pct = (marcus_loc.get("Home", 0)
                           / marcus_total_ticks * 100
                           if marcus_total_ticks else 100)
        marcus_pass = marcus_pct > 40 or marcus_home_pct < 60
        marcus_p = self._get_oc("Marcus")["personality"]
        status = (f"{GREEN}PASS \u2713{RESET}" if marcus_pass
                  else f"{RED}WARN \u2717{RESET}")
        if marcus_pass:
            passes += 1
        out(f"  {CYAN}Marcus{RESET} "
            f"(C={marcus_p['conscientiousness']}, "
            f"E={marcus_p['extraversion']}): "
            f"social activities = {marcus_pct:.0f}%, "
            f"home = {marcus_home_pct:.0f}%  -> {status}")

        # Mei: unique activities >= 4 AND unique locations >= 3
        mei_counts = all_counts["Mei"]
        mei_unique_acts = len(mei_counts)
        mei_unique_locs = len(self.log.location_ticks["Mei"])
        mei_pass = mei_unique_acts >= 4 and mei_unique_locs >= 3
        status = (f"{GREEN}PASS \u2713{RESET}" if mei_pass
                  else f"{RED}WARN \u2717{RESET}")
        if mei_pass:
            passes += 1
        out(f"  {YELLOW}Mei{RESET}    (balanced): "
            f"unique activities = {mei_unique_acts}, "
            f"unique locations = {mei_unique_locs}  -> {status}")

        out()
        result_color = (GREEN if passes >= 2
                        else YELLOW if passes >= 1
                        else RED)
        out(f"  {result_color}{BOLD}Result: {passes}/{total_checks} "
            f"personality checks passed{RESET}")
        out()
        out(f"{DIM}  No network requests. 100% local simulation.{RESET}")
        out()

        return lines

    def save_report(self, lines: list[str]) -> str:
        """Save analysis report to file (plain text, no ANSI codes)."""
        out_path = Path(__file__).resolve().parent / "oc_demo_results.txt"
        plain = "\n".join(strip_ansi(line) for line in lines)
        out_path.write_text(plain, encoding="utf-8")
        return str(out_path)

    # -- Main entry --------------------------------------------------------

    async def run(self) -> None:
        self.print_banner()
        self.print_characters()

        # Create engine
        self.engine = SimulationEngine(
            world_id="oc-demo",
            time_scale=1.0,
            tick_interval_s=0.03,
        )

        # Add Starter Town locations
        print(f"{BOLD}-- Loading Starter Town --{RESET}\n")
        for loc in _LOCATIONS:
            self.engine.add_location(
                name=loc["name"],
                location_type=loc["location_type"],
                position_x=loc["position_x"],
                position_y=loc["position_y"],
                available_activities=loc.get("available_activities"),
            )
            print(f"  + {loc['name']} ({loc['location_type']})")
        print()

        # Spawn characters
        print(f"{BOLD}-- Spawning Characters --{RESET}\n")
        for oc in OCS:
            cid = str(uuid.uuid4())
            self.engine.add_character(cid, oc["name"], oc["personality"])
            self.id_to_short[cid] = oc["short"]
            c = color_for(oc["name"])
            print(f"  {c}* {oc['name']} spawned at Home{RESET}")
        print()

        # Register callbacks
        self.engine.on_tick(self.on_tick)
        self.engine.on_event(self.on_event)

        # Go!
        real_est = TOTAL_TICKS * 0.03
        print(f"{BOLD}-- Simulation Running "
              f"({TOTAL_TICKS} game-min ~ {real_est:.0f}s real) --{RESET}\n")
        self.start_time = time.time()
        self.engine.start()

        # Wait for simulation to finish or Ctrl+C
        try:
            while self.engine.running:
                await asyncio.sleep(0.1)
            # Let final events flush
            await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            pass

        report_lines = self.print_analysis_report()
        saved = self.save_report(report_lines)
        print(f"  Report saved to: {BOLD}{saved}{RESET}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    runner = DemoRunner()
    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        print(f"\n{DIM}  Interrupted by user.{RESET}")
        if runner.engine:
            runner.engine.stop()
        report_lines = runner.print_analysis_report()
        runner.save_report(report_lines)
