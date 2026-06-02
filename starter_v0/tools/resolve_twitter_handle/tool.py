from typing import Any, Optional


# Curated mapping of known people to their Twitter handles
KNOWN_HANDLES = {
    # Tech founders & CEOs
    "sam altman": {"handle": "@sama", "full_name": "Sam Altman", "context": "CEO of OpenAI"},
    "elon musk": {"handle": "@elonmusk", "full_name": "Elon Musk", "context": "CEO of Tesla, SpaceX, X"},
    "elon": {"handle": "@elonmusk", "full_name": "Elon Musk", "context": "CEO of Tesla, SpaceX, X", "informal": True},
    "andrej karpathy": {"handle": "@karpathy", "full_name": "Andrej Karpathy", "context": "AI Researcher, former Tesla/OpenAI"},
    "karpathy": {"handle": "@karpathy", "full_name": "Andrej Karpathy", "context": "AI Researcher, former Tesla/OpenAI", "informal": True},
    "mark zuckerberg": {"handle": "@facebookapp", "full_name": "Mark Zuckerberg", "context": "CEO of Meta"},
    "bill gates": {"handle": "@BillGates", "full_name": "Bill Gates", "context": "Founder of Microsoft"},
    "steve jobs": {"handle": "@stevejobs", "full_name": "Steve Jobs", "context": "Former Apple CEO"},
    "tim cook": {"handle": "@tim_cook", "full_name": "Tim Cook", "context": "CEO of Apple"},
    
    # Crypto
    "vitalik": {"handle": "@VitalikButerin", "full_name": "Vitalik Buterin", "context": "Ethereum founder", "informal": True},
    "vitalik buterin": {"handle": "@VitalikButerin", "full_name": "Vitalik Buterin", "context": "Ethereum founder"},
    
    # Organizations
    "openai": {"handle": "@OpenAI", "full_name": "OpenAI", "context": "AI research organization"},
    "chatgpt": {"handle": "@ChatGPTapp", "full_name": "ChatGPT", "context": "OpenAI's language model"},
    "google": {"handle": "@Google", "full_name": "Google", "context": "Tech company"},
    "meta": {"handle": "@Meta", "full_name": "Meta", "context": "Social media & tech company"},
    "twitter": {"handle": "@Twitter", "full_name": "Twitter", "context": "Social media platform"},
    "x": {"handle": "@X", "full_name": "X (formerly Twitter)", "context": "Social media platform"},
    "tesla": {"handle": "@Tesla", "full_name": "Tesla", "context": "Electric vehicle company"},
    "spacex": {"handle": "@SpaceX", "full_name": "SpaceX", "context": "Aerospace company"},
}


def resolve_twitter_handle(person_reference: str = "", context: str = "") -> dict[str, Any]:
    """
    Convert person names and references to Twitter handles.
    
    Args:
        person_reference: Person name, nickname, or handle (e.g., "Sam Altman", "Elon", "@samaltman")
        context: Optional context to disambiguate (e.g., "in crypto context" to help distinguish)
    
    Returns:
        Dictionary with resolved handle or list of candidates
    """
    try:
        if not person_reference:
            return {
                "error": "empty_reference",
                "message": "Please provide a person name or reference (e.g., 'Sam Altman', 'Elon Musk')"
            }
        
        # Normalize input
        ref_lower = person_reference.strip().lower()
        
        # If already a handle (starts with @), just clean it
        if ref_lower.startswith("@"):
            handle = ref_lower
            handle_clean = handle[1:] if handle.startswith("@") else handle
            return {
                "input": person_reference,
                "resolved": True,
                "handle": handle,
                "handle_clean": handle_clean,
                "type": "already_handle",
                "confidence": 1.0,
            }
        
        # Look up in known handles
        if ref_lower in KNOWN_HANDLES:
            info = KNOWN_HANDLES[ref_lower]
            return {
                "input": person_reference,
                "resolved": True,
                "handle": info["handle"],
                "handle_clean": info["handle"][1:] if info["handle"].startswith("@") else info["handle"],
                "full_name": info["full_name"],
                "context": info["context"],
                "confidence": 0.95,
                "alternatives": [],
            }
        
        # Try partial matches (check if reference is substring of known names)
        candidates = []
        for key, info in KNOWN_HANDLES.items():
            if ref_lower in key or key in ref_lower:
                candidates.append({
                    "handle": info["handle"],
                    "handle_clean": info["handle"][1:] if info["handle"].startswith("@") else info["handle"],
                    "full_name": info["full_name"],
                    "context": info["context"],
                    "match_type": "partial"
                })
        
        if candidates:
            # If only one candidate, treat as resolved
            if len(candidates) == 1:
                return {
                    "input": person_reference,
                    "resolved": True,
                    "handle": candidates[0]["handle"],
                    "handle_clean": candidates[0]["handle_clean"],
                    "full_name": candidates[0]["full_name"],
                    "context": candidates[0]["context"],
                    "confidence": 0.7,
                    "alternatives": [],
                }
            else:
                # Multiple candidates - ambiguous
                return {
                    "input": person_reference,
                    "resolved": False,
                    "matches": candidates,
                    "confidence": 0.3,
                    "suggestion": f"'{person_reference}' matched {len(candidates)} possible accounts. Please clarify which one you meant.",
                }
        
        # No match found
        return {
            "input": person_reference,
            "resolved": False,
            "matches": [],
            "confidence": 0.0,
            "suggestion": f"No known Twitter account found for '{person_reference}'. Please provide a Twitter handle (e.g., @username) or verify the person's name.",
        }
    
    except Exception as e:
        return {
            "error": "unexpected_error",
            "message": str(e),
        }
