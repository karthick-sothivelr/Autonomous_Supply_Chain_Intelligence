import chainlit as cl
import asyncio
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# --- Import VeganFlow ---
from veganflow_ai.agents.orchestrator import create_store_manager
from veganflow_ai.tools.retail_database_setup import setup_retail_database
from memory_utils import initialize_memory

@cl.on_chat_start
async def start():
    """Initialize the environment and services."""
    init_msg = cl.Message(content="⚙️ **System Booting...**")
    await init_msg.send()

    # 1. Setup Infrastructure
    setup_retail_database()
    memory_service = await initialize_memory()
    session_service = InMemorySessionService()

    # 2. Create the Agent
    orchestrator = create_store_manager()
    
    # 3. Configure Session
    user_id = "demo_user"
    session_id = "web_session_001"
    app_name = "veganflow_ui"

    await session_service.create_session(user_id=user_id, session_id=session_id, app_name=app_name)

    # 4. Store in User Session
    runner = Runner(
        agent=orchestrator,
        session_service=session_service,
        memory_service=memory_service,
        app_name=app_name
    )
    
    cl.user_session.set("runner", runner)
    cl.user_session.set("config", {"user_id": user_id, "session_id": session_id})

    # 5. Welcome Message
    init_msg.content = (
        "## 🌿 VeganFlow: Autonomous Supply Chain Intelligence\n\n"
        "I am ready to manage your supply chain. I can **Negotiate Prices**, **Check Stock**, and **Analyze Risks**.\n\n"
        "**Demo Scenario:**\n"
        "Try asking: *'Oat Barista Blend is running low. Buy 100 units at the best price.'*"
    )
    await init_msg.update()

@cl.on_message
async def main(message: cl.Message):
    """Process the user message and stream the agent's thoughts."""
    runner = cl.user_session.get("runner")
    config = cl.user_session.get("config")

    final_response = ""
    
    # We use a root step to group the thinking process
    async with cl.Step(name="🧠 VeganFlow Reasoning", type="run") as root_step:
        root_step.input = message.content
        
        # Run the Agent Loop
        async for event in runner.run_async(
            user_id=config["user_id"],
            session_id=config["session_id"],
            new_message=types.Content(parts=[types.Part(text=message.content)])
        ):
            # --- 1. DETECT TOOL CALLS (The "Actions") ---
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        tool_name = part.function_call.name
                        tool_args = part.function_call.args
                        
                        # Create a visible step for the tool
                        async with cl.Step(name=f"🛠️ Action: {tool_name}", type="tool", parent_id=root_step.id) as tool_step:
                            # Pretty print arguments
                            try:
                                args_json = json.dumps(tool_args, indent=2)
                            except:
                                args_json = str(tool_args)
                            
                            tool_step.input = args_json
                            tool_step.output = "✅ Executed successfully."

            # --- 2. DETECT FINAL RESPONSE ---
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text

        root_step.output = "Process Complete."

    # Send the final clean answer
    await cl.Message(content=final_response).send()
