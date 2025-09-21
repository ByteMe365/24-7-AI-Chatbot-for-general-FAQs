import json
import boto3
import urllib.request
import urllib.error
from urllib.parse import parse_qs
from botocore.exceptions import ClientError
import base64, traceback
import os
from datetime import datetime, time
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    ZoneInfo = None

# ====== Constants ======
SECRET_NAME = os.getenv("SECRET_NAME")
TABLE_NAME  = os.getenv("TABLE_NAME")
REGION_NAME = os.getenv("REGION_NAME")
TIME_ZONE   = os.getenv("TIME_ZONE")

# ====== Secrets (Telegram token) ======
def get_secret(secret_name, region_name):
    sm = boto3.client("secretsmanager", region_name=region_name)
    try:
        resp = sm.get_secret_value(SecretId=secret_name)
        return json.loads(resp.get("SecretString") or "{}")
    except ClientError as e:
        print("SecretsManager error:", repr(e))
        traceback.print_exc()
        return {}

secrets  = get_secret(SECRET_NAME, REGION_NAME)
TG_TOKEN = secrets.get("TELEGRAM_BOT_TOKEN")

# ====== AWS ======
dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
table     = dynamodb.Table(TABLE_NAME)

# ====== FAQ cache ======
FAQ_CACHE = None

def fetch_all():
    items = []
    try:
        resp = table.scan()
        items.extend(resp.get("Items", []))
        while "LastEvaluatedKey" in resp:
            resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []))
    except Exception as e:
        print("DynamoDB scan error:", repr(e))
        traceback.print_exc()
    return items

def get_faqs():
    global FAQ_CACHE
    if FAQ_CACHE is None:
        FAQ_CACHE = fetch_all()
    return FAQ_CACHE

# ====== Hours helpers (dynamic “today/now”) ======
WEEKLY_HOURS = {
    0: (time(9, 0),  time(21, 0)),   # Monday
    1: (time(9, 0),  time(21, 0)),   # Tuesday
    2: (time(9, 0),  time(21, 0)),   # Wednesday
    3: (time(9, 0),  time(21, 0)),   # Thursday
    4: (time(9, 0),  time(21, 0)),   # Friday
    5: (time(9, 0),  time(21, 0)),   # Saturday
    6: (time(10, 0), time(19, 0)),   # Sunday
}

def _now_local():
    if ZoneInfo:
        return datetime.now(ZoneInfo(TIME_ZONE))
    return datetime.utcnow()

def _fmt_t(t: time) -> str:
    dt = datetime.combine(datetime.today(), t)
    # Try Linux style first, then Windows, else 24h
    try:
        return dt.strftime("%-I:%M %p")
    except Exception:
        s = dt.strftime("%I:%M %p")
        return s.lstrip("0") if s.startswith("0") else s

def hours_message_for_today():
    now = _now_local()
    day_idx = now.weekday()
    hours = WEEKLY_HOURS.get(day_idx)
    day_name = now.strftime("%A")
    if not hours:
        return f"Sorry.. We’re closed today ({day_name})."

    open_t, close_t = hours
    open_dt  = now.replace(hour=open_t.hour,  minute=open_t.minute,  second=0, microsecond=0)
    close_dt = now.replace(hour=close_t.hour, minute=close_t.minute, second=0, microsecond=0)

    if now < open_dt:
        return f"We’re closed now. We open today ({day_name}) at {_fmt_t(open_t)}."
    elif now >= close_dt:
        return f"We’re closed now. Today ({day_name}) we were open {_fmt_t(open_t)}–{_fmt_t(close_t)}."
    else:
        return f"We’re open now until {_fmt_t(close_t)}."

def looks_like_today_hours(q: str) -> bool:
    ql = (q or "").lower()
    hints_any = any(w in ql for w in ["today", "now", "open now", "close now", "closing", "closing time", "Right Now"])
    hoursy    = any(w in ql for w in ["hour", "open", "close", "business hours", "operating"])
    return hoursy and (hints_any or "what time are you open today" in ql)



# ====== Improved matching for question1..16 ======

STOP = {
    "the","a","an","to","for","is","are","am","be","was","were",
    "do","does","did","you","your","our","we","i","it","of","on",
    "at","in","and","or","if","with","can","could","may","might",
    "shall","will","would","should","how","what","when","where",
    "which","who","whom","why"
}

def normalize(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in (s or ""))

def tokens(s: str):
    return [t for t in normalize(s).split() if t and t not in STOP]

def gather_questions(item):
    """Combine question, question2..question16 into one string."""
    parts = []
    for i in range(1, 17):   # question1 through question16
        key = "question" if i == 1 else f"question{i}"
        text = item.get(key)
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return " ".join(parts)



# ====== Matching (static FAQ) ======
def score_item(item, query):
    ql = (query or "").lower().strip()
    question_text = str(item.get("question", "")).lower().strip()
    if not question_text:
        return (0, 0)
    if ql == question_text:
        return (3, len(question_text))
    if ql in question_text or question_text in ql:
        return (2, len(question_text))
    qtoks = set(ql.split())
    itoks = set(question_text.split())
    overlap = len(qtoks & itoks)
    return (1 if overlap else 0, overlap)


    """
    Score similarity between user query and all question variants.
    Returns (score_level, overlap_count).
    """
    qtok = set(tokens(query))
    hay_raw = gather_questions(item)
    haytok = set(tokens(hay_raw))

    if not haytok:
        return (0, 0)

    overlap = len(qtok & haytok)

    # exact or substring match on any variant gets highest score
    qn = normalize(query)
    for i in range(1, 17):
        key = "question" if i == 1 else f"question{i}"
        txt = normalize(item.get(key, "") or "")
        if txt and (qn == txt or qn in txt or txt in qn):
            return (3, overlap or len(txt))

    # strong overlap
    if overlap >= 2:
        return (2, overlap)

    # weak overlap
    return (1 if overlap else 0, overlap)

def best_answer(user_text):
    query = (user_text or "").strip()
    if not query:
        return "Hi! Ask me about opening hours, delivery, or returns."
    best_item, best_score = None, (-1, 0)
    for it in get_faqs():
        s = score_item(it, query)
        if s > best_score:
            best_score, best_item = s, it
    if best_item and best_score[0] > 0:
        return best_item.get("answer", "No answer stored.")
    return "Sorry, I couldn’t find that. Try: opening hours, delivery, returns."

def choose_reply(user_text: str) -> str:
    if user_text and looks_like_today_hours(user_text):
        return hours_message_for_today()
    return best_answer(user_text)

# ====== Telegram send ======
def tg_send(chat_id: int, text: str, token: str):
    if not chat_id or not token:
        print("Missing chat_id or token:", chat_id, bool(token))
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        print("Telegram HTTP error:", e.read().decode("utf-8", "ignore"))
    except Exception as e:
        print("Telegram send exception:", repr(e))
        traceback.print_exc()

# ====== Event parsing ======
def parse_event_body(event):
    headers = { (k or "").lower(): v for k, v in (event.get("headers") or {}).items() }
    content_type = (headers.get("content-type") or "").lower()
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        try:
            body = base64.b64decode(body).decode("utf-8", "ignore")
        except Exception as e:
            print("Base64 decode failed:", repr(e))
    try:
        payload = body if isinstance(body, dict) else json.loads(body)
    except Exception:
        payload = {}
    return payload, content_type, body

def extract_message(payload):
    msg = payload.get("message") or payload.get("edited_message") or {}
    if not isinstance(msg, dict):
        msg = {}
    chat_id   = (msg.get("chat") or {}).get("id")
    user_text = msg.get("text", "")
    return chat_id, user_text

def handle_form_encoded(raw_body):
    form = parse_qs(raw_body)
    user_text = form.get("Body", [""])[0] or form.get("message", [""])[0]
    reply = choose_reply(user_text)
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply}</Message></Response>'
    return {"statusCode": 200, "headers": {"Content-Type": "text/xml"}, "body": twiml}

# ====== Handler ======
def lambda_handler(event, context):
    payload, content_type, raw_body = parse_event_body(event)
    chat_id, user_text = extract_message(payload)

    # Telegram webhook
    if chat_id:
        reply = choose_reply(user_text)          # <-- DO NOT overwrite later
        tg_send(chat_id, reply, TG_TOKEN)
        return {"statusCode": 200, "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"status": "ok"})}

    # Twilio-style form posts
    if "application/x-www-form-urlencoded" in content_type:
        return handle_form_encoded(raw_body)

    # Fallback: plain JSON { "message": "..." } for console/tests
    user_text = user_text or payload.get("message", "")
    reply = choose_reply(user_text)
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"reply": reply})}
