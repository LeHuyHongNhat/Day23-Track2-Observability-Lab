"""Generate a LangChain-style LLM trace and push it to self-hosted Langfuse.

Captures a full trace with nested observation spans simulating:
  retrieval (vector-search) → generation (LLM call)

GenAI semantic convention attributes are set on the generation span.

Usage:
  pip install langfuse
  python BONUS-llm-native-obs/langfuse-trace.py
"""
from __future__ import annotations

import os
import time
import uuid

# Point at the self-hosted Langfuse instance
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-00000000-0000-0000-0000-000000000000"
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-00000000-0000-0000-0000-000000000000"
os.environ["LANGFUSE_HOST"] = "http://localhost:3001"


def main() -> int:
    try:
        from langfuse import Langfuse
    except ImportError:
        print(
            "langfuse not installed. Run: pip install langfuse"
        )
        return 1

    langfuse = Langfuse()

    trace_id = uuid.uuid4().hex
    print(f"Creating trace: {trace_id}")

    trace = langfuse.trace(
        id=trace_id,
        name="langchain-qa-pipeline",
        metadata={"framework": "langchain", "pipeline": "rag-qa"},
        tags=["day23-bonus", "llm-native-obs"],
    )

    # Span 1 — retrieval (vector search)
    retrieval = trace.span(
        name="retrieval",
        input={"query": "What is SLO burn-rate alerting?"},
        metadata={"vector_store": "qdrant", "k": 5, "collection": "docs"},
    )
    time.sleep(0.05)  # simulate retrieval latency
    retrieval.end(
        output={
            "documents": [
                {"id": "doc-001", "score": 0.92, "source": "sre-workbook-ch5"},
                {"id": "doc-002", "score": 0.87, "source": "google-sre-book"},
                {"id": "doc-003", "score": 0.81, "source": "observability-eng"},
            ]
        }
    )

    # Span 2 — generation (LLM call with GenAI semantic conventions)
    generation = trace.span(
        name="generation",
        input={
            "messages": [
                {"role": "system", "content": "You are an SRE assistant."},
                {
                    "role": "user",
                    "content": "What is SLO burn-rate alerting?",
                },
            ]
        },
        metadata={
            "gen_ai.system": "langchain",
            "gen_ai.request.model": "llama3-8b-instruct",
            "gen_ai.request.max_tokens": 256,
            "gen_ai.request.temperature": 0.7,
        },
    )
    time.sleep(0.15)  # simulate generation latency
    generation.end(
        output={
            "role": "assistant",
            "content": "SLO burn-rate alerting is a method from the Google SRE workbook that "
            "triggers alerts when your error budget is being consumed faster than "
            "planned. It uses multi-window multi-burn-rate thresholds: a fast burn "
            "(14.4× normal rate over 5m + 1h) pages immediately, while a slow burn "
            "(6× over 30m + 6h) warns about gradual degradation before it consumes "
            "the entire 30-day budget.",
        },
        metadata={
            "gen_ai.usage.input_tokens": 42,
            "gen_ai.usage.output_tokens": 89,
            "gen_ai.response.finish_reason": "stop",
            "gen_ai.response.model": "llama3-8b-instruct",
        },
    )

    # Update trace with overall I/O
    trace.update(
        input={"user_query": "What is SLO burn-rate alerting?"},
        output={
            "answer": "SLO burn-rate alerting triggers on error budget consumption rate...",
            "sources": ["doc-001", "doc-002", "doc-003"],
        },
        metadata={
            "total_tokens": 131,
            "pipeline_latency_ms": 210,
            "quality_score": 0.91,
        },
    )

    langfuse.flush()
    print(f"Trace pushed to Langfuse at http://localhost:3001")
    print(f"Trace ID: {trace_id}")
    print(
        "Open http://localhost:3001 → Traces to see the full trace with nested spans."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
