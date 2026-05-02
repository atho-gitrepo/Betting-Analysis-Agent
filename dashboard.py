import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from firebase_client import FirebaseReader
from config import FIREBASE_CREDENTIALS_JSON
import json
import warnings
warnings.filterwarnings('ignore')

# Try to import matplotlib, but handle gracefully if not available
try:
    import matplotlib.pyplot as plt
    from matplotlib import cm
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Betting Analytics Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .dashboard-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 30px;
    }
    .alert-success {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .alert-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    .alert-danger {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    .sequence-win { background-color: #90EE90; color: #000; padding: 4px 8px; border-radius: 4px; text-align: center; }
    .sequence-loss { background-color: #FFB6C1; color: #000; padding: 4px 8px; border-radius: 4px; text-align: center; }
    .sequence-active { background-color: #FFD700; color: #000; padding: 4px 8px; border-radius: 4px; text-align: center; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

class BettingDashboard:
    def __init__(self):
        self.fb = FirebaseReader(FIREBASE_CREDENTIALS_JSON)
        self.df = None
        self.load_data()
    
    @st.cache_data(ttl=300)
    def load_data(_self):
        with st.spinner("🔄 Loading betting data from Firebase..."):
            bets = _self.fb.get_recent_resolved_bets(days_back=90, limit=1000)
            
            if not bets:
                st.warning("No betting data found. Run analytics_service.py first.")
                return pd.DataFrame()
            
            df = pd.DataFrame(bets)
            
            # Data processing
            df['resolved_at'] = pd.to_datetime(df['resolved_at'])
            df['date'] = df['resolved_at'].dt.date
            df['hour'] = df['resolved_at'].dt.hour
            df['day_of_week'] = df['resolved_at'].dt.day_name()
            df['week'] = df['resolved_at'].dt.isocalendar().week
            df['month'] = df['resolved_at'].dt.month
            df['profit'] = df.apply(
                lambda x: x['stake'] if x['outcome'] == 'win' else -x['stake'], 
                axis=1
            )
            df['cumulative_profit'] = df['profit'].cumsum()
            df['roi'] = (df['profit'] / df['stake'] * 100).round(2)
            
            return df
    
    def render_sidebar(self):
        with st.sidebar:
            st.image("https://img.icons8.com/color/96/000000/football2.png", width=80)
            st.title("🎯 Filters")
            st.markdown("---")
            
            if not self.df.empty:
                min_date = self.df['date'].min()
                max_date = self.df['date'].max()
                
                date_range = st.date_input(
                    "Date Range",
                    value=[min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    self.df = self.df[(self.df['date'] >= start_date) & (self.df['date'] <= end_date)]
                
                leagues = ['All'] + sorted(self.df['league'].unique().tolist())
                selected_league = st.selectbox("League", leagues)
                if selected_league != 'All':
                    self.df = self.df[self.df['league'] == selected_league]
                
                outcomes = ['All', 'win', 'loss']
                selected_outcome = st.selectbox("Outcome", outcomes)
                if selected_outcome != 'All':
                    self.df = self.df[self.df['outcome'] == selected_outcome]
                
                min_sequence = st.slider("Minimum Chase Sequence", 1, 4, 1)
                self.df = self.df[self.df['match_sequence'] >= min_sequence]
                
                st.markdown("---")
                
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
                
                st.markdown("---")
                st.markdown("### 📊 Current View")
                st.metric("Total Bets", len(self.df))
                st.metric("Total Profit", f"${self.df['profit'].sum():.2f}")
    
    def render_header_metrics(self):
        st.markdown('<div class="dashboard-header">', unsafe_allow_html=True)
        st.title("🎯 Betting Analytics Pro Dashboard")
        st.markdown("Real-time betting intelligence and performance tracking")
        st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_bets = len(self.df)
        wins = len(self.df[self.df['outcome'] == 'win'])
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        total_profit = self.df['profit'].sum()
        avg_roi = self.df['roi'].mean() if not self.df.empty else 0
        
        with col1:
            st.metric("Total Bets", total_bets)
        with col2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            st.metric("Total P&L", f"${total_profit:.2f}")
        with col4:
            st.metric("Average ROI", f"{avg_roi:.1f}%")
        with col5:
            avg_stake = self.df['stake'].mean() if not self.df.empty else 0
            st.metric("Average Stake", f"${avg_stake:.2f}")
    
    def render_profit_trends(self):
        st.subheader("📈 Profit & Loss Trends")
        
        tab1, tab2, tab3 = st.tabs(["Cumulative Profit", "Daily Performance", "Moving Average"])
        
        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=self.df['resolved_at'],
                y=self.df['cumulative_profit'],
                mode='lines+markers',
                name='Cumulative Profit',
                line=dict(color='#00ff00', width=3),
                marker=dict(size=6, color=self.df['profit'], colorscale='RdYlGn')
            ))
            fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
            fig.update_layout(
                title="Cumulative Profit Over Time",
                xaxis_title="Date",
                yaxis_title="Profit ($)",
                height=500,
                hovermode='x unified',
                template='plotly_dark'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            daily_profit = self.df.groupby('date')['profit'].agg(['sum', 'count']).reset_index()
            daily_profit.columns = ['date', 'profit', 'bets']
            colors = ['red' if x < 0 else 'green' for x in daily_profit['profit']]
            
            fig = go.Figure(data=[
                go.Bar(x=daily_profit['date'], y=daily_profit['profit'], 
                       marker_color=colors, text=daily_profit['profit'].round(2),
                       textposition='auto', name='Daily Profit')
            ])
            fig.add_trace(go.Scatter(
                x=daily_profit['date'], y=daily_profit['bets'] * 10,
                name='Number of Bets', yaxis='y2',
                mode='lines+markers', line=dict(color='orange', width=2)
            ))
            fig.update_layout(
                title="Daily Profit/Loss with Bet Volume",
                xaxis_title="Date", yaxis_title="Profit ($)",
                yaxis2=dict(title="Number of Bets", overlaying='y', side='right'),
                height=500, template='plotly_dark'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            df_ma = self.df.copy()
            df_ma['MA5'] = df_ma['profit'].rolling(window=5, min_periods=1).mean()
            df_ma['MA10'] = df_ma['profit'].rolling(window=10, min_periods=1).mean()
            df_ma['MA20'] = df_ma['profit'].rolling(window=20, min_periods=1).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_ma['resolved_at'], y=df_ma['profit'], 
                                     mode='markers', name='Individual Bets',
                                     marker=dict(size=8, color=df_ma['profit'], colorscale='RdYlGn')))
            fig.add_trace(go.Scatter(x=df_ma['resolved_at'], y=df_ma['MA5'], 
                                     mode='lines', name='MA 5', line=dict(color='cyan', width=2)))
            fig.add_trace(go.Scatter(x=df_ma['resolved_at'], y=df_ma['MA10'], 
                                     mode='lines', name='MA 10', line=dict(color='yellow', width=2)))
            fig.add_trace(go.Scatter(x=df_ma['resolved_at'], y=df_ma['MA20'], 
                                     mode='lines', name='MA 20', line=dict(color='magenta', width=2)))
            fig.update_layout(title="Moving Averages (Trend Analysis)",
                            xaxis_title="Date", yaxis_title="Profit per Bet ($)",
                            height=500, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
    
    def render_league_analysis(self):
        st.subheader("🏆 League Performance")
        
        league_stats = self.df.groupby('league').agg({
            'outcome': lambda x: (x == 'win').sum(),
            'stake': ['sum', 'count', 'mean'],
            'profit': 'sum',
            'roi': 'mean'
        }).round(2)
        
        league_stats.columns = ['wins', 'total_stake', 'bets', 'avg_stake', 'total_profit', 'avg_roi']
        league_stats['losses'] = league_stats['bets'] - league_stats['wins']
        league_stats['win_rate'] = (league_stats['wins'] / league_stats['bets'] * 100).round(1)
        
        # Treemap
        fig = px.treemap(
            league_stats.reset_index(),
            path=['league'],
            values='bets',
            color='win_rate',
            color_continuous_scale='RdYlGn',
            title="League Performance Treemap",
            hover_data={'win_rate': ':.1f', 'total_profit': ':$.2f'}
        )
        fig.update_layout(height=500, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
        
        # League table
        col1, col2 = st.columns([2, 1])
        
        with col1:
            display_df = league_stats[['bets', 'wins', 'losses', 'win_rate', 'total_profit', 'avg_roi']].copy()
            display_df.columns = ['Bets', 'Wins', 'Losses', 'Win Rate %', 'Total Profit', 'Avg ROI %']
            
            formatted_df = display_df.style.format({
                'Win Rate %': '{:.1f}',
                'Total Profit': '${:.2f}',
                'Avg ROI %': '{:.1f}'
            })
            
            st.dataframe(formatted_df, use_container_width=True, height=400)
        
        with col2:
            top_leagues = league_stats.nlargest(5, 'total_profit')[['total_profit', 'win_rate']]
            if not top_leagues.empty:
                fig = px.bar(top_leagues, x='total_profit', y=top_leagues.index,
                            orientation='h', title="Top 5 Leagues by Profit",
                            color='win_rate', color_continuous_scale='RdYlGn')
                fig.update_layout(height=400, template='plotly_dark')
                st.plotly_chart(fig, use_container_width=True)
    
    def render_chase_analysis(self):
        st.subheader("🔄 Chase Sequence Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sequence_stats = self.df.groupby('match_sequence').agg({
                'outcome': lambda x: (x == 'win').sum(),
                'stake': ['count', 'mean'],
                'profit': 'sum',
                'roi': 'mean'
            }).round(2)
            
            sequence_stats.columns = ['wins', 'bets', 'avg_stake', 'total_profit', 'avg_roi']
            sequence_stats['losses'] = sequence_stats['bets'] - sequence_stats['wins']
            sequence_stats['win_rate'] = (sequence_stats['wins'] / sequence_stats['bets'] * 100).round(1)
            
            fig = make_subplots(rows=2, cols=1,
                               subplot_titles=('Win Rate by Sequence', 'Profit by Sequence'),
                               vertical_spacing=0.15)
            
            fig.add_trace(go.Bar(x=sequence_stats.index, y=sequence_stats['win_rate'],
                               name='Win Rate', marker_color='lightblue'), row=1, col=1)
            fig.add_trace(go.Bar(x=sequence_stats.index, y=sequence_stats['total_profit'],
                               name='Profit', marker_color=['green' if x > 0 else 'red' for x in sequence_stats['total_profit']]),
                               row=2, col=1)
            
            fig.update_layout(height=500, showlegend=False, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            risk_matrix = pd.crosstab(self.df['match_sequence'], self.df['outcome'], normalize='index') * 100
            fig = px.imshow(risk_matrix, text_auto=True,
                           title="Risk Heatmap: Win/Loss % by Sequence",
                           labels=dict(x="Outcome", y="Sequence Level", color="Percentage"),
                           color_continuous_scale='RdYlGn')
            fig.update_layout(height=500, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
    
    def render_sequence_win_loss_table(self):
        """Display sequence win/loss table for last 7 days"""
        st.subheader("📅 Last 7 Days - Sequence Win/Loss Tracker")
        
        # Get last 7 days
        today = datetime.now().date()
        last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        
        # Create sequences for each day
        sequence_data = []
        for day in last_7_days:
            day_bets = self.df[self.df['date'] == day]
            
            if not day_bets.empty:
                # Get sequences in order
                sequences = day_bets.sort_values('resolved_at')[['match_sequence', 'outcome']].values.tolist()
                
                # Calculate day stats
                total_bets = len(day_bets)
                wins = len(day_bets[day_bets['outcome'] == 'win'])
                win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
                day_profit = day_bets['profit'].sum()
                
                sequence_data.append({
                    'date': day,
                    'day_name': day.strftime('%A'),
                    'total_bets': total_bets,
                    'wins': wins,
                    'losses': total_bets - wins,
                    'win_rate': win_rate,
                    'profit': day_profit,
                    'sequences': sequences,
                    'max_sequence': max([s[0] for s in sequences]) if sequences else 0
                })
            else:
                sequence_data.append({
                    'date': day,
                    'day_name': day.strftime('%A'),
                    'total_bets': 0,
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0,
                    'profit': 0,
                    'sequences': [],
                    'max_sequence': 0
                })
        
        # Display as a table with sequence visualization
        for day_data in sequence_data:
            with st.expander(f"📅 {day_data['date'].strftime('%Y-%m-%d')} - {day_data['day_name']}", expanded=(day_data['date'] == today)):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Bets", day_data['total_bets'])
                with col2:
                    st.metric("Wins/Losses", f"{day_data['wins']}/{day_data['losses']}")
                with col3:
                    delta_color = "normal" if day_data['win_rate'] >= 50 else "inverse"
                    st.metric("Win Rate", f"{day_data['win_rate']:.1f}%", delta_color=delta_color)
                with col4:
                    st.metric("Profit", f"${day_data['profit']:.2f}", 
                             delta_color="normal" if day_data['profit'] > 0 else "inverse")
                
                # Display sequence timeline
                if day_data['sequences']:
                    st.markdown("**Sequence Timeline:**")
                    
                    # Create sequence visualization
                    cols = st.columns(min(len(day_data['sequences']), 10))
                    for idx, (seq_num, outcome) in enumerate(day_data['sequences']):
                        if idx < len(cols):
                            with cols[idx]:
                                if outcome == 'win':
                                    st.markdown(f'<div class="sequence-win">🏆 L{seq_num}<br>WIN</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="sequence-loss">❌ L{seq_num}<br>LOSS</div>', unsafe_allow_html=True)
                    
                    # Show sequence pattern
                    pattern = ''.join(['W' if o == 'win' else 'L' for _, o in day_data['sequences']])
                    max_seq = day_data['max_sequence']
                    st.caption(f"Pattern: {pattern} | Max Chase Level: {max_seq}")
                    
                    if max_seq >= 3 and day_data['profit'] < 0:
                        st.warning(f"⚠️ High chase level ({max_seq}) with negative profit")
                else:
                    st.info("No bets placed on this day")
                
                st.markdown("---")
        
        # Summary statistics for last 7 days
        st.subheader("📊 7-Day Performance Summary")
        
        total_7day_bets = sum(d['total_bets'] for d in sequence_data)
        total_7day_wins = sum(d['wins'] for d in sequence_data)
        total_7day_profit = sum(d['profit'] for d in sequence_data)
        avg_win_rate = (total_7day_wins / total_7day_bets * 100) if total_7day_bets > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bets (7 days)", total_7day_bets)
        with col2:
            st.metric("Total Wins", total_7day_wins)
        with col3:
            st.metric("Avg Win Rate", f"{avg_win_rate:.1f}%")
        with col4:
            st.metric("Total Profit (7 days)", f"${total_7day_profit:.2f}",
                     delta_color="normal" if total_7day_profit > 0 else "inverse")
        
        # Weekly trend chart
        weekly_df = pd.DataFrame([{
            'date': d['date'],
            'profit': d['profit'],
            'win_rate': d['win_rate'],
            'bets': d['total_bets']
        } for d in sequence_data])
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(go.Bar(x=weekly_df['date'], y=weekly_df['profit'],
                            name='Daily Profit', marker_color=['green' if x > 0 else 'red' for x in weekly_df['profit']]),
                     secondary_y=False)
        
        fig.add_trace(go.Scatter(x=weekly_df['date'], y=weekly_df['win_rate'],
                                name='Win Rate %', mode='lines+markers',
                                line=dict(color='cyan', width=3)),
                     secondary_y=True)
        
        fig.update_layout(title="Last 7 Days: Profit vs Win Rate",
                         xaxis_title="Date", height=400, template='plotly_dark')
        fig.update_yaxes(title_text="Profit ($)", secondary_y=False)
        fig.update_yaxes(title_text="Win Rate (%)", secondary_y=True, range=[0, 100])
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Risk warning for recent patterns
        recent_sequences = []
        for day_data in sequence_data[-3:]:  # Last 3 days
            recent_sequences.extend([s[0] for s in day_data['sequences']])
        
        high_sequences_last_3days = [s for s in recent_sequences if s >= 3]
        if high_sequences_last_3days:
            st.warning(f"⚠️ Alert: {len(high_sequences_last_3days)} high-sequence (3+) bets in last 3 days. Monitor chase levels!")
        
        losing_days = len([d for d in sequence_data if d['profit'] < 0])
        if losing_days >= 4:
            st.error(f"🔴 CRITICAL: {losing_days} losing days in the last week! Consider pausing or reducing stakes.")
        elif losing_days >= 2:
            st.warning(f"⚠️ CAUTION: {losing_days} losing days in the last week. Review strategy.")
        else:
            st.success(f"✅ Only {losing_days} losing days in the last week. Strategy is working well!")
    
    def render_risk_metrics(self):
        st.subheader("⚠️ Risk Assessment & Alerts")
        
        total_bets = len(self.df)
        if total_bets > 0:
            # Calculate losing streaks
            losing_streaks = []
            current_streak = 0
            for outcome in self.df['outcome']:
                if outcome == 'loss':
                    current_streak += 1
                else:
                    if current_streak > 0:
                        losing_streaks.append(current_streak)
                    current_streak = 0
            if current_streak > 0:
                losing_streaks.append(current_streak)
            
            max_losing_streak = max(losing_streaks) if losing_streaks else 0
            avg_losing_streak = np.mean(losing_streaks) if losing_streaks else 0
            
            # Calculate winning streaks
            winning_streaks = []
            current_streak = 0
            for outcome in self.df['outcome']:
                if outcome == 'win':
                    current_streak += 1
                else:
                    if current_streak > 0:
                        winning_streaks.append(current_streak)
                    current_streak = 0
            if current_streak > 0:
                winning_streaks.append(current_streak)
            
            max_winning_streak = max(winning_streaks) if winning_streaks else 0
            profit_std = self.df['profit'].std()
            sharpe_ratio = self.df['profit'].mean() / profit_std if profit_std > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Max Losing Streak", f"{max_losing_streak} bets")
                st.metric("Avg Losing Streak", f"{avg_losing_streak:.1f} bets")
            with col2:
                st.metric("Max Winning Streak", f"{max_winning_streak} bets")
                st.metric("Profit Volatility", f"${profit_std:.2f}")
            with col3:
                st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                risk_level = "🔴 High" if sharpe_ratio < 0.5 else "🟡 Medium" if sharpe_ratio < 1 else "🟢 Low"
                st.metric("Risk Level", risk_level)
            with col4:
                recommended_chase = min(4, max(3, max_losing_streak + 1)) if max_losing_streak > 0 else 4
                st.metric("Recommended Max Chase", f"Level {recommended_chase}")
                bankroll_pct = min(25, max(5, int(sharpe_ratio * 10))) if sharpe_ratio > 0 else 5
                st.metric("Recommended Stake", f"{bankroll_pct}% of bankroll")
            
            # AI Recommendations
            st.markdown("---")
            st.subheader("🤖 AI Recommendations")
            
            today_profit = self.df[self.df['date'] == datetime.now().date()]['profit'].sum() if not self.df[self.df['date'] == datetime.now().date()].empty else 0
            
            if today_profit < -50:
                st.error(f"🔴 STOP LOSS: Daily loss of ${today_profit:.2f} exceeds $50 limit. Stop betting!")
            elif today_profit < 0:
                st.warning(f"⚠️ CAUTION: Currently down ${today_profit:.2f} today. Consider reducing stakes.")
            elif today_profit > 100:
                st.success(f"🎯 PROFIT TARGET: Daily profit target reached: +${today_profit:.2f}. Good time to stop!")
            else:
                st.info(f"📊 Today's P&L: ${today_profit:.2f}")
            
            if max_losing_streak >= 5:
                st.error(f"🚨 CRITICAL: {max_losing_streak} consecutive losses! Reset chase sequence immediately.")
            elif max_losing_streak >= 3:
                st.warning(f"⚠️ WARNING: {max_losing_streak} consecutive losses. Consider reducing stake.")
            else:
                st.success("✅ Current strategy is performing well. Continue monitoring.")
    
    def render_detailed_table(self):
        st.subheader("📋 Detailed Bet Log")
        
        col1, col2 = st.columns(2)
        with col1:
            search = st.text_input("🔍 Search matches", placeholder="Team name...")
        with col2:
            sort_by = st.selectbox("Sort by", ['resolved_at', 'profit', 'stake', 'match_sequence'])
        
        display_df = self.df.copy()
        if search:
            display_df = display_df[display_df['match_name'].str.contains(search, case=False)]
        
        display_df = display_df.sort_values(sort_by, ascending=False)
        
        display_cols = ['resolved_at', 'match_name', 'league', 'stake', 'outcome', 'profit', 'roi', 'match_sequence']
        display_df = display_df[display_cols].head(100)
        display_df.columns = ['Date', 'Match', 'League', 'Stake', 'Outcome', 'Profit', 'ROI %', 'Sequence']
        
        # Color code rows
        def color_outcome(val):
            if val == 'win':
                return 'background-color: #90EE90'
            elif val == 'loss':
                return 'background-color: #FFB6C1'
            return ''
        
        styled_df = display_df.style.applymap(color_outcome, subset=['Outcome'])
        styled_df = styled_df.format({
            'Stake': '${:.2f}',
            'Profit': '${:.2f}',
            'ROI %': '{:.1f}%'
        })
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        csv = display_df.to_csv(index=False)
        st.download_button(label="📥 Download Data as CSV", data=csv,
                          file_name=f"betting_data_{datetime.now().strftime('%Y%m%d')}.csv",
                          mime="text/csv")
    
    def run(self):
        self.df = self.load_data()
        
        if self.df.empty:
            st.warning("No data available. Please ensure:")
            st.markdown("""
            1. Firebase credentials are correct in .env
            2. Bot has placed some bets
            3. Run `python analytics_service.py` to sync data
            """)
            return
        
        self.render_sidebar()
        self.render_header_metrics()
        self.render_profit_trends()
        
        col1, col2 = st.columns(2)
        with col1:
            self.render_league_analysis()
        with col2:
            self.render_chase_analysis()
        
        # Replace temporal patterns with sequence win/loss table
        self.render_sequence_win_loss_table()
        
        self.render_risk_metrics()
        self.render_detailed_table()

if __name__ == "__main__":
    import os
    dashboard = BettingDashboard()
    dashboard.run()