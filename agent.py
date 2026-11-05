"""The agent loop: one function that runs any agent using Claude tool use."""
import datetime
import json
import os
import time

import anthropic

from config import MODEL
from tools import TOOLS, run_tool

_client = None


def get_client():
    global _client
    if _client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise SystemExit(
                "\nNo ANTHROPIC_API_KEY found.\n"
                "Copy .env.example to .env and paste your key after ANTHROPIC_API_KEY=\n")
        _client = anthropic.Anthropic()
    return _client


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def run_agent(agent_name, system_prompt, task, use_tools=True, max_turns=15, on_event=None):
    """Run one agent until it gives a final answer.

    Returns (final_text, evidence, stats).
      evidence: every tool call (agent, tool, input, raw output, time) = the audit trail
      stats:    what the agent did (time taken, tool calls, tools used, tokens, status)
    on_event:   optional callback, called with a dict whenever the agent starts,
                calls a tool, or finishes (used for the dashboard's live banner)
    """
    emit = on_event or (lambda event: None)
    started = time.time()
    messages = [{"role": "user", "content": task}]
    evidence = []
    tokens_in = tokens_out = turns = 0
    emit({"agent": agent_name, "action": "thinking", "detail": "reading the task"})

    def stats(status):
        return {"status": status, "seconds": round(time.time() - started, 1),
                "tool_calls": len(evidence),
                "tools_used": sorted({e["tool"] for e in evidence}),
                "input_tokens": tokens_in, "output_tokens": tokens_out, "turns": turns,
                "finished_at": now()}

    for _ in range(max_turns):
        kwargs = dict(model=MODEL, max_tokens=4000, system=system_prompt, messages=messages)
        if use_tools:
            kwargs["tools"] = TOOLS
        response = get_client().messages.create(**kwargs)
        turns += 1
        usage = getattr(response, "usage", None)
        tokens_in += getattr(usage, "input_tokens", 0) or 0
        tokens_out += getattr(usage, "output_tokens", 0) or 0
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":  # Claude is done
            text = "".join(b.text for b in response.content if b.type == "text").strip()
            emit({"agent": agent_name, "action": "finished", "detail": ""})
            return text, evidence, stats("completed")

        results = []
        for block in response.content:
            if block.type == "tool_use":
                emit({"agent": agent_name, "action": "calling tool",
                      "detail": f"{block.name}({json.dumps(block.input)})"})
                output = run_tool(block.name, block.input)
                evidence.append({"agent": agent_name, "tool": block.name, "input": block.input,
                                 "output": output, "at": now()})
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(output, default=str)})
        messages.append({"role": "user", "content": results})

    emit({"agent": agent_name, "action": "stopped", "detail": "too many steps"})
    return "Stopped: the agent used too many steps without finishing.", evidence, stats("stopped")
