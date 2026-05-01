import json
import logging
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

class FirebaseReader:
    def __init__(self, creds_json):
        self.db = None
        if not creds_json:
            logger.error("Firebase Credentials missing!")
            return
        try:
            cred_dict = json.loads(creds_json)
            cred = credentials.Certificate(cred_dict)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("✅ Firebase Reader connected (read-only)")
        except Exception as e:
            logger.error(f"❌ Firebase Init Error: {e}")
    
    def get_recent_resolved_bets(self, days_back=30, limit=100):
        try:
            cutoff = datetime.now() - timedelta(days=days_back)
            
            # Fixed: Use keyword argument for filter
            docs = self.db.collection('resolved_bets') \
                .where(filter=firestore.FieldFilter('resolution_timestamp', '>=', cutoff)) \
                .order_by('resolution_timestamp', direction=firestore.Query.DESCENDING) \
                .limit(limit) \
                .stream()
            
            bets = []
            for doc in docs:
                data = doc.to_dict()
                data['match_id'] = doc.id
                bets.append(data)
            
            logger.info(f"Fetched {len(bets)} resolved bets from last {days_back} days")
            return bets
        except Exception as e:
            logger.error(f"Failed to fetch bets: {e}")
            return []
    
    def get_unresolved_bets_count(self):
        try:
            count = len(self.db.collection('unresolved_bets').limit(10).get())
            return count
        except:
            return 0
    
    def get_stats_summary(self):
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Fixed: Use keyword argument for filter
            today_bets = self.db.collection('resolved_bets') \
                .where(filter=firestore.FieldFilter('resolution_timestamp', '>=', today)) \
                .limit(100) \
                .get()
            
            wins = sum(1 for doc in today_bets if doc.to_dict().get('outcome') == 'win')
            losses = len(today_bets) - wins
            
            return {
                'today_bets': len(today_bets),
                'today_wins': wins,
                'today_losses': losses
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}