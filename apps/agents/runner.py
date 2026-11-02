"""The tool loop every agent runs through, with its guardrails.

    from apps.agents.runner import Tool, run

    outcome = run("support-agent", client, system=..., prompt=..., tools=[...],
                  purpose="support:conversation:12")

run() calls the model, runs the tools it asks for and passes back their
results, until it calls a tool marked final (an agent's way of saying what
it decided: reply, escalate, draft) or answers in plain text, or runs out
of turns.  Around each step:

- the whole run is credited to the agent in the audit log
  (apps.audit.acting_as_agent): any model change it makes, and the jobs it
  queues;
- before each call, budget.check() refuses one that would pass the
  monthly cap (BudgetExceeded); after it, budget.record() keeps the cost
  and the audit log gets "agents.ai_call";
- each tool call is recorded ("agents.tool_call", with its input); a
  tool that raises gives the model an error result, and is logged;
- only the tools given exist: a name the model makes up gets an error.

Give agents read-only tools wherever possible, and make tools check what
the person may see themselves: the model's choice of input is untrusted.
"""

import json
import logging
from dataclasses import dataclass, field

from apps.audit import acting_as_agent, record

from . import budget
from .ai import estimate_tokens
from .untrusted import UNTRUSTED_RULES

log = logging.getLogger(__name__)

MAX_RESULT_CHARS = 6000


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    fn: object  # fn(**input) -> JSON-able result; not called for final tools
    properties: dict = field(default_factory=dict)  # JSON-schema properties
    required: tuple = ()
    final: bool = False  # calling it ends the run with its input as the outcome

    def spec(self):
        return {"name": self.name, "description": self.description,
                "input_schema": {"type": "object", "properties": self.properties, "required": list(self.required)}}

    def validate(self, tool_input):
        """A problem with the input in words, or ""."""
        if not isinstance(tool_input, dict):
            return "input must be an object"
        missing = [name for name in self.required if name not in tool_input]
        if missing:
            return "missing " + ", ".join(missing)
        unknown = [name for name in tool_input if name not in self.properties]
        if unknown:
            return "unknown " + ", ".join(unknown)
        for name, value in tool_input.items():
            kind = self.properties[name].get("type")
            if kind == "string" and not isinstance(value, str):
                return f"{name} must be a string"
            if kind == "string" and "enum" in self.properties[name] and value not in self.properties[name]["enum"]:
                return f"{name} must be one of " + ", ".join(self.properties[name]["enum"])
        return ""


@dataclass
class Outcome:
    final: str = ""  # the final tool's name, or "" if it stopped otherwise
    input: dict = field(default_factory=dict)
    text: str = ""  # any plain text the model ended with
    turns: int = 0
    stopped: str = ""  # why it stopped without a final tool: "text", "turns"


def string(description, **extra):
    return {"type": "string", "description": description, **extra}


def _result_text(result):
    text = result if isinstance(result, str) else json.dumps(result, default=str, ensure_ascii=False)
    return text if len(text) <= MAX_RESULT_CHARS else text[:MAX_RESULT_CHARS] + " [... cut]"


def _run_tool(agent, tool, tool_input, purpose):
    problem = tool.validate(tool_input)
    if problem:
        record("agents.tool_refused", message=f"{agent} {tool.name}: {problem}", object_repr=purpose)
        return {"error": problem}, True
    record("agents.tool_call", message=f"{tool.name}", object_repr=purpose,
           changes={"input": {k: str(v)[:200] for k, v in tool_input.items()}})
    try:
        return tool.fn(**tool_input), False
    except Exception:
        log.exception("%s: tool %s failed with %r", agent, tool.name, tool_input)
        return {"error": "the tool failed; don't retry it"}, True


def run(agent, client, *, system, prompt, tools, purpose="", max_turns=6, max_tokens=800):
    """Run the agent to its decision; see the module docstring.  Raises
    budget.BudgetExceeded, and the client's AIError / AIUnavailable."""
    by_name = {tool.name: tool for tool in tools}
    specs = [tool.spec() for tool in tools]
    system = f"{system.strip()}\n\n{UNTRUSTED_RULES}"
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    model = getattr(client, "model", "")
    with acting_as_agent(agent):
        for turn in range(1, max_turns + 1):
            budget.check(agent, model, estimate_tokens([system, messages, specs]), max_tokens)
            reply = client.complete(system=system, messages=messages, tools=specs, max_tokens=max_tokens)
            usage = budget.record(agent, reply, purpose)
            record("agents.ai_call", message=f"{reply.model}: {reply.input_tokens} in, {reply.output_tokens} out, "
                   f"${usage.cost:.4f}", object_repr=purpose)
            messages.append({"role": "assistant", "content": reply.content})
            calls = reply.tool_calls
            if not calls:
                return Outcome(text=reply.text, turns=turn, stopped="text")
            results = []
            for call in calls:
                tool = by_name.get(call.get("name"))
                if tool is None:
                    record("agents.tool_refused", message=f"{agent}: no tool {call.get('name')!r}",
                           object_repr=purpose)
                    results.append({"type": "tool_result", "tool_use_id": call.get("id"),
                                    "content": "No such tool.", "is_error": True})
                    continue
                if tool.final:
                    problem = tool.validate(call.get("input"))
                    if not problem:
                        record("agents.decided", message=tool.name, object_repr=purpose,
                               changes={"input": {k: str(v)[:500] for k, v in call["input"].items()}})
                        return Outcome(final=tool.name, input=call["input"], text=reply.text, turns=turn)
                    result, is_error = {"error": problem}, True
                else:
                    result, is_error = _run_tool(agent, tool, call.get("input"), purpose)
                results.append({"type": "tool_result", "tool_use_id": call.get("id"),
                                "content": _result_text(result), "is_error": is_error})
            messages.append({"role": "user", "content": results})
        record("agents.gave_up", message=f"{agent}: no decision after {max_turns} turns", object_repr=purpose)
        return Outcome(turns=max_turns, stopped="turns")
