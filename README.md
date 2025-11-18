# AWS re:Invent 2025 - Read Team / Blue Team

## Quick Setup

See directory-specific README's for more context about setup instructions.

### 💻 Frontend

The app runs on: `http://localhost:3000`

```bash
cd frontend
npm run dev
```

### 🐍 Backend

The server runs on: `http://localhost:8000`

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

### 🔊 Middleware Tunnel

```bash
cloudflared tunnel --url http://localhost:8000
```

Look for the URL in this output:

```bash
https://xxxxxxxxxx.trycloudflare.com
```

Take that URL and put it in the [Websocket URL Section on the Stream Dashboard](https://dashboard.getstream.io/app/1448201/chat/overview) and add `/stream/webhook` to the end of the URL, like this:

```bash
https://xxxxxxxxxx.trycloudflare.com/stream/webhook
```
