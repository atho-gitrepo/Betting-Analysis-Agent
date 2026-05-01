#!/usr/bin/env python3
import logging
from datetime import datetime
from config import ANALYSIS_DAYS_BACK, MAX_BETS_TO_ANALYZE, NOTION_SYNC_ENABLED, FIREBASE_CREDENTIALS_JSON
from firebase_client import FirebaseReader
from notion_sync import NotionSync
from insights import generate_insights
from telegram_notifier import send_daily_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | Analytics | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Betting Analytics Service Started ===")
    
    fb = FirebaseReader(FIREBASE_CREDENTIALS_JSON)
    if not fb.db:
        logger.error("Failed to connect to Firebase")
        return
    
    unresolved_count = fb.get_unresolved_bets_count()
    logger.info(f"Current unresolved bets: {unresolved_count}")
    
    bets = fb.get_recent_resolved_bets(
        days_back=ANALYSIS_DAYS_BACK, 
        limit=MAX_BETS_TO_ANALYZE
    )
    
    if not bets:
        logger.info("No resolved bets found")
        send_daily_report("No betting activity in the last 30 days.", {'unresolved_count': unresolved_count})
        return
    
    logger.info(f"Analyzing {len(bets)} bets")
    
    if NOTION_SYNC_ENABLED:
        notion = NotionSync()
        notion.sync_bets(bets)
    
    insights = generate_insights(bets)
    logger.info("AI insights generated")
    
    stats = fb.get_stats_summary()
    stats['unresolved_count'] = unresolved_count
    
    send_daily_report(insights, stats)
    
    logger.info("=== Analytics Service Completed ===")

if __name__ == "__main__":
    main()
