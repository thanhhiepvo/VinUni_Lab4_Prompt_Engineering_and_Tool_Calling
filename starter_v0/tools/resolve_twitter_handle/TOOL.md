---
name: resolve_twitter_handle
track: bonus
kind: local_knowledge
---

# resolve_twitter_handle

Convert person names and references to standardized Twitter handles.

## Purpose
Map person names, nicknames, and informal references to their official Twitter/X account handles. This tool helps the agent:
- Recognize "Sam Altman" refers to @samaltman
- Map "Elon" to @elonmusk in context
- Handle common variations and misspellings
- Return structured handle info for timeline lookups

## When to use
- Agent receives a person's name but needs to map it to a Twitter handle
- Query is ambiguous (e.g., "What did Elon tweet?" → could be Elon Musk or other Elons)
- Need to validate that a person name actually corresponds to a known Twitter account

## Input
```python
resolve_twitter_handle("Sam Altman")
resolve_twitter_handle("Elon Musk")
resolve_twitter_handle("OpenAI")
```

## Output structure
```json
{
  "input": "Sam Altman",
  "resolved": true,
  "handle": "@samaltman",
  "handle_clean": "samaltman",
  "full_name": "Sam Altman",
  "context": "CEO of OpenAI",
  "confidence": 0.95,
  "alternatives": []
}
```

Or if ambiguous:
```json
{
  "input": "Elon",
  "resolved": false,
  "matches": [
    {"handle": "@elonmusk", "full_name": "Elon Musk", "context": "Tesla, SpaceX, X CEO", "confidence": 0.98},
    {"handle": "@ElonBachman", "full_name": "Elon Bachman", "context": "Other person", "confidence": 0.3}
  ],
  "suggestion": "Likely referring to Elon Musk (@elonmusk). Ask for clarification if unsure.",
  "confidence": 0.5
}
```

## Examples

### Example 1: Clear Match
```
User: "What are Sam Altman's latest tweets?"
Agent: resolve_twitter_handle("Sam Altman") → "@samaltman"
Agent: timeline("@samaltman") → [tweets...]
```

### Example 2: Ambiguous Input
```
User: "Show me Satoshi tweets"
Agent: resolve_twitter_handle("Satoshi") → {resolved: false, matches: [multiple possibilities]}
Agent: clarify("Do you mean Satoshi Nakamoto or another Satoshi?")
```

### Example 3: Company/Organization
```
User: "OpenAI's tweets"
Agent: resolve_twitter_handle("OpenAI") → "@OpenAI"
Agent: timeline("@OpenAI")
```

## Known Handles (Curated List)

| Input | Handle | Full Name |
|-------|--------|-----------|
| Sam Altman | @samaltman | Sam Altman |
| Elon Musk | @elonmusk | Elon Musk |
| Elon | @elonmusk | Elon Musk (inferred from context) |
| OpenAI | @OpenAI | OpenAI (Organization) |
| ChatGPT | @OpenAI or @ChatGPTapp | OpenAI ChatGPT |
| Vitalik | @VitalikButerin | Vitalik Buterin |
| Satoshi | [ambiguous] | Various Satoshis |

## Integration

This tool should be called automatically by the agent when:
1. User mentions a person by name
2. Agent is about to call `timeline` but only has a person name (not a handle)
3. There's ambiguity about which account to use

Consider adding to system prompt: "When using timeline with a person's name, first call resolve_twitter_handle to get the correct handle."
