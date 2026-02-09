# AI Voice Agent - Appointment Scheduling Assistant

A web-based AI voice agent that conducts natural voice conversations with a lip-synced avatar to help patients book, view, modify, and cancel medical appointments.

## Demo

> [Live Demo](https://your-deployed-url.vercel.app) (coming soon)

## Architecture

```
Browser (React/Next.js)
    |  WebRTC (audio/video/data)
    v
LiveKit Cloud (SFU + Agent Dispatch)
    |  WebRTC
    v
Python LiveKit Agent (Railway)
    |  +-- Deepgram STT (speech -> text)
    |  +-- Claude LLM (reasoning + tool calls)
    |  +-- Cartesia TTS (text -> speech)
    |  +-- Tavus Avatar (lip-synced video)
    |
    v
Supabase (PostgreSQL)
```

### How It Works

1. User speaks into their microphone in the browser
2. Audio streams via WebRTC through LiveKit to the Python agent
3. **Deepgram** transcribes speech to text in real-time
4. **Claude** (Anthropic) processes the text, decides to respond or call a tool
5. Tool calls execute against **Supabase** (e.g., book an appointment)
6. Tool call events are pushed to the frontend via LiveKit data channels for real-time visualization
7. Claude generates a response, **Cartesia** converts it to speech
8. **Tavus** renders a lip-synced avatar video from the audio
9. Avatar video + audio stream back to the browser

## Features

- **Voice Conversations** -- Natural speech-to-speech interaction powered by Deepgram STT + Cartesia TTS
- **AI Avatar** -- Lip-synced video avatar via Tavus that speaks the agent's responses
- **7 Tool Functions** -- Full appointment lifecycle management:
  | Tool | Description |
  |------|-------------|
  | `identify_user` | Look up patient by phone number |
  | `fetch_slots` | Get available appointment slots |
  | `book_appointment` | Book a new appointment |
  | `retrieve_appointments` | View all scheduled appointments |
  | `cancel_appointment` | Cancel an existing appointment |
  | `modify_appointment` | Reschedule an appointment |
  | `end_conversation` | End call with a summary |
- **Real-Time Tool Visualization** -- Every tool call is displayed on the frontend as it executes (started -> completed)
- **Call Summary** -- Automatic conversation summary when the call ends
- **Double-Booking Prevention** -- Slot availability checks before booking or modifying

## Tech Stack

| Component | Technology |
|-----------|------------|
| Voice Framework | [LiveKit Agents](https://docs.livekit.io/agents/) (Python) |
| Speech-to-Text | [Deepgram](https://deepgram.com/) Nova 3 |
| Text-to-Speech | [Cartesia](https://cartesia.ai/) Sonic |
| LLM | [Claude](https://anthropic.com/) (Anthropic) |
| Avatar | [Tavus](https://tavus.io/) |
| Frontend | [Next.js](https://nextjs.org/) 16 + React 19 |
| Styling | [Tailwind CSS](https://tailwindcss.com/) 4 |
| Database | [Supabase](https://supabase.com/) (PostgreSQL) |
| Backend Hosting | [Railway](https://railway.app/) |
| Frontend Hosting | [Vercel](https://vercel.com/) |

## Project Structure

```
.
+-- ai-voice-agent-backend/          # Python LiveKit Agent
|   +-- agent.py                     # Entry point (pipeline setup + Tavus avatar)
|   +-- agent_definition.py          # AppointmentAgent with 7 @function_tool methods
|   +-- config.py                    # System prompt, slot config, env vars
|   +-- models.py                    # Pydantic models (ToolCallEvent)
|   +-- tools/
|   |   +-- appointment_tools.py     # Supabase CRUD operations
|   |   +-- slot_generator.py        # Time slot generation (9am-5pm, 30min, weekdays)
|   +-- db/
|   |   +-- supabase_client.py       # Singleton database client
|   +-- tests/                       # 47 test cases
|   |   +-- test_slot_generator.py   # 11 tests - slot generation logic
|   |   +-- test_appointment_tools.py# 11 tests - Supabase CRUD + edge cases
|   |   +-- test_models.py           # 6 tests  - serialization, validation
|   |   +-- test_agent_definition.py # 12 tests - all 7 tools + event publishing
|   |   +-- conftest.py              # Mock Supabase client, LiveKit room fixtures
|   +-- pyproject.toml               # uv project config
|   +-- requirements.txt
|   +-- Dockerfile
|   +-- .env.example
|
+-- ai-voice-agent-frontend/         # Next.js Web App
|   +-- src/
|   |   +-- app/
|   |   |   +-- page.tsx             # Landing page -> <VoiceAgentApp />
|   |   |   +-- layout.tsx           # Root layout with metadata
|   |   |   +-- api/token/route.ts   # POST: generates LiveKit access token
|   |   +-- components/
|   |   |   +-- VoiceAgentApp.tsx    # State machine (welcome -> connected -> summary)
|   |   |   +-- WelcomeView.tsx      # Phone input + connect button
|   |   |   +-- SessionView.tsx      # Grid layout + data channel subscriptions
|   |   |   +-- AvatarDisplay.tsx    # Tavus video track or audio visualizer fallback
|   |   |   +-- TranscriptPanel.tsx  # Real-time user/agent transcription
|   |   |   +-- ToolCallPanel.tsx    # Scrollable list of tool call cards
|   |   |   +-- ToolCallCard.tsx     # Single tool: badge, spinner/check, args, result
|   |   |   +-- CallSummary.tsx      # End-of-call modal with summary + disconnect
|   |   +-- hooks/
|   |   |   +-- useToken.ts          # Fetches LiveKit token from /api/token
|   |   |   +-- useToolCalls.ts      # Subscribes to "tool_call" data channel
|   |   |   +-- useCallSummary.ts    # Subscribes to "call_summary" data channel
|   |   +-- lib/
|   |       +-- types.ts             # TypeScript interfaces
|   |       +-- utils.ts             # Formatting helpers (tool colors, time, names)
|   +-- Dockerfile
|   +-- .env.local.example
|   +-- package.json
|
+-- docker-compose.yml               # Run backend + frontend + tests
+-- .env.example                      # Root env for docker-compose build args
+-- SYSTEM_DESIGN.md                  # Detailed architecture documentation
+-- README.md
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker (optional, for containerized setup)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-voice-agent.git
cd ai-voice-agent
```

### 2. Get API Keys

Create accounts and get API keys from these services:

| Service | Sign Up | What You Need |
|---------|---------|---------------|
| LiveKit Cloud | [cloud.livekit.io](https://cloud.livekit.io) | URL, API Key, API Secret |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | API Key |
| Deepgram | [console.deepgram.com](https://console.deepgram.com) | API Key (200 hrs/month free) |
| Cartesia | [play.cartesia.ai](https://play.cartesia.ai) | API Key |
| Tavus | [platform.tavus.io](https://platform.tavus.io) | API Key, Replica ID, Persona ID |
| Supabase | [supabase.com/dashboard](https://supabase.com/dashboard) | Project URL, Anon Key |

**Tavus Persona Setup:** When creating the persona, set `pipeline_mode: "echo"` and `transport_type: "livekit"`. This ensures Tavus only renders lip-synced video from our audio (no built-in LLM).

### 3. Set Up the Database

Run this SQL in your **Supabase SQL Editor**:

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

### 4. Set Up the Backend

```bash
cd ai-voice-agent-backend

# Copy and fill in your API keys
cp .env.example .env

# Install dependencies with uv
uv sync --all-extras

# Run the agent in dev mode
uv run python agent.py dev
```

The agent will connect to LiveKit Cloud and wait for room connections.

### 5. Set Up the Frontend

```bash
cd ai-voice-agent-frontend

# Copy and fill in LiveKit keys
cp .env.local.example .env.local

# Install dependencies
npm install

# Run the dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 6. Docker Compose (Run Everything)

```bash
# Set up env files
cp .env.example .env                              # Root (docker-compose build args)
cp ai-voice-agent-backend/.env.example ai-voice-agent-backend/.env
cp ai-voice-agent-frontend/.env.local.example ai-voice-agent-frontend/.env.local
# Fill in all API keys in each file

# Build and run both services
docker compose up --build

# Run in background
docker compose up --build -d

# Stop everything
docker compose down
```

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Web app (phone input, avatar, transcript, tool calls) |
| Backend | (no port exposed) | Connects outbound to LiveKit Cloud via WebRTC |

## Running Tests

```bash
cd ai-voice-agent-backend

# Run all 47 tests
uv run pytest -v

# Run specific test file
uv run pytest tests/test_slot_generator.py -v

# Run via Docker
docker compose --profile testing run --rm tests
```

### Test Coverage (47 tests)

| Module | Tests | What's Tested |
|--------|-------|---------------|
| `tools/slot_generator.py` | 11 | Weekday-only slots, business hours (9-5), 30-min intervals, weekend skipping, Saturday start |
| `tools/appointment_tools.py` | 11 | User lookup, slot filtering, booking, double-booking prevention, cancel, modify with conflict check |
| `models.py` | 6 | ToolCallEvent creation, JSON serialization, bytes encoding, timestamp format, status validation |
| `agent_definition.py` | 12 | All 7 tools return JSON, publish start/complete events, empty args become None, error handling |
| `conftest.py` | -- | MockSupabaseClient, MockSupabaseQuery, mock LiveKit room/context fixtures |

## Deployment

### Backend -> Railway

1. Push `ai-voice-agent-backend/` to a GitHub repo
2. Connect to [Railway](https://railway.app) and import the repo
3. Set all environment variables from `.env.example`
4. Railway auto-detects the `Dockerfile` and deploys
5. Agent registers with LiveKit Cloud automatically on startup

### Frontend -> Vercel

1. Push `ai-voice-agent-frontend/` to a GitHub repo
2. Import in [Vercel](https://vercel.com)
3. Set environment variables: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
4. Vercel auto-detects Next.js and deploys

## Conversation Flow

```
Agent: "Hello! I'm Dr. Ava, your appointment scheduling assistant.
        Could you please provide your phone number?"

User:  "Sure, it's +1234567890"
        -> [identify_user] ...done

Agent: "Welcome back, John! How can I help you today?"

User:  "I'd like to book an appointment for next Monday"
        -> [fetch_slots] ...done

Agent: "I have these slots available on Monday February 16th:
        9:00 AM, 9:30 AM, 10:00 AM... Which works best?"

User:  "10 AM please, for a general checkup"
        -> [book_appointment] ...done

Agent: "Your appointment is confirmed for Monday Feb 16 at 10:00 AM
        with Dr. Smith. Is there anything else?"

User:  "No, that's all. Thanks!"
        -> [end_conversation] ...done

        Summary: Booked appointment for John (+1234567890)
        on 2026-02-16 at 10:00 with Dr. Smith for general checkup
```

## Environment Variables

### Root (`.env`) -- docker-compose build args

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

### Backend (`ai-voice-agent-backend/.env`)

```env
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# Speech
DEEPGRAM_API_KEY=your-deepgram-key
CARTESIA_API_KEY=your-cartesia-key

# Avatar
TAVUS_API_KEY=your-tavus-key
TAVUS_REPLICA_ID=your-replica-id
TAVUS_PERSONA_ID=your-persona-id

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### Frontend (`ai-voice-agent-frontend/.env.local`)

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

## License

MIT
