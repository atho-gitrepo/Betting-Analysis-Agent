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

def clean_insights(insights_text):
    """Clean duplicate content from insights"""
    lines = insights_text.split('\n')
    cleaned_lines = []
    seen_content = set()
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Skip duplicate Betting Analysis headers
        if "📊 Betting Analysis:" in line:
            continue
            
        # Skip lines that are just dashes
        if line.strip() == "-" * len(line.strip()):
            continue
            
        # Check for duplicate content
        line_key = line.strip()[:50]  # First 50 chars as key
        if line_key not in seen_content:
            seen_content.add(line_key)
            cleaned_lines.append(line)
    
    # Return only first 5-6 lines of insights to avoid duplication
    if len(cleaned_lines) > 8:
        cleaned_lines = cleaned_lines[:6]
    
    return '\n'.join(cleaned_lines)

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
            
            # Create pattern string with icons (limit to 10 items per line)
            pattern_parts = []
            for seq_num, outcome in sequences:
                if outcome == 'win':
                    pattern_parts.append(f"✅L{seq_num}")
                else:
                    pattern_parts.append(f"❌L{seq_num}")
            
            # Join with spaces instead of arrows for cleaner look
            pattern_str = " ".join(pattern_parts[:15])  # Limit to 15 items
            if len(pattern_parts) > 15:
                pattern_str += f" +{len(pattern_parts)-15} more"
            
            # Calculate day stats
            total_bets = len(day_bets)
            wins = len(day_bets[day_bets['outcome'] == 'win'])
            win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
            day_profit = day_bets['profit'].sum()
            
            profit_emoji = "🟢" if day_profit > 0 else "🔴" if day_profit < 0 else "⚪"
            profit_color = "+" if day_profit > 0 else ""
            
            day_name = day.strftime('%a')
            pattern_lines.append(f"*{day.strftime('%m/%d')} ({day_name})*")
            pattern_lines.append(f"└ {pattern_str}")
            pattern_lines.append(f"  {profit_emoji} {total_bets}b | {wins}w | {win_rate:.0f}% | ${profit_color}{day_profit:.0f}")
            pattern_lines.append("")
        else:
            day_name = day.strftime('%a')
            pattern_lines.append(f"*{day.strftime('%m/%d')} ({day_name})*")
            pattern_lines.append(f"└ ⚪ No bets")
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
    total_profit = bets_df[bets_df['date'].isin(last_7_days)]['profit'].sum()
    
    # Find patterns (limit length for readability)
    pattern_str = ''.join(['W' if p == 'win' else 'L' for p in all_patterns])
    if len(pattern_str) > 30:
        pattern_str = pattern_str[:27] + "..."
    
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
    summary_lines.append("📈 *7-DAY SUMMARY*")
    summary_lines.append("")
    summary_lines.append(f"📊 {total_bets}b | ✅ {wins}w | ❌ {total_bets-wins}l")
    summary_lines.append(f"🎯 {win_rate:.0f}% win | 💰 ${total_profit:.0f} profit")
    summary_lines.append(f"📈 Pattern: `{pattern_str}`")
    summary_lines.append("")
    summary_lines.append(f"🔥 Win streak: {max_win_streak} | 💀 Loss streak: {max_loss_streak}")
    summary_lines.append(f"⚠️ High chases (3+): {high_sequences}")
    
    # Risk assessment - simplified
    if max_loss_streak >= 5:
        summary_lines.append("")
        summary_lines.append("🔴 *CRITICAL*: 5+ consecutive losses!")
        summary_lines.append("→ Reset chase to level 1")
    elif max_loss_streak >= 3:
        summary_lines.append("")
        summary_lines.append("⚠️ *WARNING*: Multiple consecutive losses")
        summary_lines.append("→ Reduce to level 1 stake")
    elif win_rate >= 60:
        summary_lines.append("")
        summary_lines.append("🟢 *OPTIMAL*: Good win rate")
        summary_lines.append("→ Maintain current strategy")
    
    return "\n".join(summary_lines)

def send_daily_report(insights, bets_df, stats):
    """Send comprehensive daily report with sequence patterns"""
    
    # Clean the insights to remove duplicates
    clean_ai_insights = clean_insights(insights)
    
    # Header
    header = "🤖 *BETTING ANALYTICS* 🤖\n"
    header += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    header += "─" * 25 + "\n\n"
    
    # Bot status (compact)
    profit_emoji = "🟢" if stats.get('today_profit', 0) > 0 else "🔴" if stats.get('today_profit', 0) < 0 else "⚪"
    bot_status = f"📊 *Today*: {stats.get('today_bets', 0)} bets | P&L {profit_emoji} ${stats.get('today_profit', 0):.0f}\n"
    bot_status += f"⏳ Active bets: {stats.get('unresolved_count', 0)}\n\n"
    
    # AI Insights (cleaned)
    ai_section = "🧠 *AI Insights*\n"
    ai_section += f"{clean_ai_insights}\n\n"
    
    # Format sequence pattern for last 7 days
    sequence_pattern = format_sequence_pattern(bets_df)
    sequence_summary = format_sequence_summary(bets_df)
    
    # Combine all sections
    full_message = header + bot_status + ai_section + sequence_pattern
    
    if sequence_summary:
        full_message += "\n" + sequence_summary
    
    # Add closing (minimal)
    full_message += "\n\n─" * 25 + "\n"
    full_message += "💡 Dashboard: https://betting-analytics.up.railway.app"
    
    # Split message if too long (Telegram limit 4096 chars)
    if len(full_message) > 4000:
        # Send in parts
        part1 = header + bot_status + sequence_pattern[:2500]
        part2 = sequence_summary + "\n\n" + ai_section + "\n\n💡 Dashboard: https://betting-analysis-agent-production.up.railway.app"
        
        send_telegram_message(part1)
        send_telegram_message(part2)
        return True
    
    return send_telegram_message(full_message)