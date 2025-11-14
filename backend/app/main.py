# app/main.py
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json                                                  # ⬅️ add this
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from stream_chat import StreamChat
from groq import Groq 
import os

app = FastAPI()

# Allow your Next.js app to talk to FastAPI in dev
origins = [
    "http://localhost:3000",   # Next.js dev
    "http://127.0.0.1:3000",
    # Add your production frontend URL later, e.g. "https://yourapp.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== #
#      Chat setup      #
# ==================== #
# Load .env from the project root or backend folder
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

STREAM_API_KEY = os.getenv("STREAM_API_KEY")
STREAM_API_SECRET = os.getenv("STREAM_API_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

if not STREAM_API_KEY or not STREAM_API_SECRET:
    raise RuntimeError("STREAM_API_KEY / STREAM_API_SECRET not set in .env")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in .env") 

stream_client = StreamChat(
    api_key=STREAM_API_KEY,
    api_secret=STREAM_API_SECRET,
)


# ==================== #
#       LLM setup      #
# ==================== #

groq_client = Groq(api_key=GROQ_API_KEY)

# Simple system prompt for the AI
FINSTACK_SYSTEM_PROMPT = (
    "You are FinStack AI Support. Help users understand dashboards, metrics, "
    "and financial concepts in this app. Be concise (2-4 sentences), friendly, "
    "and avoid heavy legal disclaimers unless necessary."
)

# ========== # 
#   Models   #
# ========== # 

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

class StreamTokenRequest(BaseModel):
    user_id: str
    name: str | None = None
    image: str | None = None

class StreamTokenResponse(BaseModel):
    api_key: str
    token: str
    user: dict

class ClearChatRequest(BaseModel):
    user_id: str

# ========== # 
#   Routes   #
# ========== # 

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    """
    This is where you'd:
    - Verify Stream webhook (if you're using webhooks)
    - Or talk to Stream's API / your model / etc.
    For now, we’ll just echo something back.
    """
    reply_text = f"Echo from FastAPI: you said '{payload.message}' (user: {payload.user_id})"
    return ChatResponse(reply=reply_text)

@app.post("/stream/token", response_model=StreamTokenResponse)
def get_stream_token(payload: StreamTokenRequest):
    """
    Called by your frontend to get a Stream user token.
    Secrets stay on the server.
    """
    user = {"id": payload.user_id}
    if payload.name:
        user["name"] = payload.name
    if payload.image:
        user["image"] = payload.image

    # ensure user exists / is updated
    stream_client.upsert_user(user)

    # create a signed JWT token for this user
    token = stream_client.create_token(payload.user_id)

    return StreamTokenResponse(api_key=STREAM_API_KEY, token=token, user=user)

@app.post("/stream/clear-chat")
def clear_chat(payload: ClearChatRequest):
    """
    Clear all messages in the user's support channel.
    """
    try:
        user_id = payload.user_id
        channel_id = f"support-{user_id}"
        
        # Get the channel
        channel = stream_client.channel("messaging", channel_id)
        
        # Truncate (delete all messages)
        channel.truncate()
        
        print(f"🗑️  Cleared chat for user: {user_id}")
        return {"status": "success", "message": "Chat cleared"}
        
    except Exception as e:
        print(f"❌ Error clearing chat: {e}")
        return {"status": "error", "error": str(e)}

@app.post("/stream/webhook")
async def stream_webhook(request: Request, x_signature: str = Header(None)):
    """
    Webhook endpoint for Stream Chat.
    Stream will POST events here (e.g. message.new).
    We:
      - verify signature
      - ignore our own bot messages
      - call Groq for an AI reply
      - show 'bot is typing…' while Groq is working
      - send the final AI answer as FinStackAI
    """
    raw_body = await request.body()

    # ✅ Verify the webhook really came from Stream
    if not x_signature or not stream_client.verify_webhook(raw_body, x_signature):
        raise HTTPException(status_code=401, detail="Invalid Stream signature")

    payload = json.loads(raw_body)
    event_type = payload.get("type")

    if event_type != "message.new":
        # Only react to new messages
        return {"received": True}

    message = payload.get("message", {}) or {}
    user = message.get("user", {}) or {}
    user_id = user.get("id")
    text = (message.get("text") or "").strip()
    cid = payload.get("cid")  # e.g. "messaging:support-demo_user_1"

    # 🔴 Don't respond to our own bot messages
    if user_id == "FinStackAI":
        return {"received": True}

    # 🧼 Ignore non-regular messages (system, deleted, etc.)
    if message.get("type") != "regular":
        return {"received": True}

    if not (cid and text and user_id):
        return {"received": True}

    # Split "messaging:support-demo_user_1" -> ("messaging", "support-demo_user_1")
    channel_type, channel_id = cid.split(":", 1)
    channel = stream_client.channel(channel_type, channel_id)

    # 1) Tell Stream "FinStackAI is typing…" so the UI shows a typing indicator
    try:
        channel.send_event(
            {"type": "typing.start"},
            "FinStackAI",       # user_id of the bot
        )
    except Exception as e:
        print("⚠️ typing.start failed:", e)

    # 2) Call Groq to get an AI response
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",   # nice fast model 
            messages=[
                {"role": "system", "content": FINSTACK_SYSTEM_PROMPT},
                # You can add more history here if you want multi-turn context:
                # {"role": "user", "content": "previous message..."},
                {"role": "user", "content": text},
            ],
        )
        bot_text = completion.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Groq error:", e)
        bot_text = (
            "I had trouble reaching the AI engine just now, "
            "but I did receive your message:\n\n" + text
        )

    # 3) Stop typing + send the final AI message
    try:
        channel.send_event(
            {"type": "typing.stop"},
            "FinStackAI",
        )
    except Exception as e:
        print("⚠️ typing.stop failed:", e)

    channel.send_message(
        {
            "text": bot_text,
            "ai_generated": True,   # optional custom flag
        },
        "FinStackAI",              # message from this user_id
    )

    return {"received": True}

# ================================== #
#     REPLIES WITH USER'S MESSAGE    #
# ================================== #
# @app.post("/stream/webhook")
# async def stream_webhook(request: Request, x_signature: str = Header(None)):
#     """
#     Webhook endpoint for Stream Chat.
#     Stream will POST events here (e.g. message.new).
#     """
#     raw_body = await request.body()

#     # ✅ Verify the webhook really came from Stream
#     if not x_signature or not stream_client.verify_webhook(raw_body, x_signature):
#         raise HTTPException(status_code=401, detail="Invalid Stream signature")

#     payload = json.loads(raw_body)
#     event_type = payload.get("type")

#     if event_type == "message.new":
#         message = payload.get("message", {}) or {}
#         user = message.get("user", {}) or {}
#         user_id = user.get("id")
#         text = message.get("text", "") or ""
#         cid = payload.get("cid")  # e.g. "messaging:support-demo_user_1"

#         # 🔴 IMPORTANT: don't respond to our own bot messages
#         if user_id == "FinStackAI":
#             return {"received": True}

#         # (optional) ignore non-regular messages
#         if message.get("type") != "regular":
#             return {"received": True}

#         if cid and text and user_id:
#             # Split "messaging:support-demo_user_1" -> ("messaging", "support-demo_user_1")
#             channel_type, channel_id = cid.split(":", 1)
#             channel = stream_client.channel(channel_type, channel_id)

#             bot_text = f"Hey {user_id}, you said: {text}"
#             channel.send_message(
#                 {"text": bot_text},
#                 "FinStackAI",  # bot user_id
#             )

#     return {"received": True}