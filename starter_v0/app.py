import streamlit as st
import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd

from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import build_artifact_version

# Load environment variables
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
RUNS_DIR = ROOT / "runs"
load_lab_env(ROOT)

# Configure Page
st.set_page_config(
    page_title="Agentic Research Workspace",
    page_icon="🔬",
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
        margin-bottom: 1.5rem;
    }
    /* Elegant containers */
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
    /* Status Badges */
    .badge-pass {
        background-color: #2ecc71;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .badge-fail {
        background-color: #e74c3c;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
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

# Set up Workspace Tabs
tab_chat, tab_eval = st.tabs(["💬 Live Agent Chat", "📊 Evaluation Dashboard"])

# ----------------- TAB 1: LIVE AGENT CHAT -----------------
with tab_chat:
    # Setup Sidebar Configuration inside Live Chat tab
    with st.sidebar:
        st.markdown("### ⚙️ Live Chat Settings")
        provider_name = st.selectbox(
            "Model Provider",
            ["openai", "openrouter", "anthropic", "gemini"],
            index=0,
            key="chat_provider"
        )
        
        default_models = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet",
            "gemini": "gemini-2.5-flash",
            "openrouter": "google/gemini-2.5-flash"
        }
        
        model_name = st.text_input("Model Name", value=default_models.get(provider_name, "gpt-4o-mini"), key="chat_model")
        max_rounds = st.slider("Max Tool Execution Rounds", min_value=1, max_value=8, value=4, key="chat_max_rounds")
        history_window = st.slider("History Context Window", min_value=1, max_value=10, value=5, key="chat_history_window")
        
        st.markdown("---")
        st.markdown("### 📜 System Prompt Override")
        system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        default_prompt = system_prompt_path.read_text(encoding="utf-8") if system_prompt_path.exists() else ""
        system_prompt = st.text_area("Edit System Prompt", value=default_prompt, height=200, key="chat_sys_prompt")
        
        st.markdown("---")
        if st.button("🔄 Clear Chat"):
            if "chat_history" in st.session_state:
                st.session_state.chat_history = []
            if "messages" in st.session_state:
                st.session_state.messages = []
            st.rerun()

    # Title
    st.markdown('<div class="gradient-text">🔬 Agentic Research Workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="gradient-subtitle">Interact with the Research Agent and watch it execute parallel tools, resolve handles, and manage policy checks in real time.</div>', unsafe_allow_html=True)

    # Initialize Session State
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

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
                        
                        tools_executed.append({
                            "name": call.name,
                            "args": call.args,
                            "result": event["result"]
                        })
                        
                        result = event.get("result", {})
                        if isinstance(result, dict) and result.get("awaiting_user"):
                            clarify_triggered = True
                            clarify_question = result.get("question") or call.args.get("question") or "Need clarification."
                            break
                        
                        non_clarify_events.append(event)
                    
                    if clarify_triggered:
                        final_text = clarify_question
                        break
                    
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
                
                st.rerun()

# ----------------- TAB 2: EVALUATION DASHBOARD -----------------
with tab_eval:
    st.markdown('<div class="gradient-text">📊 Evaluation Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="gradient-subtitle">Analyze benchmark suite execution runs, compare versions, and inspect case-by-case outputs.</div>', unsafe_allow_html=True)
    
    # Scan runs directory for logs
    run_files = sorted(list(RUNS_DIR.glob("*.json")), reverse=True) if RUNS_DIR.exists() else []
    
    if not run_files:
        st.warning("No evaluation runs found in the `runs/` directory. Run evaluation suite scripts first to generate metrics.")
    else:
        # Load all run summaries for comparison & sidebar dropdown
        run_summaries = []
        for file in run_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    run_summaries.append({
                        "file_name": file.name,
                        "file_path": file,
                        "run_id": data.get("run_id", file.stem),
                        "version": data.get("version", "N/A"),
                        "suite": data.get("suite", "N/A"),
                        "provider": data.get("provider", "N/A"),
                        "accuracy": data.get("summary", {}).get("case_accuracy", 0.0),
                        "passed": data.get("summary", {}).get("passed_cases", 0),
                        "total": data.get("summary", {}).get("total_cases", 0),
                        "routing": data.get("summary", {}).get("tool_routing_accuracy", 0.0),
                        "arguments": data.get("summary", {}).get("argument_accuracy", 0.0),
                        "multiturn": data.get("summary", {}).get("multiturn_accuracy", 0.0),
                        "timestamp": data.get("generated_at", "N/A")
                    })
            except Exception as e:
                pass
                
        df_runs = pd.DataFrame(run_summaries)
        
        # 1. Version Comparison Trend Chart
        st.markdown("### 📈 Accuracy Progress Timeline (Base Suite)")
        df_base = df_runs[df_runs["suite"] == "base"].copy()
        # Sort chronologically by timestamp
        df_base = df_base.sort_values("timestamp")
        
        if not df_base.empty:
            chart_data = df_base[["version", "accuracy"]].copy()
            chart_data["accuracy"] = chart_data["accuracy"] * 100
            st.line_chart(data=chart_data, x="version", y="accuracy", color="#6c5ce7")
        else:
            st.info("No base suite runs to compile progress timeline.")
            
        st.markdown("---")
        
        # 2. Select Run File to Inspect
        st.markdown("### 🔍 Detailed Run inspector")
        selected_run_label = st.selectbox(
            "Select Evaluation Run Log to Inspect",
            options=df_runs.index,
            format_func=lambda idx: f"[{df_runs.loc[idx, 'version'].upper()}] - {df_runs.loc[idx, 'suite'].upper()} Suite via {df_runs.loc[idx, 'provider'].upper()} ({df_runs.loc[idx, 'timestamp']})"
        )
        
        selected_run = df_runs.loc[selected_run_label]
        
        # Load the selected run data
        with open(selected_run["file_path"], "r", encoding="utf-8") as f:
            run_data = json.load(f)
            
        # Top-level metric cards
        summary = run_data.get("summary", {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Accuracy", f"{summary.get('case_accuracy', 0.0)*100:.1f}%", help="Percentage of cases that passed completely")
        with col2:
            st.metric("Tool Routing Accuracy", f"{summary.get('tool_routing_accuracy', 0.0)*100:.1f}%")
        with col3:
            st.metric("Argument Accuracy", f"{summary.get('argument_accuracy', 0.0)*100:.1f}%")
        with col4:
            st.metric("Passed Cases", f"{summary.get('passed_cases', 0)} / {summary.get('total_cases', 0)}")
            
        # Filters for case listing
        st.markdown("#### Test Cases Details")
        filter_status = st.radio("Filter cases by status:", ["All", "Passed", "Failed"], horizontal=True)
        
        cases = run_data.get("results", [])
        
        filtered_cases = []
        for case in cases:
            passed = case.get("result", {}).get("passed", False)
            if filter_status == "Passed" and not passed:
                continue
            if filter_status == "Failed" and passed:
                continue
            filtered_cases.append(case)
            
        # Render Cases
        for case in filtered_cases:
            case_id = case.get("id", "N/A")
            passed = case.get("result", {}).get("passed", False)
            difficulty = case.get("metadata", {}).get("difficulty", "easy").upper()
            skill = case.get("metadata", {}).get("skill", "general")
            
            badge_html = '<span class="badge-pass">PASS</span>' if passed else '<span class="badge-fail">FAIL</span>'
            
            with st.expander(f"📌 {case_id} ({skill}) — Difficulty: {difficulty}", expanded=not passed):
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span><b>Status:</b> {badge_html}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                st.markdown(f"**Input:** `{case.get('input') or case.get('turns', [{'content': 'N/A'}])[-1]['content']}`")
                
                # Render multi-turn history if present
                if "turns" in case:
                    with st.container():
                        st.markdown("**Turn History Context:**")
                        for t_idx, turn in enumerate(case["turns"]):
                            st.markdown(f"> **Turn {t_idx+1} ({turn.get('role')}):** {turn.get('content')}")
                
                # Show Expected vs Actual side-by-side
                col_exp, col_act = st.columns(2)
                with col_exp:
                    st.markdown("**Expected Tool Calls:**")
                    expected_calls = case.get("expect", {}).get("tool_calls", [])
                    if expected_calls:
                        st.json(expected_calls)
                    else:
                        st.write("*No tool calls expected (out of scope/answering directly)*")
                with col_act:
                    st.markdown("**Actual Tool Calls:**")
                    actual_calls = case.get("result", {}).get("actual_tool_calls", [])
                    if actual_calls:
                        st.json(actual_calls)
                    else:
                        st.write("*No tool calls made*")
                        
                # Failure details if failed
                if not passed:
                    failures = case.get("result", {}).get("failures", [])
                    observed_mismatch = case.get("result", {}).get("observed_mismatch", "N/A")
                    st.error(f"**Failure Type:** {observed_mismatch}\n\n**Reasons:**\n" + "\n".join([f"- {f}" for f in failures]))
                    
                    if case.get("result", {}).get("actual_text"):
                        st.info(f"**Actual Text Response:** {case['result']['actual_text']}")
