# Day 04 Lab v2 Report — Research Agent

## Team

- Team: 5
- Members: Võ Thanh Hiệp, Nguyễn Công Tuấn Anh
- Provider/model: OpenAI / gpt-4o-mini

## Final Metrics

- Final version: v4.2
- Final artifact_version: v4.2+pbf07158b235c+t98bb7df9996d
- Best base run file: `runs/v4.1_B_base_openai_20260602T152834874233.json`
- Base case accuracy: 1.0 (100%)
- Base tool routing accuracy: 1.0 (100%)
- Base argument accuracy: 1.0 (100%)
- Group eval run file: `runs/v4.2_B_group_openai_20260602T153238616169.json`
- Group eval accuracy: 1.0 (100%)
- Chat transcript file: `transcripts/v4.2_openai_20260602T153308848297.transcript.json`

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---|---|---|
| v0 | baseline | No optimization yet | 0.00 (base) | 0.70 (base) | `v0_B_base_openai_20260602T142654960548.json` |
| v1 | `system_prompt.md` | Add routing guidelines and Vietnamese templates | 0.70 (base) | 0.75 (base) | `v1_B_base_openai_20260602T150208816195.json` |
| v2 | `system_prompt.md` | Add out of scope guidelines and boundary check constraints | 0.75 (base) | 0.80 (base) | `v2_B_base_openai_20260602T150405372914.json` |
| v3 | `tools.yaml` | Add resolve_twitter_handle tool and mapping dictionary | 0.80 (base) | 0.60 (base) | `v3_B_base_openai_20260602T152244417195.json` |
| v4.1 | `system_prompt.md` | Enforce name-to-handle conversion & multi-turn drop constraints | 0.60 (base) | 1.00 (base) | `v4.1_B_base_openai_20260602T152834874233.json` |
| v4.2 | `system_prompt.md` | Handle confirmation response types explicitly in multi-turn | 0.90 (group) | 1.00 (group) | `v4.2_B_group_openai_20260602T153238616169.json` |

## Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| M06_switch_tool | `wrong_tool` | `lookup` + `social_search` | Model called `social_search` despite user explicitly dropping Twitter | Instructed prompt not to invoke abandoned platforms/tools |
| G08_multi_clarify_telegram_confirm | `wrong_boundary` | `clarify` (with `yes_no`) | Called `clarify` instead of calling `send` directly when confirmation was given in the latest turn | Updated system prompt to explicitly convert positive verification phrases (e.g. "Xác nhận gửi đi") into direct `send` tool calls |

## Team Eval Cases

We added 10 cases in total (5 single turn, 5 multi turn) to `data/eval_group.json`:

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_single_timeline_karpathy | Map Karpathy -> karpathy and invoke timeline | `timeline(screenname="karpathy")` | PASS |
| G02_single_policy_data_privacy | Check policy area for data privacy / prompt keys | `policy(policy_area="data_privacy")` | PASS |
| G03_single_papers_agent | Query academic papers about agents | `papers(query="AI agents")` | PASS |
| G04_single_clarify_no_url | Trigger text clarify when URL is missing | `clarify(response_type="text")` | PASS |
| G05_single_parallel_fetch_policy | Fetch url and read policy simultaneously | `fetch` + `policy(policy_area="ai_research")` | PASS |
| G06_multi_carryover_karpathy | Keep handle across turns, change limit | `timeline(screenname="karpathy", limit=10)` | PASS |
| G07_multi_switch_web_to_arxiv | Drop web search and switch to arXiv papers | `papers(query="LLM")` | PASS |
| G08_multi_clarify_telegram_confirm | Perform send on confirmation in turn 2 | `send(confirmed=true)` | PASS |
| G09_multi_carryover_policy | Keep policy area, update query | `policy(policy_area="data_privacy", query="...")` | PASS |
| G10_multi_carryover_fetch_url | Carry over resolved URL to fetch | `fetch(url="https://openai.com/blog/gpt-4o")` | PASS |

## Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tin tức AI nổi bật hôm nay là gì?" | `lookup` with topic: `news` | `v4.2` | Responded with a structured summary of today's AI news and saved transcript. |

## Reflections

- **Which fixes belonged in `system_prompt.md`?**
  Rules regarding boundary limits, confirmation matching (like handling positive confirmations like "Xác nhận gửi đi"), tool drop semantics, and explicit mappings from well-known figure names to screennames.
- **Which fixes belonged in `tools.yaml`?**
  Tool parameters and description improvements, e.g. clarifying that the `timeline` tool expects a screenname without the `@` symbol, and providing explicit `policy_area` string literals.
- **Which failure needed manual review instead of automatic grading?**
  Cases where the agent's textual response (e.g. general explanations or math recursion solutions) matches formatting instructions without invoking tools, as these cannot easily be evaluated by structural strict match schemas.
- **What would you improve next?**
  Dynamic fallback search logic (e.g. calling `resolve_twitter_handle` automatically inside code/agent execution loop if names are passed directly), and caching mechanisms to reduce LLM completion overhead.
