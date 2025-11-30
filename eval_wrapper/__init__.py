import sys
import os

# 1. Add project root to path so veganflow_ai is visible
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../eval_wrapper
project_root = os.path.dirname(current_dir)              # .../
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. Expose the agent module
# This allows 'import eval_wrapper' to access 'eval_wrapper.agent'
from . import agent
