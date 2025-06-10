from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
import json
import csv
import io
import sqlite3
import hashlib
from datetime import datetime, timedelta
import asyncio
import uvicorn

# Add parent directory to path to import your existing LangGraph system
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from main import create_workflow, State
except ImportError:
    print("⚠️ Warning: Could not import LangGraph system. Running in test mode.")
    # Mock functions for testing
    def create_workflow():
        class MockWorkflow:
            def compile(self):
                return self
            def invoke(self, state):
                return {
                    'final_output': {
                        'topic': state['topic'],
                        'analysis_summary': {
                            'total_clusters': 3,
                            'total_posts': 50,
                            'average_desperation_score': 7.5,
                            'high_priority_clusters': 2,
                            'total_engagement_weight': 150.0,
                            'trending_clusters': 1
                        },
                        'clusters': [
                            {
                                'cluster_id': 'test_cluster_1',
                                'topic': 'Test Pain Point 1',
                                'problem_category': 'Technical',
                                'frequency': 15,
                                'desperation_score': 8,
                                'avg_pain_score': 7.5,
                                'avg_upvotes': 25,
                                'total_engagement_weight': 80.0,
                                'trend_tag': '🆙 trending',
                                'market_proxy': {'subscribers': 50000, 'posts_per_week': 12},
                                'sample_post': {'title': 'Test post title', 'url': 'https://reddit.com/test'},
                                'mvp_suggestion': 'Build a test solution',
                                'all_subreddits': ['testdev', 'testing'],
                                'related_pain_points': []
                            }
                        ]
                    }
                }
        return MockWorkflow()
    
    class State(dict):
        pass

app = FastAPI(
    title="Reddit Pain Finder API",
    description="FastAPI microservice for Reddit pain point analysis using LangGraph",
    version="3.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_PATH = "../database/painpoints.db"

def init_database():
    """Initialize SQLite database for saved searches and results."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Analysis results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            topic_hash TEXT UNIQUE NOT NULL,
            results JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    # Saved searches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            keywords TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_run DATETIME,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # User accounts table (simple TinyAuth)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    ''')
    
    # Alert subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            search_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            slack_webhook TEXT,
            frequency TEXT DEFAULT 'weekly',
            min_desperation_score INTEGER DEFAULT 7,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (search_id) REFERENCES saved_searches (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Pydantic models
class AnalysisRequest(BaseModel):
    topic: str
    save_results: bool = True

class SavedSearchRequest(BaseModel):
    user_id: str
    topic: str
    keywords: Optional[str] = None

class AlertSubscriptionRequest(BaseModel):
    user_id: str
    search_id: int
    email: str
    slack_webhook: Optional[str] = None
    frequency: str = "weekly"
    min_desperation_score: int = 7

class UserRegistration(BaseModel):
    email: str
    password: str

class AnalysisResponse(BaseModel):
    id: str
    topic: str
    status: str
    results: Optional[Dict[str, Any]] = None
    created_at: str

# Helper functions
def get_topic_hash(topic: str) -> str:
    """Generate a hash for the topic to use as cache key."""
    return hashlib.md5(topic.lower().strip().encode()).hexdigest()

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DATABASE_PATH)

def hash_password(password: str) -> str:
    """Simple password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()

# Background task for running analysis
async def run_pain_analysis(topic: str, topic_hash: str):
    """Run the LangGraph pain analysis workflow in background."""
    try:
        # Create the workflow
        workflow = create_workflow()
        app_instance = workflow.compile()
        
        # Run the analysis
        initial_state = State(
            topic=topic,
            subreddits=[],
            posts=[],
            pain_clusters=[],
            final_output={}
        )
        
        result = app_instance.invoke(initial_state)
        
        # Save results to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(days=7)  # Cache for 7 days
        
        cursor.execute('''
            INSERT OR REPLACE INTO analysis_results 
            (topic, topic_hash, results, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (topic, topic_hash, json.dumps(result['final_output']), expires_at))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Analysis completed and saved for topic: {topic}")
        
    except Exception as e:
        print(f"❌ Error in background analysis for {topic}: {str(e)}")

# API Routes

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Reddit Pain Finder API v3.0",
        "phase": "3",
        "features": ["Interactive Dashboard", "Saved Searches", "Alerts", "CSV Export"]
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start a new pain point analysis."""
    topic_hash = get_topic_hash(request.topic)
    
    # Check if we have recent cached results
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, results, created_at 
        FROM analysis_results 
        WHERE topic_hash = ? AND expires_at > DATETIME('now')
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (topic_hash,))
    
    cached_result = cursor.fetchone()
    conn.close()
    
    if cached_result:
        # Return cached results
        return AnalysisResponse(
            id=str(cached_result[0]),
            topic=request.topic,
            status="completed",
            results=json.loads(cached_result[1]),
            created_at=cached_result[2]
        )
    
    # Start new analysis in background
    if request.save_results:
        background_tasks.add_task(run_pain_analysis, request.topic, topic_hash)
    
    return AnalysisResponse(
        id=topic_hash,
        topic=request.topic,
        status="processing",
        created_at=datetime.now().isoformat()
    )

@app.get("/analyze/{topic_hash}")
async def get_analysis_status(topic_hash: str):
    """Get analysis status and results."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, topic, results, created_at 
        FROM analysis_results 
        WHERE topic_hash = ?
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (topic_hash,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {"status": "not_found", "message": "Analysis not found"}
    
    return AnalysisResponse(
        id=str(result[0]),
        topic=result[1],
        status="completed",
        results=json.loads(result[2]),
        created_at=result[3]
    )

@app.get("/topics/{topic_id}/export.csv")
async def export_csv(topic_id: str):
    """Export analysis results as CSV."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT topic, results 
        FROM analysis_results 
        WHERE id = ? OR topic_hash = ?
    ''', (topic_id, topic_id))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    topic, results_json = result
    results = json.loads(results_json)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        'Cluster ID', 'Topic', 'Problem Category', 'Frequency', 
        'Desperation Score', 'Avg Pain Score', 'Avg Upvotes',
        'Engagement Weight', 'Trend Tag', 'Subscribers', 
        'Posts Per Week', 'Sample Post Title', 'Sample Post URL',
        'MVP Suggestion', 'Subreddits'
    ])
    
    # Write cluster data
    for cluster in results.get('clusters', []):
        writer.writerow([
            cluster.get('cluster_id', ''),
            cluster.get('topic', ''),
            cluster.get('problem_category', ''),
            cluster.get('frequency', 0),
            cluster.get('desperation_score', 0),
            cluster.get('avg_pain_score', 0),
            cluster.get('avg_upvotes', 0),
            cluster.get('total_engagement_weight', 0),
            cluster.get('trend_tag', ''),
            cluster.get('market_proxy', {}).get('subscribers', 0),
            cluster.get('market_proxy', {}).get('posts_per_week', 0),
            cluster.get('sample_post', {}).get('title', ''),
            cluster.get('sample_post', {}).get('url', ''),
            cluster.get('mvp_suggestion', ''),
            ', '.join(cluster.get('all_subreddits', []))
        ])
    
    output.seek(0)
    
    # Return as streaming response
    filename = f"pain_analysis_{topic.replace(' ', '_')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Saved Searches API
@app.post("/searches")
async def save_search(request: SavedSearchRequest):
    """Save a search for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO saved_searches (user_id, topic, keywords)
        VALUES (?, ?, ?)
    ''', (request.user_id, request.topic, request.keywords))
    
    search_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": search_id, "message": "Search saved successfully"}

@app.get("/searches/{user_id}")
async def get_user_searches(user_id: str):
    """Get all saved searches for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, topic, keywords, created_at, last_run, is_active
        FROM saved_searches 
        WHERE user_id = ? AND is_active = TRUE
        ORDER BY created_at DESC
    ''', (user_id,))
    
    searches = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": search[0],
            "topic": search[1],
            "keywords": search[2],
            "created_at": search[3],
            "last_run": search[4],
            "is_active": search[5]
        }
        for search in searches
    ]

# Alert Subscriptions API
@app.post("/alerts")
async def create_alert_subscription(request: AlertSubscriptionRequest):
    """Create an alert subscription for a saved search."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO alert_subscriptions 
        (user_id, search_id, email, slack_webhook, frequency, min_desperation_score)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        request.user_id, request.search_id, request.email,
        request.slack_webhook, request.frequency, request.min_desperation_score
    ))
    
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": alert_id, "message": "Alert subscription created successfully"}

@app.get("/alerts/{user_id}")
async def get_user_alerts(user_id: str):
    """Get all alert subscriptions for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.id, a.search_id, s.topic, a.email, a.slack_webhook,
               a.frequency, a.min_desperation_score, a.created_at
        FROM alert_subscriptions a
        JOIN saved_searches s ON a.search_id = s.id
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
    ''', (user_id,))
    
    alerts = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": alert[0],
            "search_id": alert[1],
            "topic": alert[2],
            "email": alert[3],
            "slack_webhook": alert[4],
            "frequency": alert[5],
            "min_desperation_score": alert[6],
            "created_at": alert[7]
        }
        for alert in alerts
    ]

# Simple TinyAuth endpoints
@app.post("/auth/register")
async def register_user(request: UserRegistration):
    """Register a new user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(request.password)
    
    try:
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', (request.email, password_hash))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"user_id": str(user_id), "message": "User registered successfully"}
        
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

@app.post("/auth/login")
async def login_user(request: UserRegistration):
    """Login user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(request.password)
    
    cursor.execute('''
        SELECT id FROM users 
        WHERE email = ? AND password_hash = ?
    ''', (request.email, password_hash))
    
    user = cursor.fetchone()
    
    if user:
        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = DATETIME('now')
            WHERE id = ?
        ''', (user[0],))
        conn.commit()
        conn.close()
        
        return {"user_id": str(user[0]), "message": "Login successful"}
    else:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True) 