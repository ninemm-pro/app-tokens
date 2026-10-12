#!/usr/bin/env python3
"""Checks the token lists before a pull request is merged.

Usage: python3 scripts/check_list.py <base git ref>

Every list must stay a valid token list. An entry added or changed since <base> must also be a
complete PulseChain entry whose address is listed once, with its logo here in token-logo/: a PNG
named by the address, at least MIN_LOGO_PX square, at most MAX_LOGO_BYTES. Entries already on the
list are not held to the logo rules, so a request is never refused for an older entry's gap.

Python's standard library only, so nothing needs installing or pinning. Exits 1 with one line per
problem.
"""
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

LISTS = ("9mm-tokenlist.json", "9mm-tokenlist-extended.json")
PULSECHAIN = 369
LOGO_BASE = "https://raw.githubusercontent.com/ninemm-pro/app-tokens/main/token-logo/"
MIN_LOGO_PX = 128
MAX_LOGO_BYTES = 200 * 1024
MAX_TEXT = 64
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
FIELDS = {"chainId", "address", "name", "symbol", "decimals", "logoURI", "tags", "extensions"}
ROOT = Path(__file__).resolve().parent.parent


def entry_problems(token):
    """What makes one entry not a complete PulseChain token entry."""
    problems = []
    if not isinstance(token, dict):
        return ["is not an object"]
    if token.get("chainId") != PULSECHAIN:
        problems.append(f"chainId must be {PULSECHAIN}")
    if not isinstance(token.get("address"), str) or not ADDRESS.fullmatch(token["address"]):
        problems.append("address must be 0x and 40 hex digits")
    for field in ("name", "symbol"):
        text = token.get(field)
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
            problems.append(f"{field} must be 1 to {MAX_TEXT} characters")
    decimals = token.get("decimals")
    if not isinstance(decimals, int) or isinstance(decimals, bool) or not 0 <= decimals <= 255:
        problems.append("decimals must be a whole number from 0 to 255")
    if not isinstance(token.get("logoURI"), str):
        problems.append("logoURI is missing")
    unknown = set(token) - FIELDS
    if unknown:
        problems.append(f"unknown fields: {', '.join(sorted(unknown))}")
    return problems


def logo_problems(token):
    """What is wrong with a new entry's logo: here, a PNG named by its address, the right size."""
    expected = f"{LOGO_BASE}{token['address']}.png"
    if token["logoURI"] != expected:
        return [f"logoURI must be {expected}"]
    path = ROOT / "token-logo" / f"{token['address']}.png"
    if not path.is_file():
        return [f"logo file token-logo/{path.name} is missing"]
    data = path.read_bytes()
    if len(data) > MAX_LOGO_BYTES:
        return [f"logo is {len(data) // 1024} KB; at most {MAX_LOGO_BYTES // 1024} KB"]
    if not data.startswith(PNG_SIGNATURE) or data[12:16] != b"IHDR":
        return ["logo is not a PNG file"]
    width, height = struct.unpack(">II", data[16:24])
    if width != height or width < MIN_LOGO_PX:
        return [f"logo is {width}x{height}; it must be square and at least {MIN_LOGO_PX}x{MIN_LOGO_PX}"]
    return []


def base_tokens(base, name):
    """The list's entries at <base>, as canonical JSON text, or an empty set where it did not exist."""
    shown = subprocess.run(["git", "show", f"{base}:{name}"], cwd=ROOT, capture_output=True, text=True, timeout=60)
    if shown.returncode != 0:
        return set()
    return {json.dumps(token, sort_keys=True) for token in json.loads(shown.stdout).get("tokens", [])}


def list_problems(name, base):
    path = ROOT / name
    if not path.is_file():
        return []
    try:
        tokens = json.loads(path.read_text(encoding="utf-8")).get("tokens")
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as error:
        return [f"{name}: not a valid token list ({error})"]
    if not isinstance(tokens, list):
        return [f"{name}: has no tokens array"]
    before = base_tokens(base, name)
    counts = {}
    for token in tokens:
        if isinstance(token, dict) and isinstance(token.get("address"), str):
            counts[token["address"].lower()] = counts.get(token["address"].lower(), 0) + 1
    problems = []
    for index, token in enumerate(tokens):
        if json.dumps(token, sort_keys=True) in before:
            continue
        label = f"{name}: entry {index + 1} ({token.get('symbol', '?') if isinstance(token, dict) else '?'})"
        found = entry_problems(token)
        if not found:
            if counts[token["address"].lower()] > 1:
                found.append("its address is already on the list")
            found += logo_problems(token)
        problems += [f"{label}: {problem}" for problem in found]
    return problems


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 scripts/check_list.py <base git ref>")
    problems = [problem for name in LISTS for problem in list_problems(name, sys.argv[1])]
    for problem in problems:
        print(problem)
    if problems:
        sys.exit(1)
    print("The lists pass.")


if __name__ == "__main__":
    main()
