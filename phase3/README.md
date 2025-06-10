# Reddit Pain Finder - Phase 3: Interactive Dashboard

Phase 3 adds a complete interactive dashboard with Next.js frontend, FastAPI backend microservice, saved searches, and alert system.

## 🚀 Features

### ✅ Interactive Dashboard
- **Topic search bar** with real-time analysis
- **Results table** with clickable clusters for detailed views
- **Heat-map visualization** of desperation vs engagement
- **Drill-down modals** showing raw posts, comments, and MVP suggestions

### ✅ Saved Searches & Alerts
- **User authentication** with simple TinyAuth system
- **Save searches** for repeated analysis
- **Alert subscriptions** via email and Slack
- **Weekly/daily digest** of high-priority pain points

### ✅ CSV/API Export
- **Download results** as CSV for external analysis
- **REST API** for programmatic access
- **Background processing** for large analyses

## 🏗 Architecture

```
phase3/
├── backend/           # FastAPI microservice
│   ├── main.py       # API endpoints & database
│   ├── alert_system.py # Email/Slack alerts
│   └── requirements.txt
├── frontend/          # Next.js dashboard
│   ├── app/
│   │   ├── page.tsx  # Main dashboard
│   │   └── searches/ # Saved searches page
│   └── package.json
└── database/          # SQLite storage
    └── painpoints.db
```

## 🔧 Setup Instructions

### 1. Backend Setup

```bash
cd phase3/backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your API keys

# Start FastAPI server
python main.py
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd phase3/frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Database Setup

The SQLite database is automatically created when you first run the backend. It includes tables for:
- Analysis results (cached for 7 days)
- Saved searches
- User accounts
- Alert subscriptions

## 📧 Alert System Setup

### Email Alerts

1. **Gmail Setup** (recommended):
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_gmail@gmail.com
   SMTP_PASSWORD=your_app_password  # Generate in Gmail settings
   ```

2. **Other Providers**:
   - Outlook: `smtp-mail.outlook.com:587`
   - Yahoo: `smtp.mail.yahoo.com:587`

### Slack Alerts

1. Create a Slack webhook:
   - Go to your Slack workspace settings
   - Apps → Incoming Webhooks → Add to Slack
   - Copy the webhook URL

2. Add webhook URL when creating alert subscription

### Cron Job Setup

For automated alerts, set up a cron job:

```bash
# Run daily at 8 AM
0 8 * * * cd /path/to/phase3/backend && python alert_system.py

# Run weekly on Monday at 8 AM
0 8 * * 1 cd /path/to/phase3/backend && python alert_system.py
```

## 📊 API Endpoints

### Analysis
- `POST /analyze` - Start new analysis
- `GET /analyze/{topic_hash}` - Get analysis status/results

### Export
- `GET /topics/{topic_id}/export.csv` - Download CSV

### User Management
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login

### Saved Searches
- `POST /searches` - Save a search
- `GET /searches/{user_id}` - Get user's searches

### Alerts
- `POST /alerts` - Create alert subscription
- `GET /alerts/{user_id}` - Get user's alerts

## 🎯 Usage Guide

### 1. Basic Search
1. Enter a topic (e.g., "indie game developers")
2. Click "Analyze" 
3. View results in interactive table
4. Click clusters for detailed information

### 2. Save & Alert Setup
1. Sign up/login with email
2. Search for a topic
3. Click "Save" to save the search
4. Go to "Saved Searches" page
5. Click bell icon to set up alerts

### 3. Export Data
1. After running analysis
2. Click "Export CSV" in heat map section
3. Use data in Excel, Google Sheets, or other tools

## 🔥 Alert Email Example

```html
🔥 Pain Point Alert: indie game developers (3 high-priority)

📊 High-Priority Clusters Found: 3
⚡ Total Engagement Weight: 245.67
📈 Trending Clusters: 1 🆙

🚨 High-Priority Pain Points:

1. 🎯 Marketing and Visibility Issues 🆙
   🔥 Desperation: 8/10 | ⚡ Engagement: 87.23
   💡 MVP: Social media automation tool for indie devs
   📎 https://reddit.com/r/gamedev/post123

💡 Next Steps:
- Review trending clusters for immediate opportunities
- Validate high-desperation problems with customers
- Build MVPs for trending problems first
```

## 🚦 Status

**Phase 3 Complete!** ✅

### What's Working:
- ✅ Interactive dashboard with search & visualization
- ✅ User authentication and saved searches
- ✅ Alert system with email/Slack notifications
- ✅ CSV export functionality
- ✅ Background analysis processing
- ✅ Database persistence

### Next Steps (Phase 4):
- Twitter/X integration for real-time pain points
- Product Hunt & Indie Hackers data sources
- App Store review analysis
- Stack Overflow integration

## 🐛 Troubleshooting

### Backend Issues
- **Port 8000 in use**: Change PORT in `.env`
- **Database errors**: Delete `database/painpoints.db` and restart
- **Email not sending**: Check SMTP credentials and app passwords

### Frontend Issues
- **Port 3000 in use**: Next.js will auto-suggest port 3001
- **API connection failed**: Ensure backend is running on port 8000
- **Build errors**: Run `npm install` to update dependencies

### Alert Issues
- **No emails received**: Check spam folder and SMTP settings
- **Slack not working**: Verify webhook URL is correct
- **Cron not running**: Check file paths and permissions

## 📈 Performance Notes

- **Analysis caching**: Results cached for 7 days
- **Background processing**: Large analyses run asynchronously
- **Database**: SQLite suitable for MVP, consider PostgreSQL for production
- **Rate limiting**: Reddit API has rate limits, analysis may take 2-5 minutes

## 🔒 Security Considerations

- **TinyAuth**: Basic auth for MVP, implement proper JWT for production
- **Environment variables**: Never commit API keys to version control
- **HTTPS**: Use HTTPS in production for secure authentication
- **Database**: Consider encryption for sensitive user data 