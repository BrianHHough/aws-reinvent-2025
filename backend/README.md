# FastAPI Python Server

## Set up Virtual Environment

Create and activate the virtualenv:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

Upgrade `pip` and install deps:

```bash
pip install --upgrade pip
pip install fastapi "uvicorn[standard]" python-dotenv
```

Create a `requirements.txt` file to lock deps:

```bash
pip freeze > requirements.txt
```

## Install Deps for chat

```bash
pip install stream-chat python-dotenv groq
```

## Install Client-Side Daemon via CloudFlare

See Documentation of the [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/)

```bash
brew install cloudflared
```

## Launch the Server

### Run the FastAPI Server: Terminal #1

```bash
python -m uvicorn app.main:app --reload --port 8000
```

^ Important to use `python` first so the Python for the venv is used

### Run the CloudFlare Tunnel: Terminal #2

This will generate a URL:

```bash
cloudflared tunnel --url http://localhost:8000
```

Take that URL and put it in the [Websocket page on Stream](https://dashboard.getstream.io/app/1448201/chat/overview)

The URL will look something like this:

```bash
https://xxxxxxxxxx.trycloudflare.com
```

Verify it is running on your url:
`https://xxxxxxxxxx.trycloudflare.com/health`

You should see:

```json
{"status":"ok"}
```
