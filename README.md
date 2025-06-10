# Reddit Pain Point Finder

A LangGraph-based multi-agent system that identifies pain points from Reddit discussions to help founders find and validate startup ideas.

## 🎯 What It Does

Enter any topic (e.g., "college students", "indie game developers", "small business owners") and the tool will:

1. **Find Relevant Subreddits**: Uses AI to identify the 3 most active communities where people discuss problems
2. **Collect Real Data**: Fetches top posts from past year + hot posts from these subreddits
3. **Analyze Pain Points**: Uses AI to identify, summarize, and score problems (1-10 intensity)
4. **Cluster Similar Problems**: Groups related pain points using semantic similarity
5. **Score Desperation**: Measures emotional urgency and desperation levels (1-10)
6. **Generate Market Insights**: Provides market proxy data (subscribers, post frequency)
7. **Enhanced JSON Output**: Structured data for programmatic analysis

## 🚀 Features

### Phase 1: Enhanced Scraping & Scoring ✨

- **Smart Subreddit Discovery**: AI identifies the top 3 most active communities
- **Comprehensive Data Collection**: Yearly top + hot posts (up to 30 per subreddit)
- **Semantic Clustering**: Groups similar pain points using sentence transformers
- **Desperation Scoring**: AI measures emotional intensity and urgency (1-10)
- **Market Proxy Data**: Subscriber counts and posting frequency estimates
- **Frequency Analysis**: Identifies most commonly experienced problems
- **Enhanced JSON Output**: Structured data with clustering and market insights
- **GPT-4o Integration**: Uses latest OpenAI model for better analysis

### Core Features

- **Deep Content Analysis**: Analyzes posts + top 5 comments for context
- **Pain Point Scoring**: Rates problem intensity from 1-10
- **MVP Suggestions**: Provides concrete solution ideas
- **Rich Output**: Categorized results with source links and metrics

## 📋 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get API Keys

**OpenAI API Key:**
- Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
- Create a new API key
- Make sure you have credits in your account
- **Recommended**: Use GPT-4o for best results

**Reddit API Credentials:**
- Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
- Click "Create App" or "Create Another App"
- Choose "script" type
- Note your `client_id` (under the app name) and `client_secret`

### 3. Configure Environment
```bash
# Copy the example file
cp env.example .env

# Edit .env with your API keys
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=reddit_pain_finder_v2.0
```

### 4. Test Setup
```bash
python test_tool.py
```

### 5. Run the Tool
```bash
python main.py
```

## 💡 Example Usage

```
🎯 Enhanced Reddit Pain Point Finder
==============================================
Enter a topic/niche to analyze: indie game developers

🚀 Starting pain point analysis for topic: indie game developers
🔎 Finding subreddits for: indie game developers
📍 Found subreddits: ['gamedev', 'IndieGaming', 'gamedesign']
📄 Retrieving posts from subreddits...
  📥 Fetching posts from r/gamedev
    📈 Found 15 yearly top posts
    🔥 Found 15 hot posts
    🔄 Processing 28 unique posts
✅ Successfully retrieved 67 posts
🧠 Analyzing posts for pain points...
  🧠 Step 1: Extracting pain points from posts...
  ✅ Extracted 23 individual pain points
  🔄 Step 2: Clustering pain points for frequency analysis...
    📥 Loading sentence transformer model...
    🎯 Identified 5 pain point clusters
  🔥 Step 3: Scoring desperation and creating enhanced output...
  ✅ Created 5 enhanced pain point clusters

======================================================================
🎯 ENHANCED PAIN POINT ANALYSIS: INDIE GAME DEVELOPERS
======================================================================
📊 Summary: 5 clusters found across 3 subreddits
📈 Total Pain Points: 23
🔥 Average Desperation Score: 6.8/10
📊 Average Pain Score: 6.4/10
🚨 High Priority Clusters (7+ desperation): 3

🔥 TOP PAIN POINT CLUSTERS (by priority):
--------------------------------------------------

1. 🎯 Cluster: cluster_0
   📝 Problem: Marketing games with zero budget
   🔥 Desperation Score: 9/10 | Pain Score: 7.8/10
   📊 Frequency: 8 posts | Avg Upvotes: 156.3
   📍 Subreddits: gamedev, IndieGaming
   👥 Market: 1,250,000 subscribers, ~16 posts/week
   💡 MVP Opportunity: Marketing automation tool for indie game developers
   🔗 Sample: How do you market your game when you have absolutely no budget?...
      📎 https://reddit.com/r/gamedev/...

💾 Enhanced JSON output saved to: pain_analysis_indie_game_developers.json
```

## 🏗️ Architecture

### Enhanced LangGraph Workflow
```
User Input → Subreddit Finder → Post Retriever → Pain Parser & Clusterer → Enhanced Output
```

### Key Components
- **`agents/subreddit_finder.py`**: GPT-4o powered subreddit discovery (top 3)
- **`agents/post_retriever.py`**: Enhanced Reddit data collection (yearly + hot posts)
- **`agents/pain_parser.py`**: AI-powered clustering, desperation scoring, market analysis
- **`main.py`**: LangGraph workflow with JSON output
- **`utils/reddit_api.py`**: Reddit API client setup

### Enhanced Features (Phase 1)
- **Semantic Clustering**: Uses sentence-transformers to group similar pain points
- **Desperation Analysis**: GPT-4o measures emotional intensity
- **Market Proxy Data**: Subscriber counts and post frequency estimates
- **JSON Export**: Structured output for further analysis

## 🎨 Enhanced Output Categories

The tool now provides structured analysis across:
- **Cluster Analysis**: Grouped pain points with frequency data
- **Desperation Scoring**: Emotional intensity measurement (1-10)
- **Market Insights**: Subscriber base and activity estimates
- **Priority Ranking**: Combined frequency × desperation × pain score

## 🔧 Troubleshooting

**"Reddit API credentials not found"**
- Make sure your `.env` file exists and has the correct Reddit credentials
- Verify your Reddit app is set to "script" type

**"OpenAI API key not found"**
- Check your `.env` file has the OpenAI API key
- Ensure you have credits in your OpenAI account
- For best results, use GPT-4o model

**"Clustering failed" or sentence-transformer errors**
- First run may take longer as it downloads the embedding model
- Ensure you have enough disk space and internet connection
- Tool will fallback to individual analysis if clustering fails

**Rate limiting issues**
- The tool respects Reddit API limits
- If you hit limits, wait a few minutes before running again
- Enhanced version includes delays to prevent rate limiting

## 🚀 Next Steps

After finding clustered pain points:
1. **Focus on high desperation clusters** (7+ scores) for immediate opportunities
2. **Validate frequency data** by engaging with the communities  
3. **Research existing solutions** for high-frequency problems
4. **Build quick prototypes** for top-ranked clusters
5. **Use JSON output** for further programmatic analysis

## 📝 Tips for Best Results

- **Be specific**: "college students" → "computer science students"
- **Try variations**: "remote workers", "freelancers", "digital nomads"
- **Focus on active communities**: Tool now limits to top 3 most active subreddits
- **Look for cluster patterns**: Multiple similar pain points = validated problem
- **Check desperation scores**: Higher emotional intensity = better opportunity

---

Built with ❤️ for founders seeking real problems to solve.
**Phase 1**: Enhanced with clustering, desperation scoring, and market insights. 