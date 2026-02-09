# AI Voice Agent - System Design

## Context

Build a web-based AI voice agent that conducts natural voice conversations, displays a lip-synced avatar, and manages appointment booking/retrieval against a Supabase database. The project requires two separate repos (backend + frontend) and a deployed link.

**Key choices:** Claude (Anthropic) as LLM, Tavus for avatar, Railway for backend deployment, Vercel for frontend.

---

## Architecture Overview

```
Vercel (React/Next.js Frontend)
    |  WebRTC (audio/video/data)
    v
LiveKit Cloud (SFU + Agent Dispatch)
    |  WebRTC (agent participant)
    v
Railway (Python LiveKit Agent)
    |  +-- Deepgram STT (speech -> text)
    |  +-- Claude LLM (reasoning + tool calls)
    |  +-- Cartesia TTS (text -> speech)
    |  +-- Tavus Avatar (speech -> lip-synced video)
    |  +-- REST API
    v
Supabase (PostgreSQL - appointments)
```

### Single Utterance Flow

1. User speaks -> audio streams via WebRTC to LiveKit Agent
2. Deepgram STT transcribes audio -> text
3. Claude LLM decides: respond or call a tool
4. If tool call -> execute against Supabase -> publish event to frontend via data channel -> return result to LLM
5. Claude generates text response -> Cartesia TTS -> audio
6. Audio -> Tavus avatar renders lip-synced video -> streams back to frontend

---

## Tech Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Voice Framework | LiveKit Agents (Python) | Real-time voice pipeline orchestration |
| Speech-to-Text | Deepgram (Nova 3) | Transcribe user speech |
| Text-to-Speech | Cartesia (Sonic 3) | Generate agent voice |
| LLM | Claude (Anthropic) | Reasoning, tool calling, conversation |
| Avatar | Tavus | Lip-synced video avatar |
| Frontend | Next.js + React | Web application |
| Database | Supabase (PostgreSQL) | Appointment storage |
| Backend Hosting | Railway | Always-on Python agent |
| Frontend Hosting | Vercel | Static + serverless deployment |

---

## Phase 1: Service Setup & API Keys

Create accounts and get API keys for:
- **LiveKit Cloud** (cloud.livekit.io) -- URL, API Key, API Secret
- **Anthropic** -- API key for Claude
- **Deepgram** (deepgram.com) -- API key (200 hrs/month free)
- **Cartesia** (cartesia.ai) -- API key for TTS
- **Tavus** (tavus.io) -- API key, create a Replica + Persona (set `pipeline_mode: "echo"`, `transport_type: "livekit"`)
- **Supabase** (supabase.com) -- Project URL + anon key

---

## Phase 2: Database Schema (Supabase)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    doctor_name VARCHAR(255) NOT NULL DEFAULT 'Dr. Smith',
    reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'cancelled', 'completed', 'modified')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_appointments_phone ON appointments(phone_number);
CREATE INDEX idx_appointments_date_time ON appointments(appointment_date, appointment_time)
    WHERE status = 'scheduled';
```

### Hard-Coded Slot Design

Available slots are generated in the backend as configuration:
- **Days**: Next 5 business days (Mon-Fri)
- **Hours**: 9:00 AM - 5:00 PM
- **Interval**: 30-minute slots
- **Doctor**: Dr. Smith (default)
- Booked slots are filtered out by querying Supabase

---

## Phase 3: Backend (Python LiveKit Agent)

### Directory Structure

```
ai-voice-agent-backend/
+-- agent.py                  # Entry point: AgentServer, session setup, Tavus avatar
+-- agent_definition.py       # AppointmentAgent class with 7 @function_tool methods
+-- tools/
|   +-- __init__.py
|   +-- appointment_tools.py  # Supabase CRUD (identify, fetch, book, retrieve, cancel, modify)
|   +-- slot_generator.py     # Generate available time slots
+-- db/
|   +-- __init__.py
|   +-- supabase_client.py    # Singleton Supabase client
+-- config.py                 # System prompt, slot config, env var loading
+-- models.py                 # Pydantic models (Appointment, ToolCallEvent)
+-- requirements.txt
+-- .env.example
+-- Dockerfile
+-- README.md
```

### Key Files

#### `agent.py` -- Entry Point

Wires together the voice pipeline:
- `AgentSession` with:
  - `deepgram.STT(model="nova-3")` for speech recognition
  - `anthropic.LLM(model="claude-sonnet-4-20250514")` for reasoning
  - `cartesia.TTS(model="sonic-3")` for voice synthesis
  - `silero.VAD` for voice activity detection
  - `MultilingualModel` turn detector
- `tavus.AvatarSession(replica_id=..., persona_id=...)` for avatar
- Metrics collection for optional cost tracking

#### `agent_definition.py` -- Core Agent Logic

- `AppointmentAgent(Agent)` class with `instructions=SYSTEM_PROMPT`
- 7 `@function_tool` methods:
  1. `identify_user` -- Ask for phone number, look up in DB
  2. `fetch_slots` -- Generate available slots, filter booked ones
  3. `book_appointment` -- INSERT into Supabase with double-booking check
  4. `retrieve_appointments` -- SELECT scheduled appointments by phone
  5. `cancel_appointment` -- UPDATE status to 'cancelled'
  6. `modify_appointment` -- UPDATE date/time with availability check
  7. `end_conversation` -- Generate summary, publish to frontend, end call
- Each tool publishes start/complete events to frontend via `room.local_participant.publish_data(topic="tool_call")`
- `end_conversation` also publishes on `topic="call_summary"`

#### `tools/appointment_tools.py` -- Supabase CRUD

- `identify_user_by_phone(phone)` -- lookup by phone number
- `fetch_available_slots(preferred_date)` -- generate slots, subtract booked ones
- `book_appointment(phone, name, date, time, reason)` -- INSERT with double-booking prevention
- `retrieve_appointments(phone)` -- SELECT WHERE status='scheduled'
- `cancel_appointment(id)` -- UPDATE status='cancelled'
- `modify_appointment(id, new_date, new_time)` -- UPDATE with availability check

#### `tools/slot_generator.py` -- Slot Generation

- Generates slots for next 5 business days
- 9:00 AM - 5:00 PM, 30-minute intervals
- Returns list of `{date, time, doctor}` dicts

### Tool Call -> Frontend Visualization

Each `@function_tool` method publishes JSON via LiveKit data channel:

```python
# On tool start:
await room.local_participant.publish_data(
    payload=ToolCallEvent(
        tool_name="book_appointment",
        status="started",
        arguments={...}
    ).model_dump_json(),
    reliable=True,
    topic="tool_call"
)

# On tool complete:
await room.local_participant.publish_data(
    payload=ToolCallEvent(
        tool_name="book_appointment",
        status="completed",
        arguments={...},
        result={...}
    ).model_dump_json(),
    reliable=True,
    topic="tool_call"
)
```

### Dependencies

```
livekit-agents[deepgram,cartesia,anthropic,silero,tavus,turn-detector]~=1.3
supabase>=2.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

---

## Phase 4: Frontend (React/Next.js)

### Directory Structure

```
ai-voice-agent-frontend/
+-- app/
|   +-- layout.tsx
|   +-- page.tsx                # Landing page -> <VoiceAgentApp />
|   +-- api/token/route.ts      # POST: generates LiveKit access token
+-- components/
|   +-- VoiceAgentApp.tsx       # State machine: welcome -> connected -> summary
|   +-- WelcomeView.tsx         # Phone input + connect button
|   +-- SessionView.tsx         # Grid layout: avatar + transcript (left), tools (right)
|   +-- AvatarDisplay.tsx       # Renders Tavus video track from agent participant
|   +-- TranscriptPanel.tsx     # Real-time user/agent transcription display
|   +-- ToolCallPanel.tsx       # List of tool call cards
|   +-- ToolCallCard.tsx        # Single tool: name badge, spinner/checkmark, args, result
|   +-- CallSummary.tsx         # End-of-call modal with summary + disconnect
+-- hooks/
|   +-- useToolCalls.ts         # Subscribes to "tool_call" data channel
|   +-- useCallSummary.ts       # Subscribes to "call_summary" data channel
|   +-- useToken.ts             # Fetches LiveKit token from /api/token
+-- lib/
|   +-- types.ts                # ToolCallEvent, CallSummaryData, ConnectionState
|   +-- utils.ts                # Formatting helpers
+-- package.json
+-- tailwind.config.ts
+-- .env.local.example
```

### Component Tree

```
<VoiceAgentApp>
  +-- {welcome} -> <WelcomeView />           (phone input, connect button)
  +-- {connected} ->
     <LiveKitRoom serverUrl token connect audio>
       <SessionView>
         +-- <AvatarDisplay />               (Tavus video track)
         +-- <TranscriptPanel />             (useTrackTranscription)
         +-- <ToolCallPanel>                 (useToolCalls hook)
              +-- <ToolCallCard /> x N
       </SessionView>
       {summary received} -> <CallSummary /> (modal overlay)
     </LiveKitRoom>
```

### Key Hooks

**`useToolCalls`** -- Listens on `useDataChannel("tool_call", callback)`:
- On "started" event -> add to list with spinner
- On "completed" event -> replace matching started entry with result

**`useCallSummary`** -- Listens on `useDataChannel("call_summary", callback)`:
- When received -> triggers state transition to summary view

### Token Endpoint (`/api/token`)

- Accepts POST with `{ phoneNumber }`
- Generates LiveKit `AccessToken` with room join grants
- Returns `{ token, url }` for the frontend to connect

### Dependencies

```
next ^15, react ^19, @livekit/components-react ^2, livekit-client ^2,
livekit-server-sdk ^2, tailwindcss ^4, lucide-react
```

---

## Phase 5: Deployment

### Backend -> Railway

- `Dockerfile`: Python 3.12-slim, install deps, `CMD ["python", "agent.py", "start"]`
- Set all env vars in Railway dashboard
- Agent auto-registers with LiveKit Cloud on startup

### Frontend -> Vercel

- Import Next.js repo
- Set env vars: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- Auto-builds and deploys

### Environment Variables

| Variable | Backend | Frontend |
|----------|---------|----------|
| LIVEKIT_URL | Yes | Yes |
| LIVEKIT_API_KEY | Yes | Yes |
| LIVEKIT_API_SECRET | Yes | Yes |
| ANTHROPIC_API_KEY | Yes | No |
| DEEPGRAM_API_KEY | Yes | No |
| CARTESIA_API_KEY | Yes | No |
| TAVUS_API_KEY | Yes | No |
| TAVUS_REPLICA_ID | Yes | No |
| TAVUS_PERSONA_ID | Yes | No |
| SUPABASE_URL | Yes | No |
| SUPABASE_KEY | Yes | No |

---

## Implementation Order

| Step | What | Files |
|------|------|-------|
| 1 | Create Supabase project + run SQL | (Supabase dashboard) |
| 2 | Init backend repo, install deps, create `.env` | `requirements.txt`, `.env` |
| 3 | Build `config.py`, `db/supabase_client.py`, `models.py` | 3 files |
| 4 | Build `tools/slot_generator.py` + `tools/appointment_tools.py` | 2 files |
| 5 | Build `agent_definition.py` (all 7 tools) | 1 file (core) |
| 6 | Build `agent.py` (pipeline without Tavus first) | 1 file |
| 7 | Test backend via LiveKit playground | -- |
| 8 | Add Tavus avatar to `agent.py` | edit 1 file |
| 9 | Init frontend repo (Next.js + Tailwind) | scaffold |
| 10 | Build token endpoint + types + hooks | 5 files |
| 11 | Build all components (Welcome -> Session -> Summary) | 8 files |
| 12 | End-to-end testing (book, retrieve, cancel, modify flows) | -- |
| 13 | Deploy backend to Railway, frontend to Vercel | Dockerfile |

---

## Verification Plan

1. **Voice pipeline**: Connect via frontend -> speak -> verify transcription appears -> verify agent responds with voice
2. **Tool calls**: Say "I want to book an appointment" -> verify `identify_user` fires -> provide phone -> verify tool card appears in UI
3. **Booking flow**: Provide date/time -> verify `fetch_slots` -> `book_appointment` -> confirm in Supabase
4. **Retrieve**: Ask "what appointments do I have" -> verify `retrieve_appointments` returns correct data
5. **Cancel/Modify**: Cancel or change an appointment -> verify Supabase updates
6. **Double-booking**: Try to book an already-taken slot -> verify rejection
7. **Summary**: Say goodbye -> verify `end_conversation` fires -> summary modal appears with correct details
8. **Avatar**: Verify Tavus video renders and lips sync with agent speech

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Tavus persona misconfiguration | Must set `pipeline_mode: "echo"` and `transport_type: "livekit"` -- test standalone first |
| Data channel message loss | Use `reliable=True` for all `publish_data` calls |
| System prompt quality | Allocate time for prompt iteration; ensure agent asks for phone first, confirms before booking |
| Supabase cold start (free tier) | First request after inactivity takes ~10s; consider keep-alive ping |
| Room access in tool functions | Access via `context.session.room`; fallback: store in `session.userdata` |
