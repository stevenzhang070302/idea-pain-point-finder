import os
import praw
from dotenv import load_dotenv

load_dotenv()

def get_reddit_client():
    """Initialize and return a Reddit client using PRAW."""
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'reddit_pain_finder_v1.0')
    
    if not client_id or not client_secret:
        raise ValueError("Reddit API credentials not found in .env file")
    
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    
    return reddit 