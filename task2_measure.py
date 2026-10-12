#!/usr/bin/env python3
"""Measure HTTPS transfer throughput and TCP setup time on one network.

Run once per network label. Each invocation records at least five independent
transfers in ``out/throughput.json``; the same target and response size make
the measurements comparable across labels.
"""
import argparse
import json
import os
import shutil
import statistics
import subprocess
import tempfile
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
TARGET = "https://speed.cloudflare.com/__down?bytes=5000000"
DEFAULT_REPEATS = 5


def one_run():
    """Return curl timing fields for one full 5 MB HTTPS transfer."""
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl is required; install it or add it to PATH")

    fmt = "%{time_namelookup} %{time_connect} %{time_starttransfer} " \
          "%{time_total} %{size_download} %{http_code} %{remote_ip}"
    try:
        result = subprocess.run(
            [curl, "--fail", "--location", "--silent", "--show-error",
             "--connect-timeout", "15", "--max-time", "120",
             "--output", os.devnull, "--write-out", fmt, TARGET],
            capture_output=True, text=True, timeout=125, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("curl exceeded the 125-second safety timeout") from exc

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"curl exited {result.returncode}")
    fields = result.stdout.split()
    if len(fields) != 7:
        raise RuntimeError(f"unexpected curl timing output: {result.stdout!r}")

    dns, connected, first_byte, total, size = map(float, fields[:5])
    status = int(fields[5])
    if status < 200 or status >= 300:
        raise RuntimeError(f"download returned HTTP {status}")
    byte_count = int(size)
    if byte_count <= 0 or total <= 0:
        raise RuntimeError("download returned no bytes or had an invalid duration")

    return {
        "dns_s": dns,
        "connect_s": max(0.0, connected - dns),
        "ttfb_s": max(0.0, first_byte - connected),
        "total_s": total,
        "bytes": byte_count,
        "mbps": byte_count * 8 / total / 1_000_000,
        "http_status": status,
        "remote_ip": fields[6],
    }


def append_record(record):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "throughput.json")
    records = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as stream:
            records = json.load(stream)
        if not isinstance(records, list):
            raise ValueError(f"{path} must contain a JSON array")
    records.append(record)

    fd, temporary = tempfile.mkstemp(prefix="throughput-", suffix=".tmp", dir=OUT)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(records, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path, len(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True,
                        help='network name, e.g. "campus wifi" or "tethering"')
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    args = parser.parse_args()
    if not args.label.strip():
        parser.error("--label must not be empty")
    if args.repeats < 5:
        parser.error("--repeats must be at least 5 to satisfy Task 2")

    runs = []
    for number in range(args.repeats):
        result = one_run()
        runs.append(result)
        print(f"  {number + 1}/{args.repeats}  {result['mbps']:7.2f} Mbps   "
              f"handshake {result['connect_s'] * 1000:6.1f} ms   "
              f"ttfb {result['ttfb_s'] * 1000:6.1f} ms")
        if number + 1 < args.repeats:
            time.sleep(1)

    speeds = [run["mbps"] for run in runs]
    handshakes = [run["connect_s"] * 1000 for run in runs]
    median = statistics.median(speeds)
    record = {
        "label": args.label.strip(),
        "when": datetime.now().astimezone().isoformat(timespec="seconds"),
        "target": TARGET,
        "runs": runs,
        "mbps_median": median,
        "mbps_min": min(speeds),
        "mbps_max": max(speeds),
        "mbps_spread": max(speeds) - min(speeds),
        "mbps_spread_fraction": (max(speeds) - min(speeds)) / median if median else 0,
        "handshake_ms_median": statistics.median(handshakes),
    }
    path, count = append_record(record)
    print(f"\n  {record['label']}: median {median:.2f} Mbps, "
          f"spread {record['mbps_spread_fraction']:.0%} across {args.repeats} runs")
    print(f"  handshake median {record['handshake_ms_median']:.1f} ms")
    print(f"  -> {path} ({count} labelled record(s))")


if __name__ == "__main__":
    main()
