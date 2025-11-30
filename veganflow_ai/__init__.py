"""Top-level package for veganflow_ai.

Expose the `agent` submodule as the attribute `veganflow_ai.agent` so
external runners that do `import veganflow_ai` and then access
`veganflow_ai.agent` find the expected module object.

Note: importing `agent` will execute the module-level initialization
in `veganflow_ai/agent.py` (database setup and root_agent creation),
which appears to be intentional for this project.
"""

from . import agent as agent

__all__ = ["agent"]

