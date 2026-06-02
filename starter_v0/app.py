import streamlit as st
import json
import re
from pathlib import Path
from datetime import datetime

from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import build_artifact_version

# Load environment variables
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

# Configure Page
st.set_page_config(
    page_title="Agentic Research Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown(
    """
    <style>
    /* Gradient headers */
    .gradient-text {
        background: linear-gradient(135deg, #6c5ce7, #a29bfe, #00cec9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    .gradient-subtitle {
        color: #b2bec3;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    /* Elegant borders and shadow containers */
    .stChatInputContainer {
        border-radius: 12px;
    }
    .tool-execution-card {
        background-color: #1e1e24;
        border-left: 5px solid #6c5ce7;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 12px;
        color: #dfe6e9;
    }
    .tool-title {
        color: #a29bfe;
        font-weight: 700;
        font-family: monospace;
    }
    /* Sidebar premium styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1e1e24, #0f0f12);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Helper function to serialize JSON
def json_pretty(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)

# Helper function to execute tool calls
def execute_tool_call(call: ToolCall) -> dict:
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {
            "tool": call.name,
            "args": call.args,
            "result": {"error": "unknown_tool", "message": f"No local implementation for {call.name}"},
        }
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}

# Setup Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    provider_name = st.selectbox(
        "Model Provider",
        ["openai", "openrouter", "anthropic", "gemini"],
        index=0
    )
    
    # Auto-fallback to default model
    default_models = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-sonnet",
        "gemini": "gemini-2.5-flash",
        "openrouter": "google/gemini-2.5-flash"
    }
    
    model_name = st.text_input("Model Name", value=default_models.get(provider_name, "gpt-4o-mini"))
    max_rounds = st.slider("Max Tool Execution Rounds", min_value=1, max_value=8, value=4)
    history_window = st.slider("History Context Window", min_value=1, max_value=10, value=5)
    
    st.markdown("---")
    st.markdown("### 📜 System Prompt Settings")
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    default_prompt = system_prompt_path.read_text(encoding="utf-8") if system_prompt_path.exists() else ""
    system_prompt = st.text_area("Edit System Prompt", value=default_prompt, height=250)
    
    st.markdown("---")
    if st.button("🔄 Clear Chat & Session"):
        st.session_state.clear()
        st.rerun()

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# Main Title Header
st.markdown('<div class="gradient-text">🔍 Research Agent Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="gradient-subtitle">An agentic assistant equipped with real-time news retrieval, social media monitoring, academic research extraction, and internal company policies.</div>', unsafe_allow_html=True)

# Render Chat History
for message in st.session_state.chat_history:
    role = message["role"]
    avatar = "👤" if role == "user" else "🤖"
    
    with st.chat_message(role, avatar=avatar):
        # Render tools invoked in this turn
        if "tools" in message and message["tools"]:
            with st.expander("🔧 Tools Executed in this Turn", expanded=False):
                for tool in message["tools"]:
                    st.markdown(
                        f"""
                        <div class="tool-execution-card">
                            <div class="tool-title">⚡ Call: {tool['name']}</div>
                            <b>Arguments:</b> <pre>{json_pretty(tool['args'])}</pre>
                            <b>Result:</b> <pre style="max-height: 250px; overflow-y: auto;">{json_pretty(tool['result'])}</pre>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        # Render text response
        if message["text"]:
            st.markdown(message["text"])

# Get User Input
if user_input := st.chat_input("Ask the research agent..."):
    # Append user turn to history
    st.session_state.chat_history.append({"role": "user", "text": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
        
    # Build full prompt context window
    trimmed_history = []
    # Fetch last N user/assistant message turns from state
    turns_to_fetch = st.session_state.chat_history[-(history_window * 2):]
    for h in turns_to_fetch:
        trimmed_history.append({"role": h["role"], "content": h["text"]})
        
    messages = [
        {"role": "system", "content": system_prompt},
        *trimmed_history
    ]
    
    # Load tools
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    
    # Initialize Provider
    provider = make_provider(provider_name)
    
    # Execution Loop
    assistant_placeholder = st.empty()
    with assistant_placeholder.container():
        with st.chat_message("assistant", avatar="🤖"):
            status_container = st.empty()
            tools_executed = []
            final_text = ""
            
            # Start model round loop
            for round_idx in range(1, max_rounds + 1):
                status_container.markdown(f"🤖 *Thinking (Round {round_idx}/{max_rounds})...*")
                
                try:
                    response = provider.complete(
                        messages=messages,
                        tools=openai_tools,
                        model=model_name,
                        temperature=0.0
                    )
                except Exception as exc:
                    st.error(f"Provider Error: {exc}")
                    break
                
                calls = response.tool_calls
                
                if not calls:
                    final_text = response.text or ""
                    break
                
                # Format assistant tool call payload for model continuation
                call_summary = [{"name": call.name, "args": call.args} for call in calls]
                content = response.text or "I will call the selected tool(s)."
                messages.append({
                    "role": "assistant",
                    "content": f"{content}\n\nTOOL_CALLS_JSON:\n{json_pretty(call_summary)}"
                })
                
                non_clarify_events = []
                clarify_triggered = False
                clarify_question = ""
                
                # Execute tool calls
                for call in calls:
                    status_container.markdown(f"🔧 *Running tool: `{call.name}`...*")
                    event = execute_tool_call(call)
                    
                    # Store for UI display
                    tools_executed.append({
                        "name": call.name,
                        "args": call.args,
                        "result": event["result"]
                    })
                    
                    # Check if clarification is needed
                    result = event.get("result", {})
                    if isinstance(result, dict) and result.get("awaiting_user"):
                        clarify_triggered = True
                        clarify_question = result.get("question") or call.args.get("question") or "Need clarification."
                        break
                    
                    non_clarify_events.append(event)
                
                if clarify_triggered:
                    final_text = clarify_question
                    break
                
                # Append tool execution results back to history context
                messages.append({
                    "role": "user",
                    "content": (
                        "TOOL_RESULTS_JSON:\n"
                        f"{json_pretty(non_clarify_events)}\n\n"
                        "Use only these tool results to continue."
                    )
                })
            
            # Render tool executions
            if tools_executed:
                with st.expander("🔧 Tools Executed in this Turn", expanded=True):
                    for tool in tools_executed:
                        st.markdown(
                            f"""
                            <div class="tool-execution-card">
                                <div class="tool-title">⚡ Call: {tool['name']}</div>
                                <b>Arguments:</b> <pre>{json_pretty(tool['args'])}</pre>
                                <b>Result:</b> <pre style="max-height: 250px; overflow-y: auto;">{json_pretty(tool['result'])}</pre>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            
            status_container.empty()
            st.markdown(final_text)
            
            # Save to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "text": final_text,
                "tools": tools_executed
            })
            
            # Auto-rerun to lock states
            st.rerun()
