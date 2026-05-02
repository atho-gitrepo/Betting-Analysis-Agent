import requests
import logging
from datetime import datetime, timedelta
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_REPORTS_ENABLED

logger = logging.getLogger(__name__)

def send_telegram_message(message):
    """Send message to Telegram"""
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

def format_sequence_pattern(bets_df):
    """Format last 7 days win/loss sequence pattern for Telegram"""
    today = datetime.now().date()
    last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    
    pattern_lines = []
    pattern_lines.append("📊 *LAST 7 DAYS SEQUENCE PATTERN*")
    pattern_lines.append("")
    
    for day in last_7_days:
        day_bets = bets_df[bets_df['date'] == day]
        
        if not day_bets.empty:
            # Get sequences in order
            sequences = day_bets.sort_values('resolved_at')[['match_sequence', 'outcome']].values.tolist()
            
            # Create pattern string with icons
            pattern = []
            for seq_num, outcome in sequences:
                if outcome == 'win':
                    pattern.append(f"✅ L{seq_num}")
                else:
                    pattern.append(f"❌ L{seq_num}")
            
            pattern_str = " → ".join(pattern)
            
            # Calculate day stats
            total_bets = len(day_bets)
            wins = len(day_bets[day_bets['outcome'] == 'win'])
            win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
            day_profit = day_bets['profit'].sum()
            
            profit_emoji = "🟢" if day_profit > 0 else "🔴" if day_profit < 0 else "⚪"
            
            day_name = day.strftime('%a')
            pattern_lines.append(f"*{day.strftime('%Y-%m-%d')} ({day_name})*")
            pattern_lines.append(f"└ {pattern_str}")
            pattern_lines.append(f"  {profit_emoji} {total_bets} bets | {wins} wins | Win Rate: {win_rate:.0f}% | P&L: ${day_profit:.2f}")
            pattern_lines.append("")
        else:
            day_name = day.strftime('%a')
            pattern_lines.append(f"*{day.strftime('%Y-%m-%d')} ({day_name})*")
            pattern_lines.append(f"└ ⚪ No bets placed")
            pattern_lines.append("")
    
    return "\n".join(pattern_lines)

def format_sequence_summary(bets_df):
    """Format summary of sequence patterns for last 7 days"""
    today = datetime.now().date()
    last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    
    # Collect all sequences from last 7 days
    all_patterns = []
    all_sequences = []
    
    for day in last_7_days:
        day_bets = bets_df[bets_df['date'] == day]
        if not day_bets.empty:
            sequences = day_bets.sort_values('resolved_at')['outcome'].tolist()
            all_patterns.extend(sequences)
            all_sequences.extend(day_bets.sort_values('resolved_at')['match_sequence'].tolist())
    
    if not all_patterns:
        return None
    
    # Calculate overall stats
    total_bets = len(all_patterns)
    wins = sum(1 for p in all_patterns if p == 'win')
    win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
    
    # Find patterns
    pattern_str = ''.join(['W' if p == 'win' else 'L' for p in all_patterns])
    
    # Find longest streaks
    max_win_streak = 0
    max_loss_streak = 0
    current_win = 0
    current_loss = 0
    
    for outcome in all_patterns:
        if outcome == 'win':
            current_win += 1
            current_loss = 0
            max_win_streak = max(max_win_streak, current_win)
        else:
            current_loss += 1
            current_win = 0
            max_loss_streak = max(max_loss_streak, current_loss)
    
    # Count high sequences (level 3+)
    high_sequences = sum(1 for s in all_sequences if s >= 3)
    
    summary_lines = []
    summary_lines.append("📈 *7-DAY SEQUENCE SUMMARY*")
    summary_lines.append("")
    summary_lines.append(f"📊 Total Bets: *{total_bets}*")
    summary_lines.append(f"✅ Wins: *{wins}* | ❌ Losses: *{total_bets - wins}*")
    summary_lines.append(f"🎯 Win Rate: *{win_rate:.1f}%*")
    summary_lines.append(f"📈 Pattern: `{pattern_str}`")
    summary_lines.append("")
    summary_lines.append(f"🔥 Longest Win Streak: *{max_win_streak}*")
    summary_lines.append(f"💀 Longest Loss Streak: *{max_loss_streak}*")
    summary_lines.append(f"⚠️ High Level Chases (3+): *{high_sequences}*")
    
    # Risk assessment
    if max_loss_streak >= 5:
        summary_lines.append("")
        summary_lines.append("🔴 *CRITICAL RISK*: 5+ consecutive losses detected!")
        summary_lines.append("→ Reset chase sequence immediately")
        summary_lines.append("→ Consider reducing stake by 50%")
    elif max_loss_streak >= 3:
        summary_lines.append("")
        summary_lines.append("⚠️ *WARNING*: Multiple consecutive losses")
        summary_lines.append("→ Reduce chase level to 1")
        summary_lines.append("→ Review league filters")
    elif win_rate >= 60:
        summary_lines.append("")
        summary_lines.append("🟢 *OPTIMAL*: Win rate above 60%")
        summary_lines.append("→ Strategy working well")
        summary_lines.append("→ Consider slight stake increase")
    
    return "\n".join(summary_lines)

def send_daily_report(insights, bets_df, stats):
    """Send comprehensive daily report with sequence patterns"""
    
    # Header
    header = "🤖 *BETTING ANALYTICS REPORT* 🤖\n"
    header += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    header += "─" * 30 + "\n\n"
    
    # Bot status
    bot_status = "📊 *BOT STATUS*\n"
    bot_status += f"• Active unresolved bets: *{stats.get('unresolved_count', 0)}*\n"
    bot_status += f"• Today's activity: *{stats.get('today_bets', 0)}* bets\n"
    bot_status += f"• Today's P&L: *${stats.get('today_profit', 0):.2f}*\n\n"
    
    # AI Insights from local LLM
    ai_section = "🧠 *AI ANALYSIS*\n"
    ai_section += f"{insights}\n\n"
    
    # Format sequence pattern for last 7 days
    sequence_pattern = format_sequence_pattern(bets_df)
    sequence_summary = format_sequence_summary(bets_df)
    
    # Combine all sections
    full_message = header + bot_status + ai_section + sequence_pattern
    
    if sequence_summary:
        full_message += "\n" + sequence_summary
    
    # Add closing recommendation
    full_message += "\n\n─" * 30 + "\n"
    full_message += "💡 *Next Steps*\n"
    
    # Dynamic recommendation based on recent performance
    if stats.get('today_profit', 0) < -50:
        full_message += "🔴 STOP: Daily loss limit exceeded. Stop betting for today.\n"
    elif stats.get('today_profit', 0) > 100:
        full_message += "🟢 PROFIT TARGET MET: Good time to stop and lock profits.\n"
    else:
        full_message += "📈 Continue monitoring. Dashboard available for detailed analysis.\n"
    
    full_message += "\n📊 Dashboard: *https://betting-analytics.up.railway.app*"
    
    # Split message if too long (Telegram limit 4096 chars)
    if len(full_message) > 4000:
        # Send in parts
        part1 = header + bot_status + sequence_pattern[:3000]
        part2 = sequence_summary + ai_section + "\n\n💡 *Next Steps*...\n" + full_message[-500:]
        
        send_telegram_message(part1)
        send_telegram_message(part2)
        return True
    
    return send_telegram_message(full_message)