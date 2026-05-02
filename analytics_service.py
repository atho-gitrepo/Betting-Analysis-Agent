#!/usr/bin/env python3
import logging
import pandas as pd
from datetime import datetime, timedelta
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
    
    # Fetch bets for analysis
    bets = fb.get_recent_resolved_bets(
        days_back=ANALYSIS_DAYS_BACK, 
        limit=MAX_BETS_TO_ANALYZE
    )
    
    if not bets:
        logger.info("No resolved bets found")
        # Send report even with no data
        empty_df = pd.DataFrame()
        empty_stats = {'unresolved_count': unresolved_count, 'today_bets': 0, 'today_profit': 0}
        send_daily_report("No betting activity in the last 30 days.", empty_df, empty_stats)
        return
    
    # Convert to DataFrame for sequence analysis
    df = pd.DataFrame(bets)
    df['resolved_at'] = pd.to_datetime(df['resolved_at'])
    df['date'] = df['resolved_at'].dt.date
    df['profit'] = df.apply(
        lambda x: x['stake'] if x['outcome'] == 'win' else -x['stake'], 
        axis=1
    )
    
    logger.info(f"Analyzing {len(bets)} bets")
    
    # Sync to Notion (if enabled)
    if NOTION_SYNC_ENABLED:
        notion = NotionSync()
        notion.sync_bets(bets)
    
    # Generate AI insights
    insights = generate_insights(bets)
    logger.info("AI insights generated")
    
    # Calculate today's stats
    today = datetime.now().date()
    today_bets = df[df['date'] == today] if not df.empty else pd.DataFrame()
    today_profit = today_bets['profit'].sum() if not today_bets.empty else 0
    
    # Get basic stats
    stats = fb.get_stats_summary()
    stats['unresolved_count'] = unresolved_count
    stats['today_profit'] = today_profit
    
    # Send comprehensive report with sequence patterns
    send_daily_report(insights, df, stats)
    
    logger.info("=== Analytics Service Completed ===")

if __name__ == "__main__":
    main()