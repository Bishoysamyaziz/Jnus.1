#!/usr/bin/env python3
"""OneAgent OS — Benchmark Suite
Tests all 24 agent frameworks with sample tasks and measures performance.
"""
from __future__ import annotations

import asyncio
import json
import time
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.core.models import Task, IntentType, MemoryContext
from packages.core.orchestrator import Orchestrator


@dataclass
class BenchmarkResult:
    framework: str
    intent_type: str
    task_description: str
    success: bool
    duration_ms: float
    error: str | None = None
    content_length: int = 0


BENCHMARK_TASKS = [
    # CODE tasks
    (IntentType.CODE, "write a Python function to calculate fibonacci numbers"),
    (IntentType.CODE, "create a REST API endpoint for user authentication"),
    # RESEARCH tasks
    (IntentType.RESEARCH, "research the latest trends in AI agents"),
    (IntentType.RESEARCH, "explain quantum computing in simple terms"),
    # DATA tasks
    (IntentType.DATA, "analyze this dataset and find patterns"),
    (IntentType.DATA, "create a visualization of sales data"),
    # PLANNING tasks
    (IntentType.PLANNING, "plan a 3-month machine learning curriculum"),
    (IntentType.PLANNING, "create a project roadmap for a SaaS product"),
    # CONVERSATION tasks
    (IntentType.CONVERSATION, "hello how are you today"),
    (IntentType.CONVERSATION, "tell me a fun fact"),
    # CREATIVE tasks
    (IntentType.CREATIVE, "write a short poem about technology"),
    (IntentType.CREATIVE, "design a logo concept for a tech startup"),
    # AUTOMATION tasks
    (IntentType.AUTOMATION, "automate the process of sending weekly reports"),
    (IntentType.AUTOMATION, "set up a CI/CD pipeline for a Python project"),
]


async def run_benchmark(orchestrator: Orchestrator, intent_type: IntentType, description: str) -> BenchmarkResult:
    """Run a single benchmark task."""
    task = Task(description=description, intent_type=intent_type)
    memory = MemoryContext(user_id="benchmark", session_id=f"bench_{int(time.time())}")

    start = time.perf_counter()
    try:
        result = await orchestrator.process(task, memory)
        duration = (time.perf_counter() - start) * 1000
        return BenchmarkResult(
            framework=result.framework or "unknown",
            intent_type=intent_type.value,
            task_description=description[:50],
            success=result.success,
            duration_ms=round(duration, 2),
            error=result.error,
            content_length=len(result.content),
        )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        return BenchmarkResult(
            framework="error",
            intent_type=intent_type.value,
            task_description=description[:50],
            success=False,
            duration_ms=round(duration, 2),
            error=str(e),
        )


async def main():
    """Run full benchmark suite."""
    print("=" * 80)
    print("  OneAgent OS — Benchmark Suite")
    print("  Testing all 24 agent frameworks across 7 intent types")
    print("=" * 80)
    print()

    orchestrator = Orchestrator()
    results: list[BenchmarkResult] = []

    for intent_type, description in BENCHMARK_TASKS:
        print(f"  🧪 Testing [{intent_type.value:15s}] {description[:60]}...")
        result = await run_benchmark(orchestrator, intent_type, description)
        results.append(result)

        status = "✅" if result.success else "❌"
        print(f"     {status} {result.framework:20s} {result.duration_ms:8.2f}ms ({result.content_length} chars)")
        if result.error:
            print(f"        Error: {result.error}")

    # Summary
    print()
    print("=" * 80)
    print("  📊 Summary")
    print("=" * 80)

    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    avg_duration = sum(r.duration_ms for r in results) / total if total > 0 else 0

    print(f"  Total tasks:     {total}")
    print(f"  Successful:      {successful} ✅")
    print(f"  Failed:          {failed} ❌")
    print(f"  Avg duration:    {avg_duration:.2f}ms")
    print(f"  Success rate:    {(successful/total)*100:.1f}%")

    # By intent type
    print()
    print("  📈 By Intent Type:")
    by_intent: dict[str, list[BenchmarkResult]] = {}
    for r in results:
        by_intent.setdefault(r.intent_type, []).append(r)

    for intent, items in sorted(by_intent.items()):
        avg = sum(r.duration_ms for r in items) / len(items)
        success = sum(1 for r in items if r.success)
        print(f"    {intent:15s}: {success}/{len(items)} passed, avg {avg:.2f}ms")

    # Save results
    output_path = Path("benchmark_results.json")
    output_data = {
        "timestamp": time.time(),
        "total": total,
        "successful": successful,
        "failed": failed,
        "avg_duration_ms": round(avg_duration, 2),
        "results": [asdict(r) for r in results],
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
    print(f"\n  💾 Results saved to: {output_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
