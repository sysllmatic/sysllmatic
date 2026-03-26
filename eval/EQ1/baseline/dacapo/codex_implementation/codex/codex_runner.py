#!/usr/bin/env python3
"""
Run Codex directly with the optimization prompt while tracking usage and cost.
"""
import argparse
import json
import os
import subprocess
import sys
import textwrap
import time
from typing import Dict, List, Optional


DEFAULT_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "default_prompt.txt")
DEFAULT_TEMPERATURE = "0.7"
CODEX_DIR = os.path.dirname(__file__)
APPLY_PATCH_WRAPPER = os.path.join(CODEX_DIR, "apply_patch")


def log(message: str) -> None:
    print(f"[codex_runner] {message}")


def parse_key_value(items: List[str], label: str) -> Dict[str, str]:
    env = {}
    for raw in items or []:
        if "=" not in raw:
            raise ValueError(f"{label} must be KEY=VALUE, got: {raw}")
        key, value = raw.split("=", 1)
        if not key:
            raise ValueError(f"{label} must have a non-empty key: {raw}")
        env[key] = value
    return env


def load_env_file(path: str) -> Dict[str, str]:
    env = {}
    if not os.path.isfile(path):
        return env
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"Invalid .env line: {line}")
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip("'").strip('"')
    return env


def build_prompt(path: str, custom: Optional[str]) -> str:
    if custom:
        base = custom
    else:
        base = read_instructions_file(DEFAULT_PROMPT_PATH)
    base = textwrap.dedent(base).strip()
    base = base.format(path=path)

    tool_block = load_apply_patch_instructions()
    if tool_block:
        base = f"{base}\n\n{tool_block}"
    return base


def load_apply_patch_instructions() -> Optional[str]:
    try:
        from apply_patch_runner import APPLY_PATCH_TOOL, APPLY_PATCH_TOOL_DESC
    except Exception as exc:
        log(f"apply_patch tool info unavailable: {exc}")
        return None

    desc_lines = [
        line for line in APPLY_PATCH_TOOL_DESC.splitlines() if line.strip() != "%%bash"
    ]
    desc = "\n".join(desc_lines).strip()
    tool_json = json.dumps(APPLY_PATCH_TOOL, indent=2, sort_keys=True)
    return "\n".join(
        [
            "APPLY_PATCH TOOL",
            "================",
            "The apply_patch command is available on PATH for diff-style edits.",
            "",
            desc,
            "",
            "Tool definition (JSON):",
            tool_json,
        ]
    )


def build_codex_command(
    codex_bin: str,
    working_dir: str,
    model: Optional[str],
    sandbox: str,
    extra_args: List[str],
    prompt: str,
) -> List[str]:
    cmd = [codex_bin, "exec", "--json", "--cd", working_dir, "--sandbox", sandbox]
    if model:
        cmd += ["--model", model]
    cmd += extra_args
    cmd.append(prompt)
    return cmd


def read_instructions_file(path: str) -> str:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def main():
    parser = argparse.ArgumentParser(
        description="Run Codex on a target path with the optimization prompt and track costs."
    )
    parser.add_argument("path", help="Path to the project to optimize")
    parser.add_argument("--prompt", help="Override the default optimization prompt")
    parser.add_argument("--instructions-file", help="File whose contents will be appended to the prompt")
    parser.add_argument("--model", help="Codex model to use (optional)")
    parser.add_argument(
        "--sandbox",
        default="workspace-write",
        help="Sandbox policy passed to Codex (default: workspace-write)",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to a .env file containing API keys or environment overrides",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        help="Additional environment variables KEY=VALUE (repeatable)",
    )
    parser.add_argument(
        "--codex",
        default="codex",
        help="Path to the codex CLI binary",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the Codex command without executing it",
    )
    parser.add_argument(
        "--codex-arg",
        action="append",
        default=[],
        help="Additional arguments forwarded directly to the codex CLI",
    )
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)
    if not os.path.isdir(target_path):
        print(f"Invalid path or not a directory: {target_path}", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env_file_present = os.path.isfile(args.env_file)
    try:
        env.update(load_env_file(args.env_file))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        env.update(parse_key_value(args.set, "--set"))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if "OPENAI_TEMPERATURE" not in env:
        env["OPENAI_TEMPERATURE"] = DEFAULT_TEMPERATURE
    env["PATH"] = f"{CODEX_DIR}{os.pathsep}{env.get('PATH', '')}"

    model = args.model

    instructions_text = None
    if args.instructions_file:
        try:
            log(f"reading instructions file: {args.instructions_file}")
            instructions_text = read_instructions_file(args.instructions_file)
        except FileNotFoundError:
            print(f"instructions file not found: {args.instructions_file}", file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"failed to read instructions file: {exc}", file=sys.stderr)
            return 2

    log("building prompt")
    prompt = build_prompt(target_path, args.prompt)
    if instructions_text:
        prompt = f"{prompt}\n\nADDITIONAL PROJECT INSTRUCTIONS\n================================\n{instructions_text}"

    log("constructing codex command")
    cmd = build_codex_command(
        codex_bin=args.codex,
        working_dir=target_path,
        model=model,
        sandbox=args.sandbox,
        extra_args=args.codex_arg,
        prompt=prompt,
    )

    print("Run configuration:")
    print(f"- project_path: {target_path}")
    print(f"- codex_bin: {args.codex}")
    print(f"- model: {model or 'default'}")
    print(f"- sandbox: {args.sandbox}")
    print(f"- env_file: {args.env_file} ({'present' if env_file_present else 'missing'})")
    print(f"- prompt_source: {'cli' if args.prompt else 'default'}")
    if args.instructions_file:
        print(f"- instructions_file: {args.instructions_file}")
        
    print(f"OPENAI_TEMPERATURE effective value: {env.get('OPENAI_TEMPERATURE')}")

    if args.dry_run:
        print(" ".join(cmd))
        return 0

    log("launching codex")
    start = time.time()

    stdout_lines: list[str] = []
    completed_stderr = ""

    process = subprocess.Popen(
        cmd,
        cwd=target_path,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,   # merge stderr into stdout so you see everything live
        text=True,
        bufsize=1,                 # line-buffered
    )

    try:
        assert process.stdout is not None
        for line in process.stdout:
            # stream live
            print(line, end="")
            # keep for post-processing
            stdout_lines.append(line.rstrip("\n"))
        returncode = process.wait()
    except Exception:
        process.kill()
        process.wait()
        raise

    duration = time.time() - start

    if returncode != 0:
        # since we merged stderr into stdout, we don't have exc.stderr;
        # return non-zero and you already saw logs live
        return returncode

    # No separate stderr anymore (it was merged into stdout)
    # If you want stderr separate, see note below.

    print(f"duration_seconds: {duration}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
