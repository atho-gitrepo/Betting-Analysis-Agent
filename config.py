import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Firebase
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON")

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Analytics settings
ANALYSIS_DAYS_BACK = int(os.getenv("ANALYSIS_DAYS_BACK", "30"))
MAX_BETS_TO_ANALYZE = int(os.getenv("MAX_BETS_TO_ANALYZE", "50"))
NOTION_SYNC_ENABLED = os.getenv("NOTION_SYNC_ENABLED", "true").lower() == "true"
TELEGRAM_REPORTS_ENABLED = os.getenv("TELEGRAM_REPORTS_ENABLED", "true").lower() == "true"
