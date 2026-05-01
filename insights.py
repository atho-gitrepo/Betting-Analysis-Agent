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
    if not bets:
        return "No data available for analysis."
    
    total = len(bets)
    wins = sum(1 for b in bets if b.get('outcome') == 'win')
    win_rate = wins / total if total > 0 else 0
    net_profit = sum(b.get('stake', 0) for b in bets if b.get('outcome') == 'win') - \
                 sum(b.get('stake', 0) for b in bets if b.get('outcome') != 'win')
    
    league_perf = {}
    for b in bets:
        league = b.get('league', 'Unknown')
        if league not in league_perf:
            league_perf[league] = {'wins': 0, 'losses': 0}
        if b.get('outcome') == 'win':
            league_perf[league]['wins'] += 1
        else:
            league_perf[league]['losses'] += 1
    
    league_scores = [(l, stats['wins'] - stats['losses']) for l, stats in league_perf.items()]
    best_league = max(league_scores, key=lambda x: x[1])[0] if league_scores else "None"
    worst_league = min(league_scores, key=lambda x: x[1])[0] if league_scores else "None"
    
    high_seq_losses = [b for b in bets if b.get('match_sequence', 1) >= 3 and b.get('outcome') == 'loss']
    
    context = f"""
📊 Betting Analysis:
- Total bets: {total}
- Win rate: {win_rate:.1%}
- Net profit/loss: ${net_profit:.2f}
- Best league: {best_league}
- Worst league: {worst_league}
- High-risk chase losses (sequence 3+): {len(high_seq_losses)}
"""
    
    summarizer = get_summarizer()
    if summarizer:
        try:
            result = summarizer(f"summarize: {context}", max_length=100, min_length=30, do_sample=False)
            insight = result[0]['summary_text']
            return f"{insight}\n\n{context}"
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
    
    recommendation = "Continue current strategy."
    if win_rate < 0.4:
        recommendation = "⚠️ Consider reducing stake or adjusting league filters."
    elif len(high_seq_losses) > 2:
        recommendation = "⚠️ Too many chase losses. Consider lowering MAX_CHASE_LEVEL to 3."
    elif win_rate > 0.6:
        recommendation = "✅ Strategy working well. Consider increasing original stake slightly."
    
    return f"""
📈 *AI Betting Insights*

{context}

💡 *Recommendation:* {recommendation}
"""
