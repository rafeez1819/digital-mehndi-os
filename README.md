# 🌸 Digital Mehndi OS

> *A living emotional operating system — one model, one user, zero payload.*

![Python](https://img.shields.io/badge/Python-3.11+-8B4513?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2+-2E8B57?style=flat-square&logo=django&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-Channels-D4832A?style=flat-square)
![Claude](https://img.shields.io/badge/Claude-Anthropic-FF9933?style=flat-square)
![SQLite](https://img.shields.io/badge/Memory-SQLite-C1601A?style=flat-square)

---

## What is this?

**Digital Mehndi OS** is a full-stack emotional intelligence platform where:

- Every interaction is processed through a **VAD (Valence–Arousal–Dominance)** emotional kernel
- A **living mandala interface** breathes and transforms with your emotional state in real-time
- All emotions are **woven into permanent SQLite memory** — the system knows you over time
- **Anthropic Claude** responds to you from within your emotional state — not just as a chatbot, but as a resonant soul
- **WebSocket streaming** delivers sub-50ms emotional packets to the frontend

The interface is inspired by **Mehndi (henna art)** — intricate, alive, and personal.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (HTML/JS)                │
│  Mandala Canvas · VAD Sliders · Henna Vine · Avatar │
└────────────────────┬────────────────────────────────┘
           WebSocket │  (ws://host/ws/emotion/)
┌────────────────────▼────────────────────────────────┐
│              DJANGO CHANNELS (ASGI)                 │
│  EmotionStreamConsumer  ←→  EmotionalKernel         │
│         ↓                        ↓                  │
│   EmotionMemory          claude-sonnet-4-6          │
│   EmotionalProfile                                  │
└─────────────────────────────────────────────────────┘
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `emotional_kernel/kernel.py` | VAD processing, capsule selection, Claude prompting |
| `memory/models.py` | SQLite emotion history & per-user profiles |
| `websocket/consumers.py` | Real-time WebSocket packet streaming |
| `api/views.py` | REST endpoints for sync access |
| `frontend/static/js/ws-client.js` | Frontend WebSocket client |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/digital-mehndi-os.git
cd digital-mehndi-os

# 2. Setup (creates venv, installs deps, runs migrations)
bash scripts/setup.sh

# 3. Add your Anthropic API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key" >> .env

# 4. Run
source venv/bin/activate
cd backend
python manage.py runserver

# 5. Open
open http://localhost:8000
```

---

## WebSocket API

Connect to `ws://localhost:8000/ws/emotion/<user_id>/`

### Send a message
```json
{ "type": "message", "text": "I feel something beautiful today", "use_claude": true }
```

### Override VAD manually
```json
{ "type": "vad_override", "valence": 0.8, "arousal": 0.6, "dominance": 0.5 }
```

### Receive an emotion packet
```json
{
  "type": "emotion_packet",
  "vad": { "valence": 0.72, "arousal": 0.54, "dominance": 0.48 },
  "emotion_label": "Joy",
  "emotion_color": "rgb(183, 96, 34)",
  "mandala_petals": 18,
  "vine_curve": 0.29,
  "pattern_hash": "knot-a3f8c12b",
  "latency_ms": 23.4,
  "response_text": "The pattern blooms where your words fall...",
  "capsules": [...]
}
```

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/emotion/process/` | Sync emotion processing |
| `GET`  | `/api/emotion/history/` | Fetch emotion history |
| `GET`  | `/api/profile/<user_id>/` | Get emotional profile |
| `GET`  | `/api/health/` | Health check |

---

## Roadmap

- [ ] Multi-user sessions
- [ ] Redis channel layer for production scale
- [ ] Emotion export (JSON / CSV)
- [ ] Self-upgrade: profile-driven prompt adaptation
- [ ] Mobile PWA

---

## Philosophy

> *Code should breathe like henna on skin.*
> *Every pattern is unique. Every interaction is remembered.*
> *One model. One user. One soul.*

---

## License

MIT — paint freely. 🌸
