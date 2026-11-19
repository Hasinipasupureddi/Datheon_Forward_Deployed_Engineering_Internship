# Task 4 - Local Latency Benchmark

Date: 19 November 2026
Environment: Local Docker deployment
LLM: Ollama qwen2.5:3b

## Health Endpoint
- Requests: 10
- Average latency: 2.69 ms
- Minimum latency: 2.13 ms
- Maximum latency: 4.76 ms

## RAG Query Endpoint
- Requests: 3
- Successful grounded queries: 3/3
- Average latency: 13,540.13 ms
- Minimum latency: 5,424.27 ms
- Maximum latency: 29,671.86 ms

## Notes
- Results are from a local test environment.
- RAG latency includes retrieval, reranking and LLM generation.
- Results are indicative and are not production performance guarantees.
