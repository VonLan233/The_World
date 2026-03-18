#!/usr/bin/env python3
"""
Benchmark script: qwen3.5:9b on role-play dialogue scenarios.

Run:
    cd backend
    OLLAMA_URL=http://localhost:11435 OLLAMA_MODEL=qwen3.5:9b \\
        uv run python scripts/benchmark_qwen.py

Output: scripts/benchmark_results_qwen3.5_9b.json
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Make the_world package importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import httpx

from the_world.ai.tier2_ollama import generate_ollama_response
from the_world.ai.tier3_rules import generate_rules_response
from the_world.ai.types import AIContext, InteractionType
from the_world.config import settings

# ---------------------------------------------------------------------------
# ANSI
# ---------------------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"

# ---------------------------------------------------------------------------
# Test matrix
# ---------------------------------------------------------------------------

PERSONALITIES = [
    {
        "label": "外向热情型",
        "name": "Aria",
        "personality": {
            "openness": 0.8,
            "conscientiousness": 0.5,
            "extraversion": 0.9,
            "agreeableness": 0.8,
            "neuroticism": 0.3,
        },
    },
    {
        "label": "内敛理性型",
        "name": "Leon",
        "personality": {
            "openness": 0.6,
            "conscientiousness": 0.9,
            "extraversion": 0.2,
            "agreeableness": 0.4,
            "neuroticism": 0.2,
        },
    },
    {
        "label": "敏感创意型",
        "name": "Nova",
        "personality": {
            "openness": 0.9,
            "conscientiousness": 0.3,
            "extraversion": 0.5,
            "agreeableness": 0.6,
            "neuroticism": 0.8,
        },
    },
]

INTERACTION_TYPES = [
    InteractionType.GREETING,
    InteractionType.DAILY_CONVERSATION,
    InteractionType.FIRST_MEETING,
    InteractionType.RELATIONSHIP_MILESTONE,
    InteractionType.IDLE_CHAT,
    InteractionType.NEED_CRITICAL,
]

# ---------------------------------------------------------------------------
# Connectivity pre-check
# ---------------------------------------------------------------------------

async def check_connectivity() -> None:
    """Verify Ollama is reachable and qwen3.5:9b is available."""
    url = settings.OLLAMA_URL
    model = settings.OLLAMA_MODEL
    print(f"{BOLD}-- Connectivity check --{RESET}")
    print(f"  URL   : {url}")
    print(f"  Model : {model}")

    try:
        async with httpx.AsyncClient(trust_env=False, timeout=10.0) as client:
            resp = await client.get(f"{url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        print(f"\n{RED}{BOLD}ERROR: Cannot reach Ollama at {url}{RESET}")
        print(f"  {exc}")
        print("\nMake sure your SSH tunnel is running:")
        print("  ssh -L 11435:localhost:11434 Administrator@<host> -N")
        sys.exit(1)

    available_models = [m["name"] for m in data.get("models", [])]
    # Accept both "qwen3.5:9b" and "qwen3.5:9b-..." variants
    found = any(m == model or m.startswith(model.split(":")[0] + ":" + model.split(":")[1]) for m in available_models)
    if not found:
        print(f"\n{YELLOW}WARNING: Model '{model}' not found in Ollama.{RESET}")
        print(f"  Available: {available_models}")
        print("  Proceeding anyway — Ollama may still serve it.\n")
    else:
        print(f"  {GREEN}Model confirmed: {model}{RESET}")
    print()

# ---------------------------------------------------------------------------
# Single test case
# ---------------------------------------------------------------------------

async def run_case(char: dict, itype: InteractionType, case_idx: int) -> dict:
    ctx = AIContext(
        character_id=f"bench-{char['name'].lower()}-{case_idx}",
        character_name=char["name"],
        personality=char["personality"],
        mood="neutral",
        mood_score=50.0,
        current_activity="walking",
        current_location="Town Square",
        interaction_type=itype,
        target_name="Alex",
        relationship_score=30.0,
        memories=[],
        sim_tick=case_idx,
    )

    result: dict = {
        "case_id": case_idx,
        "personality_label": char["label"],
        "character_name": char["name"],
        "interaction_type": itype.value,
        "latency_ms": None,
        "tier2_dialogue": None,
        "tier3_dialogue": None,
        "dialogue_length": None,
        "is_non_empty": False,
        "error": None,
    }

    # Tier 3 (rules) — always fast
    try:
        t3_resp = await generate_rules_response(ctx)
        result["tier3_dialogue"] = t3_resp.dialogue
    except Exception as exc:
        result["tier3_dialogue"] = f"[error: {exc}]"

    # Tier 2 (qwen via Ollama)
    t_start = time.perf_counter()
    try:
        t2_resp = await generate_ollama_response(ctx)
        latency = (time.perf_counter() - t_start) * 1000
        result["latency_ms"] = round(latency, 1)
        result["tier2_dialogue"] = t2_resp.dialogue
        result["dialogue_length"] = len(t2_resp.dialogue)
        result["is_non_empty"] = bool(t2_resp.dialogue.strip())
    except Exception as exc:
        latency = (time.perf_counter() - t_start) * 1000
        result["latency_ms"] = round(latency, 1)
        result["error"] = str(exc)
        result["is_non_empty"] = False

    return result

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    print(f"""
{BOLD}{CYAN}================================================================
     Benchmark: qwen3.5:9b  |  Role-play Dialogue
     3 Personalities x 6 Interaction Types = 18 Cases
================================================================{RESET}
""")

    await check_connectivity()

    # Build test cases
    cases: list[tuple[dict, InteractionType]] = [
        (char, itype)
        for char in PERSONALITIES
        for itype in INTERACTION_TYPES
    ]

    results: list[dict] = []
    total = len(cases)

    print(f"{BOLD}-- Running {total} test cases --{RESET}\n")

    for idx, (char, itype) in enumerate(cases, start=1):
        label = f"{char['label']} / {itype.value}"
        print(f"  [{idx:>2}/{total}] {label:<45}", end="", flush=True)

        result = await run_case(char, itype, idx)
        results.append(result)

        if result["error"]:
            print(f"{RED}ERROR{RESET}  {DIM}{result['error'][:60]}{RESET}")
        else:
            lat = result["latency_ms"]
            lat_color = GREEN if lat < 3000 else YELLOW if lat < 8000 else RED
            print(f"{lat_color}{lat:>7.0f}ms{RESET}  {DIM}{result['tier2_dialogue'][:50]!r}{RESET}")

    print()

    # ---------------------------------------------------------------------------
    # Aggregate stats
    # ---------------------------------------------------------------------------
    success_results = [r for r in results if r["error"] is None and r["is_non_empty"]]
    success_count = len(success_results)
    latencies = [r["latency_ms"] for r in results if r["latency_ms"] is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    sorted_lat = sorted(latencies)
    p95_idx = max(0, int(len(sorted_lat) * 0.95) - 1)
    p95_latency = sorted_lat[p95_idx] if sorted_lat else 0.0

    meta = {
        "model": settings.OLLAMA_MODEL,
        "ollama_url": settings.OLLAMA_URL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cases": total,
        "success_count": success_count,
        "avg_latency_ms": round(avg_latency, 1),
        "p95_latency_ms": round(p95_latency, 1),
    }

    report = {"meta": meta, "results": results}

    # ---------------------------------------------------------------------------
    # Save JSON
    # ---------------------------------------------------------------------------
    out_path = Path(__file__).resolve().parent / "benchmark_results_qwen3.5_9b.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------------------------------------------------------------------------
    # Summary table
    # ---------------------------------------------------------------------------
    print(f"{BOLD}{CYAN}================================================================")
    print(f"  BENCHMARK SUMMARY")
    print(f"================================================================{RESET}")
    print(f"  Model         : {meta['model']}")
    print(f"  Endpoint      : {meta['ollama_url']}")
    print(f"  Total cases   : {total}")
    success_color = GREEN if success_count == total else YELLOW if success_count > 0 else RED
    print(f"  Successes     : {success_color}{success_count}/{total}{RESET}")
    lat_color = GREEN if avg_latency < 3000 else YELLOW if avg_latency < 8000 else RED
    print(f"  Avg latency   : {lat_color}{avg_latency:.0f} ms{RESET}")
    print(f"  P95 latency   : {lat_color}{p95_latency:.0f} ms{RESET}")
    print()

    # Per-personality breakdown
    print(f"{BOLD}  Per-personality avg latency:{RESET}")
    for char in PERSONALITIES:
        char_results = [r for r in results if r["character_name"] == char["name"] and r["latency_ms"] is not None]
        if char_results:
            avg = sum(r["latency_ms"] for r in char_results) / len(char_results)
            ok = sum(1 for r in char_results if r["is_non_empty"])
            print(f"    {char['label']:<12} ({char['name']:<6})  {avg:>7.0f} ms  {ok}/{len(char_results)} ok")
    print()

    # Per-interaction type breakdown
    print(f"{BOLD}  Per-interaction avg latency:{RESET}")
    for itype in INTERACTION_TYPES:
        itype_results = [r for r in results if r["interaction_type"] == itype.value and r["latency_ms"] is not None]
        if itype_results:
            avg = sum(r["latency_ms"] for r in itype_results) / len(itype_results)
            ok = sum(1 for r in itype_results if r["is_non_empty"])
            print(f"    {itype.value:<28}  {avg:>7.0f} ms  {ok}/{len(itype_results)} ok")
    print()

    print(f"  Report saved: {BOLD}{out_path}{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
