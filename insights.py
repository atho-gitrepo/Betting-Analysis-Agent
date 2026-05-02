import logging
from transformers import pipeline
import torch

logger = logging.getLogger(__name__)

_summarizer = None

def get_summarizer():
    global _summarizer
    if _summarizer is None:
        logger.info("Loading local LLM (T5-small)...")
        try:
            torch.set_grad_enabled(False)
            _summarizer = pipeline(
                "summarization",
                model="t5-small",
                device=-1,
                model_kwargs={"torch_dtype": torch.float32}
            )
            logger.info("✅ Local LLM loaded")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            _summarizer = "error"
    return _summarizer if _summarizer != "error" else None

def generate_insights(bets):
    """Generate betting insights using local T5 model"""
    if not bets:
        return "No data available for analysis."
    
    # Calculate statistics
    total = len(bets)
    wins = sum(1 for b in bets if b.get('outcome') == 'win')
    win_rate = wins / total if total > 0 else 0
    net_profit = sum(b.get('stake', 0) for b in bets if b.get('outcome') == 'win') - \
                 sum(b.get('stake', 0) for b in bets if b.get('outcome') != 'win')
    
    # League performance
    league_perf = {}
    for b in bets:
        league = b.get('league', 'Unknown')
        # Clean league name for display
        league = league.replace(',', '').strip()
        if league not in league_perf:
            league_perf[league] = {'wins': 0, 'losses': 0}
        if b.get('outcome') == 'win':
            league_perf[league]['wins'] += 1
        else:
            league_perf[league]['losses'] += 1
    
    # Find best/worst leagues
    league_scores = [(l, stats['wins'] - stats['losses']) for l, stats in league_perf.items()]
    best_league = max(league_scores, key=lambda x: x[1])[0] if league_scores else "None"
    worst_league = min(league_scores, key=lambda x: x[1])[0] if league_scores else "None"
    
    # Clean league names (remove commas)
    best_league = best_league.replace(',', '')
    worst_league = worst_league.replace(',', '')
    
    # Count high sequence losses
    high_seq_losses = sum(1 for b in bets if b.get('match_sequence', 1) >= 3 and b.get('outcome') == 'loss')
    
    # Create clean insight text (no markdown formatting here)
    insight = f"💰 {wins}/{total} wins | {win_rate*100:.0f}% win rate | ${net_profit:.0f} profit\n"
    insight += f"🏆 Best: {best_league} | Worst: {worst_league}\n"
    insight += f"⚠️ {high_seq_losses} high-risk chases"
    
    # Add recommendation based on performance
    if high_seq_losses > 5:
        insight += "\n📉 Recommendation: Reduce chase level to 3"
    elif win_rate > 0.65:
        insight += "\n📈 Recommendation: Maintain current strategy"
    elif win_rate < 0.45:
        insight += "\n📉 Recommendation: Review league filters"
    
    return insight