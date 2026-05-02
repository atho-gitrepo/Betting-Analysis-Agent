# 🎯 Betting Analytics Pro

An intelligent betting analytics system that automatically syncs your Telegram betting bot data, provides AI-powered insights, and visualizes performance through an interactive dashboard.

## 🚀 Core Features

### Automated Data Pipeline
- **Read-only Firebase Integration** - Securely connects to your bot's Firestore database without any modifications to existing bot code
- **Real-time Bet Syncing** - Automatically fetches resolved bets and pushes them to Notion database
- **Local LLM Processing** - Uses T5-small transformer model for on-device betting pattern analysis (no external API calls)
- **Telegram Reporting** - Scheduled daily reports with win rates, profit/loss, and risk recommendations

### 📊 Interactive Dashboard
Built with Streamlit, featuring:

#### Performance Analytics
- **Cumulative Profit Tracking** - Real-time visualization of profit/loss over time
- **Daily Performance** - Bar charts showing daily P&L with bet volume overlay
- **Moving Averages** - 5, 10, and 20-period trend analysis
- **Win Rate Metrics** - Overall performance statistics and league-specific breakdowns

#### League Intelligence
- **League Performance Treemap** - Visual hierarchy of league profitability
- **Top/Bottom League Rankings** - Identify most and least profitable competitions
- **ROI Analysis** - Return on investment per league with betting volume insights
- **League Filtering** - Drill down into specific league performance

#### Chase Sequence Analysis
- **Sequence Win Rate** - Performance breakdown by chase level (1-4)
- **Profit by Sequence** - Financial results per sequence level
- **Risk Heatmap** - Win/loss percentage matrix by sequence level
- **Pattern Recognition** - Identify dangerous chase patterns

#### Last 7 Days Sequence Tracker
- **Daily Timeline View** - Expandable day-by-day sequence visualization
- **Sequence Blocks** - Color-coded win/loss indicators with level numbers
- **Pattern Display** - W/L sequence pattern string (e.g., "WWLWL")
- **7-Day Summary** - Aggregated metrics including total profit, win rate, and bet count
- **Weekly Trend Chart** - Dual-axis visualization of daily profit vs win rate

#### Risk Management
- **Streak Analysis** - Track maximum winning and losing streaks
- **Sharpe Ratio Calculation** - Risk-adjusted return metric
- **Volatility Monitoring** - Profit standard deviation tracking
- **Dynamic Recommendations** - AI-powered stake and chase level suggestions
- **Stop Loss Alerts** - Daily loss threshold warnings

#### Data Export
- **CSV Download** - Export filtered betting data
- **Search Functionality** - Find specific matches by name
- **Sortable Tables** - Organize by date, profit, stake, or sequence
- **Custom Date Ranges** - Filter analysis to specific time periods

### 🤖 AI Intelligence Features

#### Local LLM Processing (T5-small)
- **Pattern Detection** - Identifies betting patterns from historical data
- **Risk Assessment** - Calculates optimal chase levels based on losing streaks
- **Performance Prediction** - Win rate forecasting based on historical trends
- **Privacy First** - All processing done locally, no data sent to external APIs

#### Automated Insights
- **Daily Summary** - Automatic win rate and profit calculations
- **League Recommendations** - Identifies leagues to add/avoid
- **Stake Optimization** - Kelly Criterion-based stake suggestions
- **Sequence Alerts** - Warnings when high chase levels are triggered

### 📱 Notification System

#### Telegram Integration
- **Daily Reports** - Scheduled morning and evening performance summaries
- **Real-time Alerts** - Stop loss notifications and profit target achievements
- **Risk Warnings** - Consecutive loss alerts and sequence level warnings
- **Actionable Insights** - Clear recommendations for stake adjustment

### 🔄 Notion Integration

#### Automated Database Sync
- **Match Tracking** - Automatically creates Notion pages for each bet
- **Property Mapping** - 10+ custom properties including Match, League, Score 36', HT Score, Stake, Outcome, Sequence, Date, Match ID, and Profit
- **Duplicate Prevention** - Checks existing entries before syncing
- **Dynamic League Options** - Automatically adds new leagues to Notion select property

## 📈 Analytics Capabilities

### Performance Metrics
- **Win Rate** - Percentage of winning bets (overall and by league)
- **Net Profit/Loss** - Total financial performance
- **Average ROI** - Return on investment percentage
- **Average Stake** - Mean bet size across all wagers

### League Analysis
- **Individual League Performance** - Win rate, profit, ROI by competition
- **Volume Analysis** - Number of bets per league
- **Profit Ranking** - Best and worst performing leagues
- **Risk Assessment** - Volatility and consistency metrics per league

### Temporal Patterns (Available in data)
- **Hourly Performance** - Win rates by time of day (data accessible)
- **Day of Week Trends** - Best/worst days for betting
- **Monthly Patterns** - Seasonal performance variations

### Risk Metrics
- **Sharpe Ratio** - Risk-adjusted return calculation
- **Maximum Drawdown** - Largest peak-to-trough decline
- **Consecutive Loss Tracking** - Longest losing streak monitoring
- **Session Analysis** - Daily performance metrics
- **Volatility Index** - Standard deviation of profits

### Sequence Intelligence
- **Level Performance** - Win rates for chase levels 1-4
- **Risk Progression** - How risk increases with sequence level
- **Recovery Analysis** - Success rates after losses
- **Pattern Detection** - Recurring win/loss sequences

## 🔧 Technical Architecture

### Service Components
1. **Analytics Service** - Scheduled data processing and sync (runs every 6 hours)
2. **Streamlit Dashboard** - Real-time web interface (always-on)
3. **Process Manager** - Monitors and auto-restarts services
4. **Local LLM** - T5-small transformer for on-device intelligence

### Data Flow

Telegram Bot → Firebase → Analytics Service → Notion Database
↓
Local LLM Processing
↓
Telegram Reports & Dashboard

```

### Supported Data Sources
- **Firebase Firestore** - Primary data source (read-only access)
- **Notion API** - Destination for bet logs and analytics
- **Telegram API** - Report delivery channel

## 🎯 Key Differentiators

### No Bot Modifications Required
- Completely separate system from your existing betting bot
- Read-only Firebase access preserves bot integrity
- Zero risk of disrupting active betting operations

### Privacy-First AI
- Local LLM processing (no OpenAI API costs or data sharing)
- All analysis performed on your infrastructure
- Complete data ownership

### Production-Ready
- Automatic service monitoring and restart
- Health check endpoints for Railway deployment
- Comprehensive error logging and recovery
- Graceful handling of API rate limits

### Multi-Platform Integration
- Sync to Notion for manual analysis
- View in Streamlit dashboard for real-time monitoring
- Receive Telegram alerts for immediate action
- Export CSV for spreadsheet analysis

## 📊 Dashboard Sections

### 1. Header Metrics
- Total bets, win rate, total P&L, average ROI, average stake

### 2. Profit Trends
- Cumulative profit chart
- Daily P&L with volume overlay
- Moving average analysis

### 3. League Performance
- Interactive treemap visualization
- League ranking table
- Top 5 leagues by profit

### 4. Chase Sequence Analysis
- Win rate by sequence level
- Profit by sequence level
- Risk heatmap matrix

### 5. Last 7 Days Sequence Tracker
- Daily expandable panels
- Sequence block visualization
- Daily metrics (bets, wins, profit)
- Pattern string display
- Weekly trend chart

### 6. Risk Assessment
- Streak tracking (winning/losing)
- Sharpe ratio and volatility
- Recommended max chase level
- Optimal stake percentage
- AI-powered recommendations

### 7. Detailed Bet Log
- Searchable, sortable bet history
- Color-coded outcomes
- CSV export functionality

## 🔒 Security & Privacy

- **Read-Only Firebase Access** - Cannot modify your bot's data
- **Local LLM Processing** - No external API calls for AI insights
- **Environment Variables** - All credentials stored securely
- **No Data Storage** - Your data remains in Firebase and Notion

## 🎨 Visual Features

- **Dark Theme** - Eye-friendly interface for extended use
- **Responsive Layout** - Works on desktop and tablet
- **Interactive Charts** - Hover for details, zoom for focus
- **Color-Coded Metrics** - Green for profit/wins, red for losses
- **Progress Indicators** - Visual representation of sequences

## 📈 Example Insights Generated

- "Win rate 58.3% with net profit $245.50 over 120 bets"
- "League X shows 72% win rate - consider increasing stake"
- "3 consecutive losses at sequence level 3 - reduce to level 1 stake"
- "Best betting hours: 14:00-16:00 with 68% win rate"
- "Max losing streak of 4 - consider lowering MAX_CHASE_LEVEL to 3"

## 🚦 Alert Conditions

The system automatically detects and alerts on:
- Daily loss exceeding $50 threshold
- 3+ consecutive losses (warning)
- 5+ consecutive losses (critical)
- High-sequence (level 3+) chase losses
- Negative ROI leagues
- Profit target achievement ($100+ daily)
- Losing days trend (4+ losing days in 7 days)

## 🔄 Data Refresh

- **Dashboard** - Manual refresh button or auto-refresh every 5 minutes
- **Analytics Service** - Runs every 6 hours automatically
- **Notion Sync** - Triggers with each analytics run
- **Telegram Reports** - Twice daily (9 AM and 6 PM)

## 📦 Deployment

- **Single Container** - Both analytics and dashboard run in one container
- **Railway Ready** - Pre-configured for Railway deployment with healthchecks
- **Docker Support** - Multi-stage Dockerfile for optimized builds
- **Environment Variable** - Full configuration via .env file

## 🛠️ Technology Stack

- **Python 3.10** - Core runtime
- **Streamlit** - Dashboard framework
- **Plotly** - Interactive visualizations
- **Pandas** - Data manipulation
- **Transformers** - Local LLM (T5-small)
- **Firebase Admin** - Firestore client
- **Notion Client** - API integration
- **Docker** - Containerization
- **Railway** - Deployment platform

## 📊 Performance Characteristics

- **Startup Time** - ~10 seconds (includes model loading)
- **Memory Usage** - ~400MB (with T5-small model)
- **Analytics Runtime** - ~30 seconds for 1000 bets
- **Dashboard Response** - <2 seconds for filtered queries
- **Model Size** - 60MB (T5-small cached)

## 🌟 Unique Value Proposition

Unlike cloud-based betting trackers:
- **No subscription fees** - Self-hosted on free Railway tier
- **No data sharing** - All processing local to your instance
- **Full customization** - Modify any visualization or metric
- **Direct database access** - Your data never leaves your control
- **No API limits** - Local LLM means unlimited AI analysis