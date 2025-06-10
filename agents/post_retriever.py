from typing import List, Dict, Any
from utils.reddit_api import get_reddit_client
import praw
import time

def retrieve_posts(subreddits: List[str]) -> List[Dict[str, Any]]:
    """
    Retrieve top posts from given subreddits using PRAW.
    Fetches both yearly top posts and hot posts for comprehensive coverage.
    Enhanced for Phase 2: Collects engagement metrics for weighted scoring.
    
    Args:
        subreddits: List of subreddit names
        
    Returns:
        List of post dictionaries with enhanced metadata for engagement weighting
    """
    if not subreddits:
        return []
    
    reddit = get_reddit_client()
    all_posts = []
    
    for subreddit_name in subreddits:
        try:
            print(f"  📥 Fetching posts from r/{subreddit_name}")
            subreddit = reddit.subreddit(subreddit_name)
            
            # Collect posts from multiple sources for better coverage
            posts_to_process = []
            
            # Get top 15 posts from the past year (task 10)
            try:
                yearly_top = list(subreddit.top(time_filter="year", limit=15))
                posts_to_process.extend(yearly_top)
                print(f"    📈 Found {len(yearly_top)} yearly top posts")
            except Exception as e:
                print(f"    ⚠️ Could not fetch yearly top posts: {str(e)}")
            
            # Get top 15 hot posts for freshness (task 10)
            try:
                hot_posts = list(subreddit.hot(limit=15))
                posts_to_process.extend(hot_posts)
                print(f"    🔥 Found {len(hot_posts)} hot posts")
            except Exception as e:
                print(f"    ⚠️ Could not fetch hot posts: {str(e)}")
            
            # Remove duplicates based on post ID
            seen_ids = set()
            unique_posts = []
            for post in posts_to_process:
                if post.id not in seen_ids:
                    seen_ids.add(post.id)
                    unique_posts.append(post)
            
            print(f"    🔄 Processing {len(unique_posts)} unique posts")
            
            # Process each unique post with enhanced metadata collection
            for submission in unique_posts:
                # Skip stickied posts (announcements, etc.)
                if submission.stickied:
                    continue
                
                # Skip posts with very low engagement (likely spam or low quality)
                if submission.score < 5:
                    continue
                
                # Phase 2 Task 2: Get top comments with enhanced metadata
                submission.comments.replace_more(limit=0)  # Remove "load more" comments
                top_comments = []
                
                # Sort comments by score and get top k (enhanced for Phase 2)
                sorted_comments = sorted(
                    [c for c in submission.comments if hasattr(c, 'body')], 
                    key=lambda x: x.score, 
                    reverse=True
                )
                
                for comment in sorted_comments[:5]:  # Top 5 by score
                    if (hasattr(comment, 'body') and 
                        comment.body not in ['[deleted]', '[removed]', ''] and 
                        len(comment.body) > 10):
                        
                        top_comments.append({
                            'body': comment.body,
                            'score': comment.score,
                            'author': str(comment.author) if comment.author else '[deleted]',
                            'created_utc': comment.created_utc,  # For temporal analysis
                            'is_submitter': comment.is_submitter  # OP replies are important
                        })
                
                # Only include posts that have substantial content
                if len(submission.title) < 10 and len(submission.selftext) < 20 and len(top_comments) == 0:
                    continue
                
                # Calculate age in days for decay factor
                current_time = time.time()
                age_days = (current_time - submission.created_utc) / (24 * 3600)
                
                # Enhanced post data for Phase 2 engagement weighting
                post_data = {
                    'subreddit': subreddit_name,
                    'title': submission.title,
                    'body': submission.selftext if submission.selftext else '',
                    'comments': top_comments,
                    'url': f"https://reddit.com{submission.permalink}",
                    
                    # Phase 2 Task 1: Enhanced engagement metrics
                    'score': submission.score,
                    'num_comments': submission.num_comments,
                    'created_utc': submission.created_utc,
                    'upvote_ratio': submission.upvote_ratio,
                    'age_days': age_days,
                    
                    # Additional engagement signals
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'total_awards_received': getattr(submission, 'total_awards_received', 0),
                    'subreddit_subscribers': subreddit.subscribers,  # Market proxy data
                    'permalink': submission.permalink,
                    'post_id': submission.id,
                    
                    # Derived engagement metrics for weighting
                    'comment_engagement_ratio': min(submission.num_comments / max(submission.score, 1), 10),  # Comments per upvote (capped)
                    'controversy_score': 1 - submission.upvote_ratio,  # Higher = more controversial
                    
                    # Age decay factor (exponential decay with 30-day half-life)
                    'age_decay_factor': 2 ** (-age_days / 30),
                    
                    # Combined engagement score (for initial sorting)
                    'raw_engagement_score': (
                        submission.score * 
                        submission.upvote_ratio * 
                        (1 + submission.num_comments * 0.1) *  # Comments boost
                        (2 ** (-age_days / 30))  # Age decay
                    )
                }
                
                all_posts.append(post_data)
                
        except Exception as e:
            print(f"  ❌ Error fetching from r/{subreddit_name}: {str(e)}")
            continue
    
    # Sort by raw engagement score to prioritize high-engagement posts
    all_posts.sort(key=lambda x: x['raw_engagement_score'], reverse=True)
    
    print(f"  ✅ Successfully retrieved {len(all_posts)} posts with enhanced engagement metrics")
    return all_posts 