
A working pipeline where natural language prompts are converted into drone missions
via an LLM planner, validated by a guardrail layer, and executed deterministically
by ArduPilot SITL.

---

## Architecture

| Layer | File | Role |
|---|---|---|
| LLM Planner | `llm_planner.py` | Converts natural language to mission JSON via Groq API |
| Validator | `validator.py` | Checks schema + hard safety rules. No LLM involved. |
| Executor | `executor.py` | Sends MAVLink commands to ArduPilot. Deterministic. |
| Schema | `schema.json` | Defines allowed mission structure and safety bounds |
| Orchestrator | `main.py` | Runs all stages in sequence |

**Key design principle**: The LLM proposes, never flies. The executor contains
zero LLM code. The same validated JSON always produces the same drone behaviour.

### Safety bounds enforced by validator (not LLM):
- Altitude: 2m – 50m
- Speed: 0.5 – 15 m/s
- Max waypoints: 20
- Max loops: 10
- Max geofence offset: 500m from home

---

## Requirements

- Ubuntu 20.04 or 22.04
- Python 3.10+
- ArduPilot SITL installed
- QGroundControl (for visual telemetry)
- Groq API key (free at https://console.groq.com)

---

## Option A: Run with Docker (Recommended)

### 1. Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Start ArduPilot SITL on your host machine
```bash
sim_vehicle.py -v ArduCopter --console --map --out udp:127.0.0.1:14551
```
Wait until you see: `EKF2 IMU0 is using GPS`

### 3. Start QGroundControl
```bash
./QGroundControl.AppImage
```
Confirm drone appears on map before proceeding.

### 4. Build the Docker image
```bash
docker build -t omokai-drone .
```

### 5. Run a mission
```bash
docker run -it \
  -e GROQ_API_KEY="your-groq-key-here" \
  --network host \
  omokai-drone \
  python3 main.py "Patrol a 30 metre square loop twice at 10 metres altitude"
```

---

## Option B: Run Directly (No Docker)

### 1. Install dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Set your Groq API key
```bash
export GROQ_API_KEY="your-groq-key-here"
```

### 3. Start ArduPilot SITL
```bash
sim_vehicle.py -v ArduCopter --console --map --out udp:127.0.0.1:14551
```

### 4. Start QGroundControl
```bash
./QGroundControl.AppImage
```

### 5. Run a mission
```bash
python3 main.py "Patrol a 30 metre square loop twice at 10 metres altitude"
```

---

## Example Commands

```bash
# Valid mission — drone flies a square loop
python3 main.py "Patrol a 30 metre square loop twice at 10 metres altitude"

# Rejected by validator — altitude too high
python3 main.py "Patrol a square at 80 metres altitude"

# Rejected by LLM — nonsense prompt
python3 main.py "Make me a coffee"
```

---

## Expected Output (Valid Mission)
