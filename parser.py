"""
parser.py — AI-powered natural language parser for EchoArm
Uses Claude (via Anthropic API) to convert flexible natural language
into structured robot commands. Falls back to regex if API is unavailable.
"""

import json
import re
import urllib.request
import urllib.error


# ── Regex fallback (original MVP logic) ─────────────────────────────────────

def _regex_parse(text):
    """Original regex parser. Used when AI is unavailable."""
    text = text.lower().strip()

    result = {"action": None, "direction": None, "distance_cm": None, "angle_deg": None, "raw": text}

    if re.search(r'\b(move|go|walk|travel|advance)\b', text):
        result["action"] = "move"
    elif re.search(r'\b(rotate|turn|spin|pivot)\b', text):
        result["action"] = "rotate"
    elif re.search(r'\b(grab|grip|pick|grasp|take)\b', text):
        result["action"] = "grab"
    elif re.search(r'\b(release|drop|let go|open)\b', text):
        result["action"] = "release"
    elif re.search(r'\b(stop|halt|freeze|pause)\b', text):
        result["action"] = "stop"
        return result

    for direction in ["forward", "backward", "back", "left", "right", "up", "down"]:
        if direction in text:
            result["direction"] = "backward" if direction == "back" else direction
            break

    dist_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:cm|centimeter)', text)
    if dist_match:
        result["distance_cm"] = float(dist_match.group(1))

    angle_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:degree|deg|°)', text)
    if angle_match:
        result["angle_deg"] = float(angle_match.group(1))

    return result


# ── AI parser (Claude via Anthropic API) ────────────────────────────────────

SYSTEM_PROMPT = """You are the command parser for a robot arm controller called EchoArm.

Your job is to read a natural language instruction and return ONLY a JSON object — no explanation, no markdown, just raw JSON.

The JSON must follow this schema:
{
  "action":       string or null  — one of: "move", "rotate", "grab", "release", "stop", "unknown"
  "direction":    string or null  — one of: "forward", "backward", "left", "right", "up", "down"
  "distance_cm":  number or null  — distance in centimetres (estimate if vague, e.g. "a bit" = 5)
  "angle_deg":    number or null  — rotation angle in degrees (estimate if vague, e.g. "slightly" = 15)
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


def _ai_parse(text, api_key=None):
    """
    Calls Claude (Haiku, for speed) to parse the command.
    Returns a parsed dict, or None if the call fails.
    """
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 256,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": text}]
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    if api_key:
        headers["x-api-key"] = api_key

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            raw_text = body["content"][0]["text"].strip()
            return json.loads(raw_text)
    except urllib.error.HTTPError as e:
        print(f"[EchoArm] API error {e.code}: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"[EchoArm] AI parse failed ({type(e).__name__}): {e}")
        return None


# ── Public interface ─────────────────────────────────────────────────────────

def parse(text, api_key=None, use_ai=True):
    """
    Parse a natural language robot command into a structured dict.

    Args:
        text     : The user's input string.
        api_key  : Optional Anthropic API key. Not needed inside claude.ai.
        use_ai   : Set False to force regex-only mode (offline testing).

    Returns a dict with keys:
        action, direction, distance_cm, angle_deg, confidence, raw
    """
    text = text.strip()
    if not text:
        return {"action": None, "direction": None, "distance_cm": None,
                "angle_deg": None, "confidence": 0.0, "raw": ""}

    if use_ai:
        result = _ai_parse(text, api_key=api_key)
        if result:
            return result
        print("[EchoArm] Falling back to regex parser.")

    result = _regex_parse(text)
    result["confidence"] = 0.5 if result["action"] else 0.0
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
    print("EchoArm AI Parser — self-test\n" + "─" * 40)
    for cmd in tests:
        result = parse(cmd)
        print(f"Input : {cmd}")
        print(f"Output: {json.dumps(result, indent=2)}\n")
