"""Append-only audit log of who changed what: the owner, staff, AI agents
and the system itself.

Model changes are recorded automatically (see signals.py).  Code that does
something worth auditing without changing a model calls record(), and agent
code wraps its work in acting_as_agent() so its changes are attributed to it::

    from apps.audit import acting_as_agent, record

    with acting_as_agent("support-agent"):
        record("support.reply_sent", obj=ticket, message="Answered order-status question")
"""

from .context import (  # noqa: F401
    Actor, acting_as, acting_as_agent, acting_as_system, agent_involved, current_actor)
from .recording import record  # noqa: F401
