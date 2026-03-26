#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter
from pathlib import Path

ANSI_RE = re.compile(r"\x1B\[[0-9;]*[A-Za-z]")
ERROR_KEYWORDS = [
    "error",
    "fail",
    "traceback",
    "exception",
    "unable",
    "denied",
    "not successful",
    "no module named",
    "could not",
    "detected jdk version",
    "not found",
    "permission",
]
INPUT_COST_PER_M = 1.75
CACHED_INPUT_COST_PER_M = 0.175
OUTPUT_COST_PER_M = 14.00


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def parse_json_objects(blob: str):
    decoder = json.JSONDecoder()
    idx = 0
    length = len(blob)
    while idx < length:
        if blob[idx] != "{":
            idx += 1
            continue
        try:
            obj, end = decoder.raw_decode(blob, idx)
        except json.JSONDecodeError:
            idx += 1
            continue
        yield obj
        idx = end


def pick_highlights(lines, limit=3):
    highlights = []
    seen = set()

    def add(line):
        stripped = line.strip()
        if stripped and stripped not in seen:
            highlights.append(stripped)
            seen.add(stripped)
    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in ERROR_KEYWORDS):
            add(line)
            if len(highlights) >= limit:
                return highlights
    for line in lines:
        add(line)
        if len(highlights) >= limit:
            break
    return highlights


def extract_optimizations(summary_text: str):
    if not summary_text:
        return []
    lines = summary_text.splitlines()
    in_section = False
    optimizations = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == "**optimizations**":
            in_section = True
            continue
        if in_section and stripped.startswith("**") and stripped.endswith("**"):
            break
        if in_section:
            if not stripped:
                continue
            if stripped.startswith("-"):
                optimizations.append(stripped.lstrip("- ").strip())
    return optimizations


def calculate_cost(usage: dict) -> dict:
    input_tokens = usage.get("input_tokens", 0)
    cached_input_tokens = usage.get("cached_input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_M
    cached_input_cost = (cached_input_tokens / 1_000_000) * CACHED_INPUT_COST_PER_M
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_M

    total_cost = input_cost + cached_input_cost + output_cost

    return {
        "input_cost": input_cost,
        "cached_input_cost": cached_input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }


def summarize(log_path: Path):
    blob = log_path.read_text()
    lines = [line.strip() for line in blob.splitlines()]
    runner_messages = [line for line in lines if line.startswith("[codex_runner]")]

    commands = []
    build_events = []
    failures = []
    error_counter = Counter()
    changed_files = set()
    final_summary = None
    usage = None

    for obj in parse_json_objects(blob):
        if obj.get("type") == "turn.completed" and obj.get("usage"):
            usage = obj.get("usage")
        if obj.get("type") != "item.completed":
            continue
        item = obj.get("item", {})
        item_type = item.get("type")
        if item_type == "command_execution":
            command = item.get("command", "<unknown>")
            exit_code = item.get("exit_code")
            output = strip_ansi(item.get("aggregated_output", ""))
            output_lines = [line.strip() for line in output.splitlines() if line.strip()]
            commands.append({
                "command": command,
                "exit_code": exit_code,
                "status": item.get("status"),
                "lines": output_lines,
            })
            upper_lines = [line.upper() for line in output_lines]
            for idx, upper in enumerate(upper_lines):
                if "BUILD SUCCESS" in upper:
                    detail = output_lines[idx + 1] if idx + 1 < len(output_lines) else ""
                    build_events.append({"status": "success", "command": command, "detail": detail})
                elif "BUILD FAIL" in upper:
                    detail = output_lines[idx + 1] if idx + 1 < len(output_lines) else ""
                    build_events.append({"status": "failure", "command": command, "detail": detail})
            if exit_code and exit_code != 0:
                highlights = pick_highlights(output_lines)
                failures.append({
                    "command": command,
                    "exit_code": exit_code,
                    "highlights": highlights,
                })
                for line in highlights:
                    error_counter[line] += 1
        elif item_type == "file_change":
            for change in item.get("changes", []):
                path = change.get("path")
                if path:
                    changed_files.add(path)
        elif item_type == "agent_message":
            text = item.get("text")
            if text:
                final_summary = text

    total = len(commands)
    successes = sum(1 for cmd in commands if not cmd["exit_code"])
    failed = total - successes
    optimizations = extract_optimizations(final_summary or "")

    summary_lines = []
    summary_lines.append(f"Log Summary for {log_path}")
    summary_lines.append("=" * 80)
    summary_lines.append(f"Commands executed: {total} (success: {successes}, failed: {failed})")
    summary_lines.append(f"Tool calls (command executions): {total}")
    summary_lines.append(f"Files changed: {len(changed_files)}")
    summary_lines.append(f"Optimizations described: {len(optimizations)}")
    if runner_messages:
        summary_lines.append("Initial codex_runner messages:")
        for msg in runner_messages[:5]:
            summary_lines.append(f"  - {msg}")
        if len(runner_messages) > 5:
            summary_lines.append(f"  - ... and {len(runner_messages) - 5} more")
    if build_events:
        success_builds = sum(1 for evt in build_events if evt["status"] == "success")
        failed_builds = len(build_events) - success_builds
        summary_lines.append(
            f"Build attempts mentioned in logs: {len(build_events)} "
            f"({success_builds} success, {failed_builds} failure)"
        )
        for evt in build_events:
            detail = f" -> {evt['detail']}" if evt["detail"] else ""
            summary_lines.append(f"  - {evt['status'].title()} via {evt['command']}{detail}")
    if failures:
        summary_lines.append("Failed commands:")
        for failure in failures:
            summary_lines.append(f"  - {failure['command']} (exit {failure['exit_code']})")
            for line in failure["highlights"]:
                summary_lines.append(f"      - {line}")
    if error_counter:
        summary_lines.append("Most frequent error snippets:")
        for line, count in error_counter.most_common(5):
            summary_lines.append(f"  - [{count}x] {line}")
    if changed_files:
        summary_lines.append("Files touched:")
        for path in sorted(changed_files):
            summary_lines.append(f"  - {path}")
    if optimizations:
        summary_lines.append("Optimization bullets:")
        for line in optimizations:
            summary_lines.append(f"  - {line}")
    if final_summary:
        summary_lines.append("Final agent summary from log:")
        for line in final_summary.strip().splitlines():
            summary_lines.append(f"  {line}")
    if usage:
        costs = calculate_cost(usage)
        summary_lines.append("Usage cost summary:")
        summary_lines.append(f"  Input cost:        ${costs['input_cost']:.4f}")
        summary_lines.append(f"  Cached input cost: ${costs['cached_input_cost']:.4f}")
        summary_lines.append(f"  Output cost:       ${costs['output_cost']:.4f}")
        summary_lines.append("  " + "-" * 30)
        summary_lines.append(f"  Total cost:        ${costs['total_cost']:.4f}")
    return "\n".join(summary_lines)


def main():
    parser = argparse.ArgumentParser(description="Summarize Codex CLI logs")
    parser.add_argument("log_path", nargs="?", default="logs.txt", help="Path to the log file")
    args = parser.parse_args()
    path = Path(args.log_path)
    if not path.exists():
        raise SystemExit(f"Log file {path} does not exist")
    print(summarize(path))


if __name__ == "__main__":
    main()
