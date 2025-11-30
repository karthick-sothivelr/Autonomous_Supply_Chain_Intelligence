import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the project modules
# (Path injection is handled in __init__.py now, but we keep safety checks)
try:
    from veganflow_ai.agents.orchestrator import create_store_manager
    from veganflow_ai.tools.retail_database_setup import setup_retail_database
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.getcwd()))
    from veganflow_ai.agents.orchestrator import create_store_manager
    from veganflow_ai.tools.retail_database_setup import setup_retail_database

# Initialize DB
setup_retail_database()

# Initialize Agent
# ADK looks for this specific variable name
root_agent = create_store_manager()
