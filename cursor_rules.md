// 📌 Build a simple MVP SaaS tool using LangGraph and OpenAI to extract pain points from Reddit.

// 🧠 GOAL:
// Create a LangGraph-based multi-agent system that:
// 1. Accepts a user-input topic (e.g. "college students", "indie game dev")
// 2. Uses an LLM to find 3–5 relevant subreddits
// 3. Fetches top posts from each subreddit
// 4. Uses a LangGraph parser agent (LLM) to identify and summarize pain points from posts + comments
// 5. Outputs a structured summary: subreddit → pain points → pain score → optional MVP suggestion

// 🧱 STACK:
// - Python 3.10+
// - LangGraph
// - OpenAI API
// - PRAW (Reddit API)
// - python-dotenv (for API key management)
// - Optional: Streamlit (for a dashboard interface later)

// 🗂 PROJECT STRUCTURE:
# reddit-pain-finder/
# ├── main.py                  # LangGraph flow controller
# ├── agents/
# │   ├── subreddit_finder.py     # LLM: topic → subreddits
# │   ├── post_retriever.py       # PRAW: subreddit → posts
# │   └── pain_parser.py          # LLM: post + comments → pain points
# ├── utils/
# │   └── reddit_api.py           # Reddit client setup
# ├── .env                        # API keys
# ├── requirements.txt
# └── README.md

// ✅ TASKS FOR Cursor AGENT:
Phase 1:
1. Scaffold all files + folders above.
2. Set up LangGraph flow with node stubs: start → find_subreddits → retrieve_posts → parse_pain → output.
3. Implement basic prompt for `subreddit_finder.py` agent:
   - Prompt: "List 3–5 active subreddits relevant to the topic: {input_topic}."
4. Implement PRAW wrapper to fetch top 10 posts per subreddit.
5. Implement basic LLM prompt for `pain_parser.py` agent:
   - Prompt: "Given this post and its top 5 comments, summarize the main pain point. Score its intensity from 1–10."
6. In `main.py`, orchestrate the LangGraph flow using these agents and print structured output to console.
7. Include `.env` loading logic and `.env.example` template.
8. Generate `requirements.txt` with all needed dependencies.

9. Limit to Top 3 Subreddits Change your find_subreddits agent prompt to return only the 3 most active/relevant subreddits. In your LangGraph workflow, slice the list to the first three before fetching posts.

10. Switch to Hot/Yearly & Top 15 Posts. In your PRAW wrapper (retrieve_posts node), for each subreddit: Fetch top posts from the past year (subreddit.top(time_filter="year", limit=15)). Also consider subreddit.hot(limit=15) for freshness comparison.

11. Integrate GPT-4o as Your LLM Update your LLM client initialization in .env.example and code to select gpt-4o as the model. Adjust any model-specific prompt parameters (e.g., temperature, max_tokens).

12. Build a Frequency Map: After you parse each post’s pain point text, collect them into a list. Use sentence-transformers to embed each pain-point string. Cluster embeddings with Faiss or simple cosine-similarity thresholds. Output a frequency table: {cluster_id → count, rep_post, avg_upvotes}.

13. Score Desperation via LLM For each representative post in a cluster, call GPT-4o with a prompt like: “On a scale of 1–10, how emotionally desperate is this author? Consider helplessness, repeated failures, urgency.” Append that score to your cluster summary.

14. Add Market-Size Proxy Data For each subreddit in the top 3, pull subreddit.subscribers. Use Pushshift or simple Reddit API calls to estimate posts per week on the same topic. Combine into a { subscribers, posts_per_week } field for each cluster.

15. Emit Enhanced JSON Output In your final output node, print a JSON array of clusters:
{
  "cluster_id": "...",
  "topic": "...",
  "frequency": 12,
  "desperation_score": 8,
  "market_proxy": { "subscribers": 250000, "posts_per_week": 5 },
  "sample_post": "...",
  "avg_upvotes": 42
}

16. Update Project Scaffolding & Docs
Revise requirements.txt to include sentence-transformers, faiss-cpu (or GPU), plus any Reddit-search libs.
Expand README with a “Phase 1: Enhanced scraping & scoring” section.
Ensure your .env.example includes keys for Pushshift (if used) and model selection.

Phase 2 Tasks: 

1. Implement updated engagement-weighted scoring. Frequency does not necessary represent importance. Upvotes, comment karma, award count, and age all signal urgency.  In post_retriever.py, collect score, upvote_ratio, num_comments, created_utc. Design a pain weight w = f(freq, score_norm, comment_norm, age_decay). Sort clusters by Σ w instead of raw count.

2. Get Comment-context injection by getting: Top comments often contain clarifying anecdotes/solutions. Improves LLM extraction accuracy & desperation rating.  For each post, pull top k comments by score. Concatenate title + selftext + comments with delimiters. Add a guardrail: truncate to 8 k tokens to control cost.

3. LLM-assisted deduping of near-identical pain points - You’re clustering embeddings, but duplicate wording still slips in.	After cosine filtering, send cluster reps to GPT-4o: “Merge any that refer to the same underlying frustration.”

4. Temporal trend tagging	A pain that’s rising this month is gold for MVPs. Store created_utc for each post. Bucket by week → compute slope of mentions (rolling 4-week). Tag clusters “🆙 trending” if slope > threshold.


(Manual Review Status so far: Completed Phase 1 and 2)

Phase 3:

1. Interactive dashboard - Topic search bar + results table. Heat-map of clusters vs. desperation/time. Drill-down modal with raw posts & comments. Next.js + Supabase. Keep LangGraph backend as a FastAPI microservice.

2. Saved searches & alerts - Users (founders, PMs) save a keyword set and get a weekly Slack/email digest of new high-desperation clusters.	TinyAuth + SQLite for accounts 1st. Automations: cron job calls your pipeline, stores JSON, triggers email via Postmark.

3. CSV / API export	Power users want to feed pains into their own idea-generators.	REST endpoint: GET /topics/:id/export.csv

Phase 4:

1. X / Twitter	Real-time venting & micro-pains.	Use Twitter Academic API v2 or rsshub + scraping.

2. Product Hunt & Indie Hackers comments	Validates if pains already have solutions; surfaces gaps.	Scrape daily “discussions” feed.

3. App Store / Play Store reviews	Direct product pain signals.	Use appreviews.dev or AppFigures API.

4. Stack Overflow “help” tags	Technical niches beyond Reddit.	Filter by [python] etc.; pull vote counts.

Phase 5: Derisking the business

// Improvements list:
1. Improve subreddit finder - search keyword on reddit then have agent semantically select top three recommended? Alot of relevant arent selected.

2. More debugging needed on the JSON parsing still some errors

3. Simplify engagement scoring later?

4. Add complexity in getting sentiment vote on comments to make whole evaluation per post

5. Temporal trends needs persistence database or something to save old runs - right now it just says no trends.

6. Savings runs in appropriate folders

7. When ui is analyzing instead of blank show analysis process


Simplied Agent Workflow:
[User Input: "Topic/Niche"]
          ↓
🔎 Subreddit Finder Agent (LLM)
    - Given a topic, find related subreddits

          ↓
📄 Post Retriever Agent
    - Fetch top N posts from each subreddit

          ↓
🧠 Pain Parser Agent (LLM)
    - Reads each post + comments
    - Infers pain points (not keyword-based!)
    - Outputs: problem summary + pain intensity (0–10)

          ↓
📊 Dashboard Output
    - Console or Streamlit: show subreddit → pain → score

# No frontend for now — just CLI.

# This is a fast, scrappy MVP. Prioritize simplicity and testability. Clean architecture not required yet. Let's build the bones.