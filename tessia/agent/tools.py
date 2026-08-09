import os
import re
import json
import imaplib
import smtplib
import email
import webbrowser
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.text import MIMEText
from email.header import decode_header

CALENDAR_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vault", "calendar.json")

# Ensure vault directory and calendar JSON file exist
os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
if not os.path.exists(CALENDAR_FILE):
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)


# ==========================================
# 1. TIME, DATE & LIVE WEATHER TOOLS
# ==========================================

def get_current_datetime():
    """Returns today's exact date, time, and day of the week."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")


def get_live_weather(location="Hyderabad"):
    """Fetches real-time weather data using Open-Meteo free API."""
    try:
        # Clean location query
        clean_loc = location.lower().replace("weather", "").replace("in", "").replace("for", "").replace("today", "").strip()
        if not clean_loc:
            clean_loc = "Hyderabad"

        # 1. Geocode location name to Lat/Lon
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(clean_loc)}&count=1&language=en&format=json"
        req = urllib.request.Request(geo_url, headers={'User-Agent': 'TESSIA-Assistant/1.0'})
        with urllib.request.urlopen(req, timeout=10) as res:
            geo_data = json.loads(res.read().decode('utf-8'))

        if not geo_data.get("results"):
            return f"Could not find coordinates for location '{clean_loc}'.", None

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        city_name = geo_data["results"][0]["name"]
        country = geo_data["results"][0].get("country", "")

        # 2. Fetch current weather conditions
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        req_w = urllib.request.Request(weather_url, headers={'User-Agent': 'TESSIA-Assistant/1.0'})
        with urllib.request.urlopen(req_w, timeout=10) as res_w:
            w_data = json.loads(res_w.read().decode('utf-8'))

        current = w_data.get("current_weather", {})
        temp = current.get("temperature")
        wind = current.get("windspeed")
        
        return f"Current weather in {city_name}, {country}: {temp}°C with wind speeds of {wind} km/h.", None
    except Exception as e:
        return None, f"Failed to fetch live weather: {str(e)}"


# ==========================================
# 2. CALENDAR ENGINE (ADD, VIEW, DELETE, CLEAR)
# ==========================================

def get_calendar_events():
    """Reads all saved calendar events."""
    try:
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def add_calendar_event(title, date_str, time_str="10:00 AM"):
    """Adds a new event to TESSIA's local calendar engine."""
    events = get_calendar_events()
    new_event = {
        "id": len(events) + 1,
        "title": title,
        "date": date_str,
        "time": time_str,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    events.append(new_event)

    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)

    return f"Added event '{title}' to your calendar for {date_str} at {time_str}."


def delete_calendar_event(search_term):
    """Deletes matching event(s) from TESSIA's local calendar engine."""
    events = get_calendar_events()
    initial_count = len(events)
    
    clean_term = search_term.lower().replace("delete", "").replace("remove", "").replace("cancel", "").replace("calendar", "").replace("event", "").strip()
    
    updated_events = [
        e for e in events 
        if clean_term not in e["title"].lower() and str(e["id"]) != clean_term
    ]
    
    if len(updated_events) == initial_count:
        return f"No calendar events found matching '{clean_term}'."

    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_events, f, indent=2)

    return f"Removed event(s) matching '{clean_term}' from your calendar."


def clear_calendar():
    """Clears all events from the calendar."""
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    return "Cleared all events from your calendar."


# ==========================================
# 3. EMAIL TOOLS (IMAP / SMTP)
# ==========================================

def open_mail_app():
    """Opens default system mail client or webmail."""
    try:
        webbrowser.open("mailto:")
        return "Opened default mail application."
    except Exception as e:
        return f"Failed to open mail app: {e}"


def fetch_recent_emails(limit=3):
    """Fetches recent emails via IMAP."""
    email_user = os.environ.get("EMAIL_USER", "").strip()
    email_pass = os.environ.get("EMAIL_PASS", "").strip()
    imap_server = os.environ.get("IMAP_SERVER", "imap.gmail.com").strip()

    if not email_user or not email_pass:
        return None, "EMAIL_USER and EMAIL_PASS are not configured in your .env file."

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        if not messages[0]:
            mail.close()
            mail.logout()
            return [], None

        email_ids = messages[0].split()
        latest_ids = email_ids[-limit:]
        emails_data = []

        for e_id in reversed(latest_ids):
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    raw_subj = msg.get("Subject", "(No Subject)")
                    subject_parts = decode_header(raw_subj)
                    subject_str = ""
                    for part, encoding in subject_parts:
                        if isinstance(part, bytes):
                            subject_str += part.decode(encoding if encoding else "utf-8", errors="ignore")
                        else:
                            subject_str += str(part)

                    from_sender = msg.get("From", "Unknown Sender")

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                    emails_data.append({
                        "from": from_sender,
                        "subject": subject_str,
                        "body": body[:500]
                    })

        mail.close()
        mail.logout()
        return emails_data, None
    except Exception as e:
        return None, f"Failed to fetch emails: {str(e)}"


def send_email(to_email, subject, body):
    """Sends an email via SMTP."""
    email_user = os.environ.get("EMAIL_USER", "").strip()
    email_pass = os.environ.get("EMAIL_PASS", "").strip()
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", 587))

    if not email_user or not email_pass:
        return "EMAIL_USER and EMAIL_PASS are not configured in your .env file."

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = to_email

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, [to_email], msg.as_string())
        server.quit()
        return f"Email successfully sent to {to_email}."
    except Exception as e:
        return f"Failed to send email: {str(e)}"


# ==========================================
# 4. ARXIV RESEARCH & LIVE WEB TOOLS
# ==========================================

def fetch_arxiv_papers(topic="all", max_results=3):
    """Fetches newly published research papers from ArXiv API."""
    clean_topic = topic.replace("paper", "").replace("publication", "").replace("arxiv", "").replace("research", "").strip()
    if not clean_topic:
        clean_topic = "computer science"

    query = urllib.parse.quote(clean_topic)
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TESSIA-Assistant/1.0'})
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        papers = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            published = entry.find('atom:published', ns).text[:10]
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')[:300]
            link = entry.find('atom:id', ns).text

            papers.append({
                "title": title,
                "date": published,
                "summary": summary,
                "link": link
            })

        return papers, None
    except Exception as e:
        return None, f"Failed to fetch ArXiv publications: {str(e)}"


def search_live_web(query):
    """Searches live web content using DuckDuckGo HTML endpoint."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')

        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        clean_snippets = []
        for s in snippets[:4]:
            clean_text = re.sub(r'<[^>]+>', '', s).strip()
            if clean_text:
                clean_snippets.append(clean_text)

        if clean_snippets:
            return "\n".join(f"- {s}" for s in clean_snippets), None
        return f"Searched live web for '{query}'. No structured snippets returned.", None
    except Exception as e:
        return f"Web search queried for '{query}'.", None