import logging
from notion_client import Client
from config import NOTION_TOKEN, NOTION_DATABASE_ID, NOTION_SYNC_ENABLED

logger = logging.getLogger(__name__)

class NotionSync:
    def __init__(self):
        if not NOTION_SYNC_ENABLED:
            logger.info("Notion sync disabled")
            self.notion = None
            return
        
        if not NOTION_TOKEN or not NOTION_DATABASE_ID:
            logger.warning("Notion credentials missing")
            self.notion = None
        else:
            self.notion = Client(auth=NOTION_TOKEN)
            self.database_id = NOTION_DATABASE_ID
    
    def bet_exists(self, match_id):
        if not self.notion:
            return True
        
        try:
            query = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Match ID",
                    "rich_text": {"equals": str(match_id)}
                }
            )
            return len(query["results"]) > 0
        except Exception as e:
            logger.error(f"Notion query error: {e}")
            return False
    
    def add_bet(self, bet_data):
        if not self.notion:
            return False
        
        properties = {
            "Match": {"title": [{"text": {"content": bet_data.get("match_name", "Unknown")}}]},
            "League": {"select": {"name": bet_data.get("league", "Unknown")}},
            "Score 36'": {"rich_text": [{"text": {"content": bet_data.get("36_score", "?")}}]},
            "HT Score": {"rich_text": [{"text": {"content": bet_data.get("result_score", "?")}}]},
            "Stake": {"number": float(bet_data.get("stake", 0))},
            "Outcome": {"select": {"name": bet_data.get("outcome", "loss")}},
            "Sequence": {"number": int(bet_data.get("match_sequence", 1))},
            "Date": {"date": {"start": bet_data.get("resolved_at", "").split()[0]}},
            "Match ID": {"rich_text": [{"text": {"content": str(bet_data.get("match_id", ""))}}]},
        }
        
        try:
            self.notion.pages.create(parent={"database_id": self.database_id}, properties=properties)
            logger.info(f"✅ Synced to Notion: {bet_data.get('match_name')}")
            return True
        except Exception as e:
            logger.error(f"Notion add failed: {e}")
            return False
    
    def sync_bets(self, bets):
        if not self.notion:
            return 0
        
        new_count = 0
        for bet in bets:
            match_id = bet.get('match_id')
            if match_id and not self.bet_exists(match_id):
                if self.add_bet(bet):
                    new_count += 1
        
        logger.info(f"Synced {new_count} new bets to Notion")
        return new_count
