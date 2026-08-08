"""
ollama_service.py
-----------------
Sends supply-chain data to a local Ollama model and parses
a structured carbon-credit breakdown per stage.

Usage (standalone test):
    python -m app.services.ollama_service

Ollama must be running locally:
    ollama serve
    ollama pull gemma:7b   # or whichever model you prefer
"""

import json
import re
import requests
import logging

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
OLLAMA_URL      = "http://localhost:11434/api/generate"
OLLAMA_MODEL    = "qwen2.5:0.5b"   # change to your pulled model name
REQUEST_TIMEOUT = 120          # seconds — LLMs can be slow
# ───────────────────────────────────────────────────────────────────────────────


def _build_prompt(product_name: str, product_description: str, stages: list[dict]) -> str:
    """Build the prompt we'll send to the LLM."""
    stages_text = ""
    for i, s in enumerate(stages, 1):
        stage_type = s.get("stage_type", "").replace("_", " ").title()
        name       = s.get("name") or s.get("courier") or "Unknown"
        origin     = s.get("origin") or s.get("dispatch_city") or "Unknown location"
        transport  = s.get("transport_mode") or s.get("shipping_type") or "Unknown"
        distance   = s.get("distance_km")
        notes      = s.get("description") or ""

        stages_text += f"\nStage {i} [{stage_type}]\n"
        stages_text += f"  Name/Facility : {name}\n"
        stages_text += f"  Location      : {origin}\n"
        stages_text += f"  Transport     : {transport}\n"
        if distance:
            stages_text += f"  Distance      : {distance} km\n"
        if notes:
            stages_text += f"  Notes         : {notes}\n"

    # NOTE: We use a two-shot example structure hint so gemma understands
    # exactly what shape to output, then close with the real task.
        prompt = f"""You are a sustainability analyst specialising in carbon accounting.

A company has mapped the full supply chain for their product. Your job is to:
1. Estimate the approximate carbon credits (in kg CO₂e) required to offset each stage.
2. Give a brief 1-sentence reasoning for each estimate.
3. Provide an overall carbon rating for the product (A+, A, B, C, or D) — A+ being near-zero footprint, D being very high.
4. Give one short actionable recommendation to reduce the footprint.

PRODUCT: {product_name}
DESCRIPTION: {product_description or "Not provided"}

SUPPLY CHAIN STAGES:
{stages_text}

Respond ONLY with a valid JSON object in exactly this structure. You MUST generate an entry inside the "stages" array for EVERY single stage listed above:

{{
  "stages": [
    {{
      "stage_number": 1,
      "stage_type": "Stage Type from input",
      "name": "Stage Name from input",
      "location": "Location from input",
      "carbon_credits_kg_co2e": 120.5,
      "reasoning": "Reasoning for stage 1."
    }},
    {{
      "stage_number": 2,
      "stage_type": "Stage Type from input",
      "name": "Stage Name from input",
      "location": "Location from input",
      "carbon_credits_kg_co2e": 45.2,
      "reasoning": "Reasoning for stage 2."
    }}
  ],
  "total_carbon_credits_kg_co2e": 165.7,
  "rating": "B",
  "recommendation": "One clear action to reduce the biggest emission source."
}}
"""

    return prompt


def call_ollama(prompt: str) -> str:
    """Send prompt to Ollama and return the raw text response."""
    payload = {
        "model":  OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,     # very low — we want deterministic JSON
            "num_predict": 2048,
            "stop": ["<end_of_turn>", "<start_of_turn>"],
        }
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")


def _extract_json(text: str) -> str:
    """
    Robustly extract the first complete JSON object from messy LLM output.

    Handles:
    - Leading/trailing prose ("Here is the JSON: {...}")
    - ```json ... ``` fences
    - Partial markdown fences (``` without closing)
    - Unicode issues
    """
    text = text.strip()

    # 1. Strip ```json fences if present
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if fence_match:
        return fence_match.group(1).strip()

    # 2. Extract from first { to last } — handles leading prose
    start = text.find('{')
    end   = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]

    # 3. Nothing found — return as-is and let json.loads raise a clear error
    return text


def parse_llm_response(raw: str) -> dict:
    """
    Parse the LLM JSON response with robust extraction.
    Logs the raw output on failure so you can inspect what the model returned.
    """
    try:
        candidate = _extract_json(raw)
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        logger.error("JSON parse failed.\nRaw LLM output:\n%s\nError: %s", raw, e)
        # Re-raise with a cleaner message for the Flask flash
        raise json.JSONDecodeError(
            f"Model returned invalid JSON: {e.msg} "
            f"(raw output starts with: {raw[:120]!r})",
            e.doc, e.pos
        )


def generate_carbon_breakdown(product_name: str, product_description: str, stages: list[dict]) -> dict:
    """
    Main entry point.

    :param product_name: str
    :param product_description: str
    :param stages: list of stage dicts (serialised Stage model data)
    :returns: parsed dict with keys: stages, total_carbon_credits_kg_co2e, rating, recommendation
    :raises: requests.RequestException on network error, json.JSONDecodeError on bad LLM output
    """
    prompt = _build_prompt(product_name, product_description, stages)
    raw    = call_ollama(prompt)
    print("Raw Ollama response:\n%s", raw)
    result = parse_llm_response(raw)
    return result


# ── Standalone test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    sample_stages = [
        {
            "stage_type": "raw_material",
            "name": "Organic Cotton",
            "origin": "Tamil Nadu, India",
            "transport_mode": "Road Freight",
            "distance_km": 180,
            "description": "GOTS certified organic cotton"
        },
        {
            "stage_type": "processing",
            "name": "Ring Spinning",
            "origin": "Coimbatore, India",
            "transport_mode": "Road Freight",
            "distance_km": 60,
            "description": ""
        },
        {
            "stage_type": "manufacturing",
            "name": "Tirupur Garments Ltd",
            "origin": "Tirupur, India",
            "transport_mode": "Sea Freight",
            "distance_km": 9000,
            "description": "SA8000 certified factory"
        },
        {
            "stage_type": "shipping",
            "courier": "DHL",
            "shipping_type": "Standard Courier",
            "dispatch_city": "Mumbai, India",
            "shipping_zones": "Domestic + International",
            "description": ""
        }
    ]

    print("Sending to Ollama…")
    try:
        result = generate_carbon_breakdown(
            "Organic Cotton T-Shirt", "A sustainable basics brand.", sample_stages
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"ERROR: {e}")