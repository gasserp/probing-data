#!/usr/bin/env python3
"""Rebuild password counts erased by the cloneLedger bug (gasserp/probing#39).

Before the fix, every accepted batch was applied to a ledger copy without
passwords, so each ingest commit's ledger holds exactly the per-hour
passwords of the last batch accepted in that run (when that batch came from
a decoy). After the fix, ledgers accumulate, so a run's contribution is the
difference from the previous commit.

The script collects each run's hourly contribution in commit order, clears
the password dimension of the current ledger, and replays the contributions
in that order with ingest's addMapCount rule (a new value past 10,000
distinct values per period goes to the overflow count). Hourly periods never
come near the cap, so their maps are exact per batch; daily, monthly, and
yearly periods are rebuilt from them in acceptance order.

usage: recover_passwords.py <probing-data checkout> <fix cutoff ISO time> <out ledger>
"""
import json
import subprocess
import sys
from datetime import datetime

MAX_VALUES = 10_000
LEDGER = "data/acceptance-ledger.json"
DECOY = "decoy"

repo, cutoff, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
cutoff = datetime.fromisoformat(cutoff.replace("Z", "+00:00")).timestamp()


def git(*args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout


# Kinds come from the current registry: ledgers written before kinds existed
# have none, and every source then published passwords.
KINDS = {
    (source["source_id"], source["source_epoch"]): source.get("kind") or "host"
    for source in json.loads(git("show", "origin/main:registry/sources.json"))["sources"]
}


def batches(ledger):
    found = {}
    for source in ledger["sources"]:
        for batch in source["batches"]:
            key = (source["source_id"], source["source_epoch"], int(batch["sequence"]))
            found[key] = KINDS.get(key[:2], "host")
    return found


def hourly_passwords(ledger):
    result = {}
    for key, period in ledger["periods"].items():
        if not key.startswith("hourly\x00"):
            continue
        values = dict(period.get("passwords") or {})
        overflow = period.get("passwords_overflow", 0)
        if len(values) >= MAX_VALUES:
            raise SystemExit(f"{key} reached the cap; hourly contributions would be inexact")
        if values or overflow:
            result[key] = (values, overflow)
    return result


def difference(current, previous):
    delta = {}
    for key, (values, overflow) in current.items():
        old_values, old_overflow = previous.get(key, ({}, 0))
        changed = {v: c - old_values.get(v, 0) for v, c in values.items() if c > old_values.get(v, 0)}
        if changed or overflow > old_overflow:
            delta[key] = (changed, overflow - old_overflow)
    return delta


contributions = []  # (commit, description, {hourly key: (values, overflow)})
lost = []
previous_batches = {}
previous_hourly = {}
for line in git("log", "--reverse", "--format=%H %ct", "origin/main", "--", LEDGER).splitlines():
    commit, date = line.split()
    date = int(date)
    ledger = json.loads(git("show", f"{commit}:{LEDGER}"))
    current_batches = batches(ledger)
    current_hourly = hourly_passwords(ledger)
    new = sorted(set(current_batches) - set(previous_batches))
    if date < cutoff:
        # Only the last accepted batch of the run survived the clone.
        decoys = [key for key in new if current_batches[key] == DECOY]
        if new and current_batches[new[-1]] == DECOY and current_hourly:
            contributions.append((commit, f"batch {new[-1]}", current_hourly))
            lost += decoys[:-1]
        elif contributions:
            lost += decoys  # passwords were captured by then but did not survive
    elif new:
        delta = difference(current_hourly, previous_hourly)
        if delta:
            contributions.append((commit, f"run adding {len(new)} batches", delta))
    previous_batches = current_batches
    previous_hourly = current_hourly

ledger = json.loads(git("show", f"origin/main:{LEDGER}"))
periods = ledger["periods"]
for period in periods.values():
    period.pop("passwords", None)
    period.pop("passwords_overflow", None)

total = 0
overflowed = 0
for commit, description, hours in contributions:
    for hourly_key, (values, overflow) in sorted(hours.items()):
        hour = hourly_key.split("\x00", 1)[1]
        for key in (hourly_key, "daily\x00" + hour[:10], "monthly\x00" + hour[:7], "yearly\x00" + hour[:4]):
            if key not in periods:
                if key == hourly_key:
                    continue  # hourly period already pruned
                raise SystemExit(f"missing period {key!r}")
            period = periods[key]
            target = period.setdefault("passwords", {})
            for value, count in values.items():
                if value not in target and len(target) >= MAX_VALUES:
                    period["passwords_overflow"] = period.get("passwords_overflow", 0) + count
                    overflowed += count if key.startswith("daily") else 0
                else:
                    target[value] = target.get(value, 0) + count
            if overflow:
                period["passwords_overflow"] = period.get("passwords_overflow", 0) + overflow
        total += sum(values.values()) + overflow

with open(out_path, "w") as output:
    json.dump(ledger, output, separators=(",", ":"))
    output.write("\n")
print(f"contributions replayed: {len(contributions)}")
print(f"decoy batches not recoverable: {len(lost)} {[key[2] for key in lost]}")
print(f"password attempts restored: {total} (daily overflow: {overflowed})")
