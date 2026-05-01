import logging
import re
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
            # Cache for existing select options
            self.existing_options = {}
            self.load_existing_select_options()
    
    def clean_league_name(self, league_name):
        """Remove invalid characters for Notion Select property"""
        if not league_name:
            return "Other"
        
        # Remove commas (Notion doesn't allow them in select options)
        cleaned = league_name.replace(",", "")
        
        # Replace other problematic characters
        cleaned = cleaned.replace("/", "-")
        cleaned = cleaned.replace("&", "and")
        cleaned = cleaned.replace("'", "")
        cleaned = cleaned.replace('"', "")
        
        # Trim whitespace and limit length (Notion max 100 chars)
        cleaned = cleaned.strip()[:100]
        
        return cleaned if cleaned else "Other"
    
    def load_existing_select_options(self):
        """Fetch existing league options from Notion"""
        if not self.notion:
            return
        
        try:
            database = self.notion.databases.retrieve(self.database_id)
            league_property = database.get('properties', {}).get('League', {})
            
            if league_property.get('type') == 'select':
                options = league_property.get('select', {}).get('options', [])
                self.existing_options = {opt['name']: opt for opt in options}
                logger.info(f"Loaded {len(self.existing_options)} existing league options")
        except Exception as e:
            logger.error(f"Failed to load options: {e}")
    
    def ensure_league_option_exists(self, league_name):
        """Dynamically add league option if it doesn't exist"""
        cleaned_name = self.clean_league_name(league_name)
        
        if cleaned_name in self.existing_options:
            return cleaned_name
        
        try:
            # Update database to add new select option
            current_db = self.notion.databases.retrieve(self.database_id)
            league_prop = current_db.get('properties', {}).get('League', {})
            current_options = league_prop.get('select', {}).get('options', [])
            
            # Add new option
            new_options = current_options + [{"name": cleaned_name}]
            
            # Update database
            self.notion.databases.update(
                database_id=self.database_id,
                properties={
                    "League": {
                        "select": {
                            "options": new_options
                        }
                    }
                }
            )
            
            # Update cache
            self.existing_options[cleaned_name] = {"name": cleaned_name}
            logger.info(f"Added new league option: {cleaned_name}")
            return cleaned_name
            
        except Exception as e:
            logger.warning(f"Could not add league option '{cleaned_name}': {e}")
            # Fallback to "Other" if can't add
            return "Other"
    
    def bet_exists(self, match_id):
        """Check if bet already in Notion using match_id property"""
        if not self.notion:
            return True
        
        try:
            # Search by Match ID
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
        """Add a single bet to Notion with cleaned league name"""
        if not self.notion:
            return False
        
        # Clean and ensure league option exists
        original_league = bet_data.get("league", "Unknown")
        cleaned_league = self.ensure_league_option_exists(original_league)
        
        properties = {
            "Match": {"title": [{"text": {"content": bet_data.get("match_name", "Unknown")[:200]}}]},
            "League": {"select": {"name": cleaned_league}},
            "Score 36'": {"rich_text": [{"text": {"content": bet_data.get("36_score", "?")}}]},
            "HT Score": {"rich_text": [{"text": {"content": bet_data.get("result_score", "?")}}]},
            "Stake": {"number": float(bet_data.get("stake", 0))},
            "Outcome": {"select": {"name": bet_data.get("outcome", "loss")}},
            "Sequence": {"number": int(bet_data.get("match_sequence", 1))},
            "Date": {"date": {"start": bet_data.get("resolved_at", "").split()[0]}},
            "Match ID": {"rich_text": [{"text": {"content": str(bet_data.get("match_id", ""))}}]},
        }
        
        try:
            self.notion.pages.create(
                parent={"database_id": self.database_id}, 
                properties=properties
            )
            logger.info(f"✅ Synced to Notion: {bet_data.get('match_name', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Notion add failed: {e}")
            return False
    
    def sync_bets(self, bets):
        """Sync multiple bets (skip existing)"""
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
