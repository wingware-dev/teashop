"""What every AI agent in the shop shares: the AI client and its offline
stand-in, the monthly spending cap, the "AI assistant" label, handling of
untrusted input (customer emails and chats, web pages), checks on what an
agent writes, and the audited tool loop.  docs/agents.md describes it.

Feature agents (support, marketing, ops) live in their own apps and build on
this one; it depends on no agent app.
"""
