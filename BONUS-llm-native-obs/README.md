# BONUS — LLM-Native Observability (Langfuse)

Self-hosted Langfuse for capturing and inspecting LLM traces with GenAI semantic conventions.

## Quick start

```bash
# 1. Start Langfuse + Postgres (2 containers)
docker compose -f BONUS-llm-native-obs/docker-compose.langfuse.yml up -d

# Wait ~15s for Langfuse to initialize
docker logs day23-langfuse -f

# 2. Install Python SDK
pip install langfuse

# 3. Generate a LangChain-style trace
python BONUS-llm-native-obs/langfuse-trace.py

# 4. Open Langfuse UI
open http://localhost:3001
```

## What the trace shows

The generated trace simulates a RAG (Retrieval-Augmented Generation) pipeline:

```
langchain-qa-pipeline (trace)
├── retrieval (span) — vector search returning 3 documents
└── generation (span) — LLM call with GenAI semantic attrs
```

Each span carries:
- **I/O**: input query, retrieved documents, LLM response
- **Metadata**: `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.response.finish_reason`
- **Latency**: per-span duration
- **Cost tracking**: token counts can be mapped to $ via Langfuse's built-in model pricing table

## Langfuse vs. Jaeger

| Aspect | Jaeger (Track 03) | Langfuse (Bonus) |
|---|---|---|
| Focus | Distributed system traces | LLM call traces |
| Span semantics | HTTP/gRPC calls | Prompt → retrieval → generation |
| Token counting | Via manual span attrs | Built-in (auto-extracted) |
| Cost estimation | Manual PromQL math | Built-in pricing table |
| User feedback | Not applicable | Score annotations (thumbs up/down) |

## Scoring (bonus)

- Start Langfuse: `docker compose -f BONUS-llm-native-obs/docker-compose.langfuse.yml up -d`
- In the Langfuse UI, navigate to Traces → click the trace → screenshot the nested span view
- Save screenshot: `submission/screenshots/langfuse-trace.png`

## Cleanup

```bash
docker compose -f BONUS-llm-native-obs/docker-compose.langfuse.yml down -v
```
