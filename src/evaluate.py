import json
import statistics
from pathlib import Path


def load_events(log_dir="logs"):
    events = []
    for log_file in Path(log_dir).glob("*.log"):
        for line in log_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def main():
    events = load_events()
    llm_metrics = [event["data"] for event in events if event.get("event") == "LLM_METRIC"]
    tool_calls = [event for event in events if event.get("event") == "TOOL_CALL"]
    parse_errors = [event for event in events if event.get("event") == "AGENT_PARSE_ERROR"]
    tool_not_found = [event for event in events if event.get("event") == "TOOL_NOT_FOUND"]
    agent_end = [event for event in events if event.get("event") == "AGENT_END"]

    latencies = [m.get("latency_ms", 0) for m in llm_metrics]
    tokens = [m.get("total_tokens", 0) for m in llm_metrics]
    total_cost = sum(m.get("cost_estimate", 0) for m in llm_metrics)

    print("=== Lab 3 Evaluation Summary ===")
    print(f"LLM calls: {len(llm_metrics)}")
    print(f"Tool calls: {len(tool_calls)}")
    print(f"Parse errors: {len(parse_errors)}")
    print(f"Tool-not-found errors: {len(tool_not_found)}")
    print(f"Agent runs ended: {len(agent_end)}")

    if latencies:
        print(f"Average latency: {round(statistics.mean(latencies), 2)} ms")
        print(f"Max latency: {max(latencies)} ms")

    if tokens:
        print(f"Average tokens/call: {round(statistics.mean(tokens), 2)}")
        print(f"Total tokens: {sum(tokens)}")

    print(f"Estimated cost: ${round(total_cost, 6)}")


if __name__ == "__main__":
    main()
