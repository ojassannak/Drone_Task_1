import json
import os
from groq import Groq

SYSTEM_PROMPT = """You are a mission planner for a drone.
Convert the operator's natural language instruction into a JSON object matching this schema EXACTLY.
Output ONLY raw JSON — no explanation, no markdown, no backticks.

Schema:
{schema}

Rules:
- waypoints are offsets in METRES from home position
- North = positive lat_offset_m
- East  = positive lon_offset_m
- altitude_m is above takeoff point
- If the instruction is unsafe, impossible or too vague output: {{"error": "<reason>"}}
"""

def plan_mission(prompt: str, schema: dict) -> dict:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(schema=json.dumps(schema, indent=2))
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=1000
    )

    raw_text = response.choices[0].message.content.strip()
    print(f"\n--- LLM RAW OUTPUT ---\n{raw_text}\n----------------------\n")

    # clean up if model adds markdown fences despite instructions
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        return {"error": f"LLM returned invalid JSON: {e}"}
