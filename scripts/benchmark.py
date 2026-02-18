"""LLM inference benchmark runner using AIPerf.

Wraps `aiperf profile` to run standardized benchmarks against
OpenAI-compatible endpoints (vLLM, TRT-LLM, NIM).

Usage:
    uv run scripts/benchmark.py \
        --model Qwen/Qwen3-Coder-30B-A3B-Instruct \
        --concurrency 1,2,4

    uv run scripts/benchmark.py \
        --model nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 \
        --port 8001
"""

from __future__ import annotations

import argparse
import subprocess
import sys


DEFAULT_PORT = 8000
DEFAULT_CONCURRENCY = [1]
DEFAULT_INPUT_TOKENS = 200
DEFAULT_OUTPUT_TOKENS = 200
DEFAULT_NUM_REQUESTS = 10


def build_aiperf_cmd(
    *,
    model: str,
    port: int,
    concurrency: int,
    input_tokens: int,
    output_tokens: int,
    num_requests: int,
) -> list[str]:
    return [
        sys.executable, "-m", "aiperf",
        "profile",
        "-m", model,
        "--endpoint-type", "chat",
        "--streaming",
        "-u", f"localhost:{port}",
        "--synthetic-input-tokens-mean", str(input_tokens),
        "--output-tokens-mean", str(output_tokens),
        "--concurrency", str(concurrency),
        "--request-count", str(num_requests),
    ]


def run_benchmark(
    *,
    model: str,
    port: int,
    concurrency_levels: list[int],
    input_tokens: int,
    output_tokens: int,
    num_requests: int,
) -> None:
    for concurrency in concurrency_levels:
        print(f"\n{'='*60}")
        print(f"Model: {model}")
        print(f"Concurrency: {concurrency}")
        print(f"Input tokens: {input_tokens}, Output tokens: {output_tokens}")
        print(f"Requests: {num_requests}")
        print(f"{'='*60}\n")

        cmd = build_aiperf_cmd(
            model=model,
            port=port,
            concurrency=concurrency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            num_requests=num_requests,
        )

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"[ERROR] aiperf exited with code {result.returncode}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run LLM inference benchmarks using AIPerf",
    )
    parser.add_argument(
        "--model", "-m",
        required=True,
        help="Model name (must match served-model-name)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"Server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--concurrency", "-c",
        default=",".join(str(c) for c in DEFAULT_CONCURRENCY),
        help="Comma-separated concurrency levels (default: 1)",
    )
    parser.add_argument(
        "--input-tokens",
        type=int,
        default=DEFAULT_INPUT_TOKENS,
        help=f"Mean synthetic input token count (default: {DEFAULT_INPUT_TOKENS})",
    )
    parser.add_argument(
        "--output-tokens",
        type=int,
        default=DEFAULT_OUTPUT_TOKENS,
        help=f"Mean output token count (default: {DEFAULT_OUTPUT_TOKENS})",
    )
    parser.add_argument(
        "--num-requests", "-n",
        type=int,
        default=DEFAULT_NUM_REQUESTS,
        help=f"Number of requests (default: {DEFAULT_NUM_REQUESTS})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    concurrency_levels = [int(c) for c in args.concurrency.split(",")]

    run_benchmark(
        model=args.model,
        port=args.port,
        concurrency_levels=concurrency_levels,
        input_tokens=args.input_tokens,
        output_tokens=args.output_tokens,
        num_requests=args.num_requests,
    )


if __name__ == "__main__":
    main()
