"""
parser.py — AI-powered natural language parser for OpenGuy.
Uses Claude (via Anthropic API) to convert flexible natural language
into structured robot commands. Falls back to regex if API is unavailable.
"""

import json
import re
import os
import urllib.request
import urllib.error
from typing import Optional, Dict, Any


# ── Parser Constants ─────────────────────────────────────────────────────────

ACTION_MAPPINGS = {
    "stop": [r"stop", r"halt", r"freeze", r"pause", r"wait", r"stay", r"hold\s+position", r"brake", r"cease", r"standby"],
    "release": [r"release", r"drop", r"let\s+go", r"open\s+grip", r"ungrip", r"put\s+down", r"place", r"set\s+down", r"deposit", r"leave"],
    "move": [r"move", r"go", r"walk", r"travel", r"advance", r"steps?", r"glide", r"run", r"sprint", r"dash",
             r"crawl", r"slide", r"shift", r"drive", r"navigate", r"proceed", r"march", r"head", r"push",
             r"pull", r"drag", r"fly", r"jump", r"leap", r"hop", r"roll", r"cruise", r"drift", r"charge",
             r"rush", r"hurry", r"scoot", r"inch", r"nudge", r"creep", r"jog", r"trot", r"gallop", r"approach", r"retreat"],
    "rotate": [r"rotate", r"turn", r"spin", r"pivot", r"swing", r"yaw", r"twist", r"face", r"look",
               r"orient", r"aim", r"point", r"steer", r"swivel", r"revolve", r"roll\s+over", r"bank", r"veer"],
    "grab": [r"grab", r"grip", r"pick", r"grasp", r"take", r"hold", r"catch", r"seize", r"snatch",
             r"clamp", r"pinch", r"latch", r"secure", r"collect", r"fetch", r"acquire", r"lift", r"raise"]
}

DIRECTION_MAPPINGS = {
    "forward": [r"forward", r"ahead", r"front", r"straight"],
    "backward": [r"backward", r"back", r"rear", r"reverse"],
    "left": [r"left", r"port", r"counterclockwise", r"ccw"],
    "right": [r"right", r"starboard", r"clockwise", r"cw"],
    "up": [r"up", r"upward", r"above", r"higher"],
    "down": [r"down", r"downward", r"below", r"lower"]
}

SEMANTIC_MODIFIERS = {
    "tiny": {"distance": 1.0, "angle": 5.0},
    "slightly": {"distance": 3.0, "angle": 10.0},
    "little": {"distance": 3.0, "angle": 10.0},
    "a bit": {"distance": 5.0, "angle": 15.0},
    "bit": {"distance": 5.0, "angle": 15.0},
    "far": {"distance": 30.0, "angle": 90.0},
    "lot": {"distance": 30.0, "angle": 90.0},
    "long": {"distance": 50.0, "angle": 180.0}
}

SPEED_MODIFIERS = {
    "slowly": 0.2,
    "gently": 0.2,
    "carefully": 0.3,
    "quietly": 0.3,
    "quickly": 0.8,
    "fast": 0.9,
    "rapidly": 1.0
}


# ── Regex fallback (original MVP logic) ─────────────────────────────────────

def _regex_parse(text: str) -> Dict[str, Any]:
    """Improved regex parser with semantic interpretation and synonym handling."""
    original_text = text.strip()
    text = original_text.lower()

    result = {
        "action": "unknown",
        "direction": None,
        "distance_cm": None,
        "angle_deg": None,
        "speed": 0.5,  # Default mid speed
        "confidence": 0.0,
        "raw": original_text,
    }

    # 1. Action Intent Detection
    for action, synonyms in ACTION_MAPPINGS.items():
        pattern = r'\b(' + '|'.join(synonyms) + r')\b'
        if re.search(pattern, text):
            result["action"] = action
            result["confidence"] = 0.5
            break
    
    # 1b. Fallback: if no action detected but has a number or direction, assume "move"
    if result["action"] == "unknown":
        has_number = bool(re.search(r'\d+', text))
        has_direction = any(
            re.search(r'\b(' + '|'.join(syns) + r')\b', text)
            for syns in DIRECTION_MAPPINGS.values()
        )
        if has_number or has_direction:
            result["action"] = "move"
            result["confidence"] = 0.4

    if result["action"] == "stop":
        result["confidence"] = 0.9
        return result

    # 2. Direction Detection
    for direction, synonyms in DIRECTION_MAPPINGS.items():
        pattern = r'\b(' + '|'.join(synonyms) + r')\b'
        if re.search(pattern, text):
            result["direction"] = direction
            break

    # 3. Numeric Extractions (Priority)
    # Match values followed by units
    unit_pattern = r'(\d+(?:\.\d+)?)\s*(cm|centimeter|units?|steps?|degrees?|deg|°)'
    unit_match = re.search(unit_pattern, text)
    if unit_match:
        val = float(unit_match.group(1))
        unit = unit_match.group(2)
        if any(u in unit for u in ["cm", "centimeter", "unit"]):
            result["distance_cm"] = val
        elif "step" in unit:
            result["distance_cm"] = val * 5.0  # Normalized: 1 step = 5cm
        elif any(u in unit for u in ["degree", "deg", "°"]):
            result["angle_deg"] = val
        result["confidence"] = 0.9

    # Handle bare numbers if action is known but no units found
    if result["distance_cm"] is None and result["action"] == "move":
        bare_match = re.search(r'\b(\d+(?:\.\d+)?)\b', text)
        if bare_match and not unit_match:
            result["distance_cm"] = float(bare_match.group(1))
            result["confidence"] = 0.7

    if result["angle_deg"] is None and result["action"] == "rotate":
        bare_match = re.search(r'\b(\d+(?:\.\d+)?)\b', text)
        if bare_match and not unit_match:
            result["angle_deg"] = float(bare_match.group(1))
            result["confidence"] = 0.7

    # 4. Semantic Modifiers (Vague terms) - Only if numeric missing
    if result["distance_cm"] is None and result["action"] == "move":
        for modifier, values in SEMANTIC_MODIFIERS.items():
            if modifier in text:
                result["distance_cm"] = values["distance"]
                result["confidence"] = 0.8
                break
        else:
            if result["direction"]: # Default distance
                result["distance_cm"] = 10.0
                result["confidence"] = 0.6

    if result["angle_deg"] is None and result["action"] == "rotate":
        for modifier, values in SEMANTIC_MODIFIERS.items():
            if modifier in text:
                result["angle_deg"] = values["angle"]
                result["confidence"] = 0.8
                break
        else:
            if result["direction"]: # Default angle
                result["angle_deg"] = 45.0
                result["confidence"] = 0.6

    # 5. Speed Modifiers
    for modifier, speed_val in SPEED_MODIFIERS.items():
        if modifier in text:
            result["speed"] = speed_val
            break

    # 6. Defaults & Constraints
    if result["action"] == "move" and result["direction"] is None:
        result["direction"] = "forward"
    
    if result["action"] == "rotate" and result["direction"] is None:
        result["direction"] = "right" # Default turn direction

    if result["action"] in ["grab", "release"]:
        result["confidence"] = 0.9

    return result


# ── AI parser (Claude via Anthropic API) ────────────────────────────────────

SYSTEM_PROMPT = """You are the command parser for a robot arm controller called OpenGuy.

Your job is to read a natural language instruction and return ONLY a JSON object — no explanation, no markdown, just raw JSON.

The JSON must follow this schema:
{
  "action":       string or null  — one of: "move", "rotate", "grab", "release", "stop", "unknown"
  "direction":    string or null  — one of: "forward", "backward", "left", "right", "up", "down"
  "distance_cm":  number or null  — distance in centimetres (estimate if vague, e.g. "a bit" = 5)
  "angle_deg":    number or null  — rotation angle in degrees (estimate if vague, e.g. "slightly" = 15)
  "speed":        number          — speed from 0.0 (gently) to 1.0 (rapidly), default 0.5
  "confidence":   number          — your confidence from 0.0 to 1.0
  "raw":          string          — the original input, unchanged
}

Rules:
- If the input is ambiguous but you can make a reasonable guess, do so and lower confidence.
- If completely unclear, set action to "unknown" and confidence to 0.
- Never return anything except the JSON object.
- "a bit" or "slightly" = ~5 cm or ~15 degrees
- "a little" = ~3 cm or ~10 degrees
- "far" or "a lot" = ~30 cm or ~90 degrees

Examples:
Input: "go a bit forward"
Output: {"action":"move","direction":"forward","distance_cm":5,"angle_deg":null,"confidence":0.9,"raw":"go a bit forward"}

Input: "turn slightly right"
Output: {"action":"rotate","direction":"right","distance_cm":null,"angle_deg":15,"confidence":0.85,"raw":"turn slightly right"}

Input: "pick up the object"
Output: {"action":"grab","direction":null,"distance_cm":null,"angle_deg":null,"confidence":0.95,"raw":"pick up the object"}
"""


def _ai_parse(text: str, model: str = "groq/llama-3.3-70b-versatile") -> Optional[Dict[str, Any]]:
    """
    Calls an LLM via LiteLLM to parse the command.
    Returns a parsed dict, or None if the call fails.
    """
    try:
        import litellm
        # Attempt to enforce JSON if supported by model name heuristics
        response_format = {"type": "json_object"} if ("gpt" in model or "groq" in model) else None
        
        # We rely on litellm picking up API keys from os.environ
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            response_format=response_format,
            max_tokens=256,
            temperature=0.0
        )
        raw_text = response.choices[0].message.content.strip()
        # Clean markdown code blocks if the model didn't respect raw JSON
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.replace("```", "").strip()

        return json.loads(raw_text)
    except Exception as e:
        print(f"[OpenGuy] AI parse failed: {e}")
        return None


# ── Public interface ─────────────────────────────────────────────────────────

def parse(
    text: str, 
    use_ai: bool = True
) -> Dict[str, Any]:
    """
    Parse a natural language robot command into a structured dict.

    Args:
        text     : The user's input string.
        use_ai   : Set False to force regex-only mode (offline testing).

    Returns a dict with keys:
        action, direction, distance_cm, angle_deg, confidence, raw
    """
    text = text.strip()
    if not text:
        return {
            "action": None,
            "direction": None,
            "distance_cm": None,
            "angle_deg": None,
            "speed": 0.5,
            "confidence": 0.0,
            "raw": ""
        }

    if use_ai:
        keys = ["GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
        has_key = any(os.getenv(k) for k in keys)
        
        if not has_key:
            print("[OpenGuy] Using regex parser (No API keys found in environment)")
        else:
            model = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile")
            result = _ai_parse(text, model=model)
            if result:
                return result
            print("[OpenGuy] AI parse failed, using regex fallback")

    result = _regex_parse(text)
    if not result["action"] or result["action"] == "unknown":
        result["confidence"] = 0.0
    elif result["action"] in {"grab", "release", "stop"}:
        result["confidence"] = 0.9
    elif result["action"] == "move":
        result["confidence"] = 0.85 if result["distance_cm"] is not None else 0.6
    elif result["action"] == "rotate":
        result["confidence"] = 0.85 if result["angle_deg"] is not None else 0.6
    else:
        result["confidence"] = 0.5
    return result


# ── Quick self-test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        "move forward 10 cm",
        "go a bit forward",
        "turn slightly right",
        "pick up the object",
        "rotate left 90 degrees",
        "stop",
        "drop it gently",
        "swing the arm way to the left",
    ]
    print("OpenGuy AI Parser — self-test\n" + "─" * 40)
    for cmd in tests:
        result = parse(cmd)
        print(f"Input : {cmd}")
        print(f"Output: {json.dumps(result, indent=2)}\n")
