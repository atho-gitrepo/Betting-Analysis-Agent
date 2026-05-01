import requests
import logging
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_REPORTS_ENABLED

logger = logging.getLogger(__name__)

def send_telegram_message(message):
    if not TELEGRAM_REPORTS_ENABLED:
        logger.info("Telegram reports disabled")
        return True
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials missing")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        response = requests.post(
            url, 
            data={
                'chat_id': TELEGRAM_CHAT_ID, 
                'text': message, 
                'parse_mode': 'Markdown'
            }, 
            timeout=15
        )
        if response.status_code == 200:
            logger.info("Telegram report sent")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Telegram exception: {e}")
        return False

def send_daily_report(insights, stats):
    header = "🤖 *Betting Analytics Report* 🤖\n\n"
    stats_section = f"📊 *Bot Status*\n• Unresolved bets: {stats.get('unresolved_count', 0)}\n• Today's activity: {stats.get('today_bets', 0)} bets\n\n"
    
    full_message = header + stats_section + insights
    return send_telegram_message(full_message)
