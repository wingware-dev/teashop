"""A stand-in for the AI behind the ops agent: the rules in findings.py in
place of the model, so the daily upkeep runs on a laptop, in tests and on
the server without calling an AI service or spending anything.

It answers in the Claude API's shapes (apps.agents.ai), one tool call per
turn: it applies waiting security updates and rotates logs when the
findings say so, reads the logs, reads the health again after acting,
proposes each larger change the latest findings call for, then reports.
It never acts on log text; only on the parsed numbers in the findings.
"""

import json
import re

from apps.agents.ai import STANDIN_MODEL, Reply, estimate_tokens, tool_use_block

FINDINGS_RE = re.compile(r"FINDINGS_JSON: (\[.*?\])\n", re.DOTALL)
PROPOSED_RE = re.compile(r"ALREADY_PROPOSED_JSON: (\[.*?\])\n", re.DOTALL)
ACTIONS = ("apply_security_updates", "rotate_logs")


def _prompt(messages):
    return messages[0]["content"][0]["text"]


def _calls(messages):
    """[(tool name, input, result)] so far, in order."""
    calls, results = {}, []
    for message in messages:
        for block in message["content"]:
            if block.get("type") == "tool_use":
                calls[block["id"]] = block
            elif block.get("type") == "tool_result" and block.get("tool_use_id") in calls:
                call = calls[block["tool_use_id"]]
                try:
                    value = json.loads(block["content"])
                except (TypeError, ValueError):
                    value = {"error": block.get("content")}
                results.append((call["name"], call["input"], value))
    return results


def _json(pattern, text):
    match = pattern.search(text)
    return json.loads(match[1]) if match else []


def _summary(done, findings):
    parts = []
    for name, _, result in done:
        if result.get("error"):
            parts.append(f"{name.replace('_', ' ')} failed: {result['error']}")
        elif name == "apply_security_updates":
            before = (result.get("before") or {}).get("security")
            after = (result.get("after") or {}).get("security")
            if result.get("ok"):
                parts.append(f"Installed security updates ({before} waiting, {after} left)")
            else:
                parts.append("Installing security updates failed")
        elif name == "rotate_logs":
            if result.get("ok"):
                parts.append(f"Rotated the logs (journal {result.get('journal_mb_before')} MB to "
                             f"{result.get('journal_mb_after')} MB)")
            else:
                parts.append("Rotating the logs failed")
        elif name == "propose" and result.get("saved"):
            parts.append(f"Proposed: {result.get('title')}")
    serious = [finding["title"] for finding in findings if finding["level"] != "info"]
    parts.append("Still to look at: " + "; ".join(serious) if serious else "Nothing else needs you")
    return ".  ".join(parts) + "."


def decide(messages):
    prompt = _prompt(messages)
    done = _calls(messages)
    names = [name for name, _, _ in done]
    findings = _json(FINDINGS_RE, prompt)
    healths = [result for name, _, result in done if name == "read_health" and "findings" in result]
    if healths:
        findings = healths[-1]["findings"]
    fixes = {finding.get("fix") for finding in findings}
    for action in ACTIONS:
        if action in fixes and action not in names:
            return [tool_use_block(action, {})]
    if "read_logs" not in names:
        return [tool_use_block("read_logs", {})]
    acted = any(name in ACTIONS for name in names)
    if acted and names[-1] != "read_health" and not healths:
        return [tool_use_block("read_health", {})]
    proposed = set(_json(PROPOSED_RE, prompt)) | {call.get("key") for name, call, _ in done if name == "propose"}
    for finding in findings:
        proposal = finding.get("proposal")
        if proposal and proposal["key"] not in proposed:
            return [tool_use_block("propose", {key: proposal[key] for key in ("key", "title", "reason", "steps",
                                                                              "risk")},
                                   block_id=f"toolu_propose_{len(done)}")]
    level = "urgent" if any(f["level"] == "urgent" for f in findings) else \
        "warning" if any(f["level"] == "warning" for f in findings) else "ok"
    return [tool_use_block("report", {"summary": _summary(done, findings), "level": level})]


class OpsStandIn:
    model = STANDIN_MODEL

    def complete(self, *, system, messages, tools=(), max_tokens=1024):
        content = decide(messages)
        return Reply(content=content, model=STANDIN_MODEL, input_tokens=estimate_tokens([system, messages, tools]),
                     output_tokens=estimate_tokens(content))
