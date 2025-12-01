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

## Jira Integration Setup

The bot can query Jira tickets and notify your tech team channel when Jira is mentioned.

### 1. Get Your Jira API Token

For **Jira Cloud**:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "FinStackAI Bot")
4. Copy the token (you won't see it again!)

### 2. Configure Environment Variables

Add these to your `backend/app/.env` file:

```bash
# Jira Configuration
JIRA_DOMAIN="yourcompany.atlassian.net"
JIRA_EMAIL="your-email@company.com"
JIRA_API_TOKEN="your_api_token_here"
JIRA_PROJECT_KEY="TECH"  # Optional: default project to query

# Slack Tech Team Channel
SLACK_TECH_CHANNEL_ID="C0123456789"  # Channel ID for tech team notifications
```

### 3. How It Works

- When users mention keywords like "jira", "ticket", "bug", "task" in chat, the bot will:
  1. Query Jira for relevant tickets
  2. Include ticket information in the AI response
  3. **Send a notification to the tech team Slack channel** (not the default channel)
  
- Regular messages (without Jira keywords) still go to the default Slack channel

### 4. Finding Your Slack Channel ID

1. Open Slack in a browser
2. Navigate to the channel
3. Look at the URL: `https://app.slack.com/client/T.../C0123456789`
4. The part starting with `C` is your channel ID

### 5. Test It

Send a message in the chat like:
- "Show me the latest Jira tickets"
- "What bugs are open?"
- "List all tasks in TECH project"

The bot will query Jira and notify your tech team channel!
