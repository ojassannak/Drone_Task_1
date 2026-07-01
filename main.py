import json
import sys
from llm_planner import plan_mission
from validator import validate_mission
from executor import execute_mission

def run(prompt: str):
    print(f"\nPrompt received: '{prompt}'")

    with open("schema.json") as f:
        schema = json.load(f)

    # stage 1 — LLM proposes mission
    print("\n[1/3] Sending to LLM (Groq)...")
    raw = plan_mission(prompt, schema)

    # stage 2 — validate (no LLM involved here)
    print("[2/3] Validating mission...")
    ok, result = validate_mission(raw)

    if not ok:
        print(f"\n❌ MISSION REJECTED: {result}")
        print("No commands were sent to the drone.")
        return

    print(f"\n✅ MISSION VALIDATED:\n{json.dumps(result, indent=2)}")

    # stage 3 — execute deterministically
    print("\n[3/3] Executing mission...")
    execute_mission(result)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("\nOperator prompt: ")
    run(prompt)
