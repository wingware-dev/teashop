"""The AI model behind the agents, behind one small interface.

A client has complete(system=, messages=, tools=, max_tokens=) -> Reply.
Messages and tools use the Anthropic Messages API's shapes, which the
stand-ins produce too:

- messages: [{"role": "user" | "assistant", "content": [block, ...]}]
- blocks: {"type": "text", "text"}, {"type": "tool_use", "id", "name",
  "input"}, {"type": "tool_result", "tool_use_id", "content", "is_error"}
- tools: [{"name", "description", "input_schema"}]

client_for(agent, standin) picks the client: the real API only for agents
named in settings.AGENTS_LIVE (empty by default), else the stand-in the
agent gives, which calls nothing outside and costs nothing.  So the shop
runs, and its tests pass, without an API key or spending a cent; going
live is the owner's decision, one agent at a time.

ScriptedClient plays back fixed replies, for tests.
"""

import logging
from dataclasses import dataclass, field

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

log = logging.getLogger(__name__)

STANDIN_MODEL = "stand-in"


class AIError(Exception):
    """The AI service refused the request (bad request, bad key)."""


class AIUnavailable(AIError):
    """The AI service is down, overloaded or rate-limiting: try later."""


@dataclass
class Reply:
    content: list
    model: str = STANDIN_MODEL
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = "end_turn"
    live: bool = False

    @property
    def text(self):
        return "".join(block.get("text", "") for block in self.content if block.get("type") == "text").strip()

    @property
    def tool_calls(self):
        return [block for block in self.content if block.get("type") == "tool_use"]


def text_block(text):
    return {"type": "text", "text": text}


def tool_use_block(name, tool_input, block_id=None):
    return {"type": "tool_use", "id": block_id or f"toolu_{name}", "name": name, "input": tool_input}


def estimate_tokens(value):
    """A rough token count (about 4 characters a token, rounded up)."""
    return len(str(value)) // 4 + 1


class AnthropicClient:
    """The Claude API (Messages), called with requests.  Used only for agents
    in settings.AGENTS_LIVE, with settings.ANTHROPIC_API_KEY."""

    url = "https://api.anthropic.com/v1/messages"
    version = "2023-06-01"
    retry_statuses = {408, 409, 429, 500, 502, 503, 504, 529}

    def __init__(self, api_key, model, timeout=60):
        self.api_key, self.model, self.timeout = api_key, model, timeout

    def payload(self, *, system, messages, tools, max_tokens):
        body = {"model": self.model, "max_tokens": max_tokens, "system": system, "messages": messages}
        if tools:
            body["tools"] = tools
        return body

    def complete(self, *, system, messages, tools=(), max_tokens=1024):
        try:
            response = requests.post(
                self.url, timeout=self.timeout,
                headers={"x-api-key": self.api_key, "anthropic-version": self.version,
                         "content-type": "application/json"},
                json=self.payload(system=system, messages=messages, tools=list(tools), max_tokens=max_tokens))
        except requests.RequestException as exc:
            raise AIUnavailable(f"AI service unreachable: {exc}") from exc
        if response.status_code in self.retry_statuses:
            raise AIUnavailable(f"AI service busy or failing (HTTP {response.status_code})")
        if response.status_code != 200:
            # The body says what was wrong with the request; it never holds the key.
            raise AIError(f"AI service refused the request (HTTP {response.status_code}): {response.text[:300]}")
        data = response.json()
        usage = data.get("usage") or {}
        return Reply(content=data.get("content") or [], model=data.get("model") or self.model,
                     input_tokens=int(usage.get("input_tokens") or 0),
                     output_tokens=int(usage.get("output_tokens") or 0),
                     stop_reason=data.get("stop_reason") or "", live=True)


@dataclass
class ScriptedClient:
    """Plays back replies in order (Reply objects, or lists of blocks), and
    keeps each request in .requests.  For tests."""

    replies: list
    model: str = STANDIN_MODEL
    requests: list = field(default_factory=list)

    def complete(self, *, system, messages, tools=(), max_tokens=1024):
        self.requests.append({"system": system, "messages": [dict(m) for m in messages], "tools": list(tools),
                              "max_tokens": max_tokens})
        if not self.replies:
            raise AssertionError("ScriptedClient has no more replies")
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if not isinstance(reply, Reply):
            reply = Reply(content=list(reply), model=self.model)
        if not reply.input_tokens:
            reply.input_tokens = estimate_tokens([system, messages, tools])
        if not reply.output_tokens:
            reply.output_tokens = estimate_tokens(reply.content)
        return reply


def is_live(agent):
    return agent in settings.AGENTS_LIVE


def client_for(agent, standin):
    """The client agent uses: the Claude API if the owner turned it on for
    this agent (settings.AGENTS_LIVE), else standin() (a factory)."""
    if not is_live(agent):
        return standin()
    if not settings.ANTHROPIC_API_KEY:
        raise ImproperlyConfigured(f"AGENTS_LIVE names {agent!r} but ANTHROPIC_API_KEY is not set")
    return AnthropicClient(settings.ANTHROPIC_API_KEY, settings.AGENTS_MODEL)
