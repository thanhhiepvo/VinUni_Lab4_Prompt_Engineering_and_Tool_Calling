# V2 Failure Analysis & Enhancement Plan

## Summary
**Current**: 80% (16/20 passed) | **Target**: 85-90%

## The 4 Remaining Failures

### Category 1: Person Names as Handles (R01, R05) — 2 failures
These are really **ONE underlying issue**: Agent doesn't recognize person names as valid Twitter handles

| Case ID | Query (Vietnamese) | Expected | Actual | Root Cause |
|---------|------|----------|--------|------------|
| **R01_user_tweets_routing** | "Tweet mới nhất của Sam Altman là gì?" (Latest tweets from Sam Altman?) | `timeline("sam_altman")` | `clarify()` asking for username | Agent treats "Sam Altman" as ambiguous, asks for clarification instead of recognizing it as a handle |
| **R05_limit_arg** | "Lấy 10 tweet mới nhất của Elon Musk" (Get 10 latest tweets from Elon Musk) | `timeline("elon", limit=10)` | `clarify()` asking for username | Same: "Elon Musk" should map directly to timeline handle |

**Hypothesis**: System prompt needs explicit guidance: "When user mentions a well-known person (by full name, surname, or nickname), treat it as a direct reference to their Twitter account without asking for clarification."

---

### Category 2: Clarification Question Wording (R10, R11) — 2 failures
These **correctly use clarify**, but the question text doesn't match expected wording

| Case ID | Query | Expected Clarification | Actual Clarification | Status |
|---------|------|-------|--------|--------|
| **R10_missing_handle** | "Tóm tắt 5 tweet mới nhất" (Summarize 5 latest tweets) | Specific expected wording | "Bạn có thể cung cấp tên tài khoản Twitter mà bạn muốn tóm tắt tweet không?" | ✓ Tool correct, ✗ Wording mismatch |
| **R11_missing_url** | "Tóm tắt bài viết này" (Summarize this article) | Specific expected wording | "Vui lòng cung cấp URL cụ thể của bài viết mà bạn muốn tóm tắt." | ✓ Tool correct, ✗ Wording mismatch |

**Hypothesis**: The test cases expect exact clarification question text. Need to either:
- A) Add specific examples in system_prompt showing expected clarification phrasing
- B) Accept that slightly different phrasings are equivalent (test framework change)
- C) Create a structured clarification template tool

---

## Enhancement Strategies

### Strategy A: Prompt Enhancement (Recommended)
**File**: `artifacts/system_prompt.md`

Add sections:
```
### Known Person Handles
When users mention well-known people by name, recognize them as Twitter accounts:
- "Sam Altman" → @samaltman on Twitter
- "Elon Musk" → @elonmusk on Twitter
- "OpenAI" → @OpenAI on Twitter
Do NOT ask for clarification. Use timeline directly.

### Clarification Question Templates
When asking for missing info, use these templates:
- Missing Twitter handle: "Bạn có thể cho biết tên tài khoản Twitter cụ thể? (Ví dụ: @handles hoặc người nổi tiếng)"
- Missing URL: "Vui lòng cung cấp URL cụ thể của bài viết."
```

**Expected Impact**: Fix R01, R05 (maybe) + improve R10, R11 consistency

---

### Strategy B: New Tool — `resolve_twitter_handle`
**Purpose**: Standardize person names → Twitter handles

Create tool: `tools/resolve_twitter_handle/tool.py`
```python
def resolve_twitter_handle(person_reference: str) -> dict:
    """
    Convert person names/references to Twitter handles.
    Examples:
      "Sam Altman" → "@samaltman" or error if ambiguous
      "Elon" → error (ambiguous, ask user)
      "OpenAI" → "@OpenAI"
    """
```

**Usage in flow**:
1. User: "Show Sam Altman tweets"
2. Agent: "resolve_twitter_handle('Sam Altman')" → "@samaltman"
3. Agent: "timeline('@samaltman')"

**Expected Impact**: Fix R01, R05 reliably

---

### Strategy C: New Tool — `clarify_structured`
**Purpose**: Ensure consistent clarification question phrasing

Create tool that generates structured clarification with predefined templates:
```python
def clarify_structured(missing_info_type: str, context: str = ""):
    """
    missing_info_type: 'twitter_handle' | 'url' | 'time_period' | etc.
    Returns pre-formatted clarification question in user's language
    """
```

**Expected Impact**: Fix R10, R11 by enforcing exact question format

---

## Recommended Action Plan

### Phase 1 (Lowest Risk): Enhance system_prompt
1. Add "Known Person Handles" section with examples
2. Add "Clarification Templates" section
3. Re-run eval → expect 85%+ accuracy

### Phase 2 (If Phase 1 doesn't solve R01/R05): Add `resolve_twitter_handle` tool
1. Create new tool that maps person names to handles
2. Update timeline tool description: "Can accept person names (e.g., 'Sam Altman') or handles (e.g., '@samaltman')"
3. Guide system prompt to call resolve_twitter_handle when unclear

### Phase 3 (If Phase 1 doesn't solve R10/R11): Add `clarify_structured` tool
1. Create tool with predefined clarification templates
2. Update system prompt to use clarify_structured instead of freeform ask_user

---

## Files to Modify

```
artifacts/system_prompt.md              # Add known handles + clarification templates
artifacts/tools.yaml                    # Update timeline description
tools/timeline/tool.py                  # Optional: improve handle parsing
tools/resolve_twitter_handle/          # NEW (Phase 2)
tools/clarify_structured/               # NEW (Phase 3)
```

---

## Success Metrics
- **Phase 1 Success**: 18/20 (90%) with just prompt improvements
- **Phase 2 Success**: 19/20 (95%) with resolve_twitter_handle
- **Phase 3 Success**: 20/20 (100%) with clarify_structured

Current: **16/20 (80%)**
