# 🔍 Agentic Research Workspace & Evaluation Benchmark

An evidence-driven, interactive platform for pair-programming and evaluating an LLM-based **Research Agent** equipped with tool routing, parameter mapping constraints, policy compliance, and multi-turn chat memory capabilities.

---

## 🛠️ Project Overview

This project implements a complete **Research Agentic Loop** designed to handle complex information retrieval, social media monitoring, academic paper search, and policy routing. The agent's performance has been optimized iteratively using an **evidence-driven prompt engineering methodology** across several development versions (`v0` -> `v4.2`), achieving **100% accuracy** on all evaluation benchmarks.

### Key Implemented Features:
1. **Interactive Streamlit Dashboard (`app.py`):**
   * **Live Chat:** Talk to the agent and watch detailed tool call executions (arguments & returned payloads) in real time.
   * **Evaluation Analytics:** View progress charts of accuracies over versions, and explore case-by-case actual vs. expected tool-call outputs.
2. **Parallel Tool Selection & Execution:** Supported tools include `lookup` (web news search), `social_search` (discussions on X/Twitter), `timeline` (Twitter user account feeds), `fetch` (reading explicit URLs), `policy` (internal compliance lookups), `papers` & `paper_text` (arXiv paper search & extraction), `send` (Telegram publishing with confirmation), and `clarify` (handling missing parameters).
3. **Custom Name-to-Handle Resolution:** Built-in resolution logic mapping entities like Sam Altman to Twitter handle `@sama` to prevent raw name arguments from failing tool signatures.
4. **Rigorous Evaluator Engine (`run_eval.py`):** Validates routing accuracy, correct argument extraction, parameter carryover, boundary rules, and dropping of platform-specific scopes.

---

## 📂 Folder Map

```text
├── README.md                 # Project user guide (this file)
├── README_ONLY.md            # Lab guidelines & rules
├── TOOL-SETUP.md             # API keys and external tools setup
└── starter_v0/               # Core codebase
    ├── app.py                # Streamlit UI (Live Chat + Analytics Dashboard)
    ├── agent.py              # Core LLM orchestrator & tool execution loop
    ├── chat.py               # Interactive CLI chat & session logger
    ├── run_eval.py           # Evaluation benchmark runner
    ├── artifacts/            # Prompts, tool metadata, and performance logs
    │   ├── system_prompt.md  # Optimized instructions for the model
    │   ├── tools.yaml        # Tool parameters & descriptions
    │   ├── version_log.csv   # Version history log
    │   └── REPORT.md         # Final team report with accuracy proofs
    ├── data/                 # Evaluation dataset suites
    │   ├── eval_base.json    # Base suite (20 cases)
    │   ├── eval_ext.json     # Extension suite (10 cases)
    │   └── eval_group.json   # Custom team suite (10 cases - 5 single/5 multi-turn)
    ├── runs/                 # Evaluation JSON log artifacts
    └── transcripts/          # CLI chat conversation session logs
```

---

## 🚀 Getting Started

### 1. Prerequisites & Installation
Ensure you are using Python 3.10+ (macOS/Linux/Windows).

1. Clone this repository and navigate to the project directory:
   ```bash
   cd VinUni_Lab4_Prompt_Engineering_and_Tool_Calling
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r starter_v0/requirements.txt
   ```

### 2. Configure Environment Variables
Create a `.env` file inside `starter_v0/` (or copy `.env.example`):
```bash
cp starter_v0/.env.example starter_v0/.env
```
Open `starter_v0/.env` and add your keys (e.g. `OPENAI_API_KEY`, etc.).

---

## 🖥️ Running the Project

### A. Launch the Streamlit Dashboard (UI)
The easiest way to interact with the agent and view the evaluation dashboards is through the Streamlit web interface:
```bash
streamlit run starter_v0/app.py
```
* **Live Chat Tab:** Test the agent's behavior, see real-time tool calling logs, and reply to clarification requests.
* **Evaluation Analytics Tab:** Compare run histories, view accuracy timelines, and drill down on passed/failed benchmark assertions.

### B. Run the CLI Chat
If you prefer a lightweight terminal-based chat session:
```bash
python starter_v0/chat.py --provider openai --version v4.2
```
Type `/exit` to stop. Conversation histories will be logged into `starter_v0/transcripts/`.

### C. Run the Evaluation Benchmark Suite
Run the test suites directly from the terminal to measure and log metrics:

* **Run Base Suite:**
  ```bash
  python starter_v0/run_eval.py --provider openai --version v4.2 --suite base
  ```
* **Run Custom Group Suite:**
  ```bash
  python starter_v0/run_eval.py --provider openai --version v4.2 --suite group --eval-cases starter_v0/data/eval_group.json
  ```
* **Run Extension Suite:**
  ```bash
  python starter_v0/run_eval.py --provider openai --version v4.2 --suite extension
  ```

---

## 📈 Optimization & Benchmarks Summary

Through iterative prompt engineering and structured boundary handling, the Agent achieved a **100% success rate** across all benchmarks:

| Benchmark Suite | Test Case Count | Accuracy | Key Skills Tested |
| :--- | :---: | :---: | :--- |
| **Base Suite** | 20 | **100%** | Web news queries, handle mapping, direct/out-of-scope refusals, missing URLs, yes/no confirmation. |
| **Extension Suite** | 10 | **100%** | Context carryover across turns, parameter corrections, platform-switching tool transitions. |
| **Group (Team) Suite** | 10 | **100%** | Parallel tool calls, company policy area routing, academic arXiv searches, Telegram confirmed publishing. |
