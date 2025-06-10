from typing import List, Dict, Any
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import time
import re
from datetime import datetime, timedelta
import tiktoken

load_dotenv()

def get_openai_client():
    """Initialize OpenAI client."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found in .env file")
    return OpenAI(api_key=api_key)

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback approximation: ~4 chars per token
        return len(text) // 4

def truncate_to_token_limit(text: str, max_tokens: int = 8000, model: str = "gpt-4o") -> str:
    """Truncate text to stay within token limit (Phase 2 Task 2 guardrail)."""
    if count_tokens(text, model) <= max_tokens:
        return text
    
    # Reserve tokens for truncation marker
    truncation_marker = "\n\n[TRUNCATED TO STAY WITHIN TOKEN LIMIT]"
    marker_tokens = count_tokens(truncation_marker, model)
    available_tokens = max_tokens - marker_tokens
    
    if available_tokens <= 0:
        return truncation_marker[:max_tokens] if max_tokens > 0 else ""
    
    # Binary search for optimal truncation point
    low, high = 0, len(text)
    best_length = 0
    
    while low <= high:
        mid = (low + high) // 2
        chunk = text[:mid]
        chunk_tokens = count_tokens(chunk, model)
        
        if chunk_tokens <= available_tokens:
            best_length = mid
            low = mid + 1
        else:
            high = mid - 1
    
    # Ensure we don't go over the limit even with rounding errors
    while best_length > 0 and count_tokens(text[:best_length] + truncation_marker, model) > max_tokens:
        best_length -= 10  # Reduce by small chunks to be safe
    
    if best_length <= 0:
        return truncation_marker[:max_tokens] if max_tokens > 0 else ""
    
    truncated = text[:best_length] + truncation_marker
    return truncated

def calculate_engagement_weight(post: Dict[str, Any]) -> float:
    """
    Phase 2 Task 1: Calculate engagement-weighted score for pain points.
    Uses frequency, normalized scores, comment engagement, and age decay.
    """
    # Normalize metrics (0-1 scale) with proper defaults for missing fields
    score_norm = min(post.get('score', 0) / 1000, 1.0)  # Cap at 1000 upvotes = 1.0
    comment_norm = min(post.get('num_comments', 0) / 100, 1.0)  # Cap at 100 comments = 1.0
    
    # Age decay factor (already calculated in post_retriever)
    age_decay = post.get('age_decay_factor', 1.0)
    
    # Engagement factors with defaults
    upvote_ratio = post.get('upvote_ratio', 0.8)
    controversy_boost = 1 + (post.get('controversy_score', 0) * 0.2)  # Controversial posts get slight boost
    comment_engagement = 1 + (post.get('comment_engagement_ratio', 0) * 0.1)
    
    # Awards provide additional signal
    awards_boost = 1 + (post.get('total_awards_received', 0) * 0.05)
    
    # Combined weight formula: w = f(freq, score_norm, comment_norm, age_decay)
    weight = (
        score_norm * 0.4 +           # Upvote score (40%)
        comment_norm * 0.25 +        # Comment engagement (25%)
        upvote_ratio * 0.15          # Community approval (15%)
    ) * age_decay * controversy_boost * comment_engagement * awards_boost
    
    return weight

def prepare_post_content_with_comments(post: Dict[str, Any]) -> str:
    """
    Phase 2 Task 2: Prepare post content with comment context injection.
    Includes top comments and applies 8k token limit guardrail.
    """
    # Build comprehensive post content
    content_parts = []
    
    # Main post content
    content_parts.append(f"TITLE: {post.get('title', '')}")
    if post.get('body'):
        content_parts.append(f"POST BODY: {post.get('body', '')}")
    
    # Add metadata for context
    content_parts.append(f"ENGAGEMENT: {post.get('score', 0)} upvotes, {post.get('num_comments', 0)} comments, {post.get('upvote_ratio', 0):.1%} upvote ratio")
    
    # Phase 2 Task 2: Add top comments for clarifying anecdotes/solutions
    if post.get('comments'):
        content_parts.append("TOP COMMENTS:")
        for i, comment in enumerate(post['comments'][:5], 1):
            if isinstance(comment, dict):
                author_note = " (OP)" if comment.get('is_submitter') else ""
                content_parts.append(f"Comment {i} ({comment.get('score', 0)} pts{author_note}): {comment.get('body', '')}")
    
    combined_content = "\n\n".join(content_parts)
    
    # Phase 2 Task 2: Apply 8k token guardrail to control cost
    return truncate_to_token_limit(combined_content, max_tokens=8000)

def extract_and_parse_json_robust(response_text: str) -> Dict[Any, Any]:
    """
    Enhanced JSON extraction with comprehensive error handling and multiple fallback strategies.
    This fixes the common JSON parsing issues encountered with LLM responses.
    """
    
    # Strategy 1: Direct parse (fastest)
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Find JSON in markdown code blocks
    json_patterns = [
        r'```(?:json)?\s*(\{.*?\})\s*```',  # ```json or ``` blocks
        r'```(\{.*?\})```',                  # Simple ``` blocks
        r'`(\{.*?\})`'                       # Single backtick blocks
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    
    # Strategy 3: Extract JSON object manually by counting braces
    text = response_text.strip()
    
    # Find first opening brace
    start = text.find('{')
    if start == -1:
        raise json.JSONDecodeError("No JSON object found", response_text, 0)
    
    # Count braces to find matching closing brace
    brace_count = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_str = text[start:i+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    break
    
    # Strategy 4: Clean common LLM response patterns
    cleaned = response_text.strip()
    
    # Remove common LLM prefixes
    prefixes_to_remove = [
        "Here's the analysis:",
        "Here is the analysis:",
        "Analysis:",
        "The pain point analysis:",
        "JSON response:",
        "The JSON response is:",
        "JSON:",
        "Result:",
        "Output:",
        "Response:",
    ]
    
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
    
    # Remove trailing explanations after JSON
    if cleaned.startswith('{'):
        brace_count = 0
        for i, char in enumerate(cleaned):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    cleaned = cleaned[:i+1]
                    break
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Strategy 5: Try to fix common JSON formatting issues
    # Fix unescaped quotes in strings
    try:
        # This is a simple fix for common quote issues - more sophisticated parsing could be added
        fixed_text = re.sub(r'(?<!\\)"(?=\w)', '\\"', cleaned)
        return json.loads(fixed_text)
    except json.JSONDecodeError:
        pass
    
    # If all strategies fail, provide detailed error information
    raise json.JSONDecodeError(
        f"All JSON parsing strategies failed. Response was: {response_text[:200]}...", 
        response_text, 
        0
    )

def parse_single_pain_point(post: Dict[str, Any], client: OpenAI, model: str) -> Dict[str, Any]:
    """
    Parse a single post for pain points with enhanced Phase 2 features.
    Returns None if parsing fails completely.
    """
    try:
        # Phase 2 Task 2: Prepare enhanced post content with comments
        post_content = prepare_post_content_with_comments(post)
        
        # Enhanced prompt with stronger JSON instructions
        prompt = f"""
You are an expert at identifying business problems and pain points from social media discussions. 

Analyze this Reddit post and its comments to identify the main pain point or problem being discussed.

POST DATA:
{post_content}

INSTRUCTIONS:
1. Identify the primary pain point, frustration, or problem discussed
2. Score the pain intensity from 1-10 (1=minor inconvenience, 10=major life/business problem)
3. Suggest a potential MVP solution that could address this pain point
4. If no clear pain point exists, return pain_score: 0

CRITICAL: You must respond with ONLY valid JSON in exactly this format:
{{
    "summary": "Brief description of the main pain point",
    "pain_score": 5,
    "mvp_suggestion": "Potential MVP solution to address this problem",
    "problem_category": "Category of the problem (e.g., productivity, finance, education, etc.)"
}}

Do not include any text before or after the JSON. Do not use markdown code blocks. Return only the raw JSON object.
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert business analyst who identifies problems and opportunities from social discussions. You MUST respond with only valid JSON, no additional text whatsoever."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Lower temperature for more consistent JSON output
            max_tokens=400
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Use robust JSON parsing
        try:
            analysis = extract_and_parse_json_robust(response_text)
            
            # Validate required fields
            required_fields = ['summary', 'pain_score', 'mvp_suggestion', 'problem_category']
            for field in required_fields:
                if field not in analysis:
                    print(f"  ⚠️ Missing required field '{field}' in response for post: {post.get('title', 'Unknown')[:50]}...")
                    return None
            
            # Validate pain_score is numeric
            try:
                pain_score = float(analysis['pain_score'])
                analysis['pain_score'] = min(10, max(0, pain_score))
            except (ValueError, TypeError):
                print(f"  ⚠️ Invalid pain_score in response for post: {post.get('title', 'Unknown')[:50]}...")
                return None
            
            # Phase 2 Task 1: Calculate engagement weight for this pain point
            engagement_weight = calculate_engagement_weight(post)
            
            # Enhanced pain point data with Phase 2 metrics
            pain_point = {
                **analysis,
                'engagement_weight': engagement_weight,
                'post_score': post.get('score', 0),
                'post_title': post.get('title', ''),
                'subreddit': post.get('subreddit', ''),
                'subreddit_subscribers': post.get('subreddit_subscribers', 0),
                'source_url': post.get('url', ''),
                'created_utc': post.get('created_utc', 0),
                'age_days': post.get('age_days', 0),
                'num_comments': post.get('num_comments', 0),
                'upvote_ratio': post.get('upvote_ratio', 0),
                'full_post_content': post_content  # Store for desperation scoring
            }
            
            return pain_point
            
        except Exception as e:
            print(f"  ❌ JSON parsing error for post '{post.get('title', 'Unknown')[:50]}...': {str(e)}")
            print(f"     Raw response: {response_text[:200]}...")
            return None
            
    except Exception as e:
        print(f"  ❌ Error analyzing post '{post.get('title', 'Unknown')[:50]}...': {str(e)}")
        return None

def dedupe_clusters_with_llm(cluster_representatives: List[Dict[str, Any]], client: OpenAI, model: str) -> List[Dict[str, Any]]:
    """
    Phase 2 Task 3: LLM-assisted deduping of near-identical pain points.
    After cosine filtering, send cluster reps to GPT-4o to merge duplicates.
    """
    if len(cluster_representatives) <= 1:
        return cluster_representatives
    
    try:
        # Prepare cluster summaries for LLM analysis
        cluster_summaries = []
        for i, cluster in enumerate(cluster_representatives):
            cluster_summaries.append(f"Cluster {i}: {cluster['summary']}")
        
        dedup_prompt = f"""
You are an expert at identifying duplicate business problems. Analyze these pain point clusters and identify which ones refer to the same underlying frustration or problem.

CLUSTERS TO ANALYZE:
{chr(10).join(cluster_summaries)}

INSTRUCTIONS:
1. Identify groups of clusters that refer to the same core problem
2. For each group, specify which cluster numbers should be merged
3. If no clusters should be merged, respond with "no_merges"

Respond with ONLY a JSON array in this exact format:
[
  {{
    "merge_group": [0, 2, 5],
    "reason": "All relate to the same underlying issue with X"
  }},
  {{
    "merge_group": [1, 3],
    "reason": "Both about Y problem"
  }}
]

Or if no merges needed:
"no_merges"

Return only the JSON, no additional text.
"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at identifying duplicate business problems. Respond with only JSON, no additional text."},
                {"role": "user", "content": dedup_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content.strip()
        
        if response_text.lower() == '"no_merges"' or response_text.lower() == 'no_merges':
            print(f"    🔍 LLM deduping: No merges needed")
            return cluster_representatives
        
        # Parse merge instructions
        merge_instructions = json.loads(response_text)
        
        # Apply merges
        merged_clusters = []
        processed_indices = set()
        
        for merge_group in merge_instructions:
            indices_to_merge = merge_group['merge_group']
            if any(i in processed_indices for i in indices_to_merge):
                continue  # Skip if already processed
            
            # Merge clusters by combining their data
            primary_cluster = cluster_representatives[indices_to_merge[0]]
            for idx in indices_to_merge[1:]:
                if idx < len(cluster_representatives):
                    secondary = cluster_representatives[idx]
                    # Combine engagement weights
                    primary_cluster['engagement_weight'] += secondary['engagement_weight']
                    primary_cluster['frequency'] = primary_cluster.get('frequency', 1) + secondary.get('frequency', 1)
            
            merged_clusters.append(primary_cluster)
            processed_indices.update(indices_to_merge)
        
        # Add non-merged clusters
        for i, cluster in enumerate(cluster_representatives):
            if i not in processed_indices:
                merged_clusters.append(cluster)
        
        print(f"    🔍 LLM deduping: Merged {len(cluster_representatives)} -> {len(merged_clusters)} clusters")
        return merged_clusters
        
    except Exception as e:
        print(f"    ⚠️ LLM deduping failed: {str(e)}, keeping original clusters")
        return cluster_representatives

def calculate_temporal_trends(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Phase 2 Task 4: Temporal trend tagging.
    Bucket posts by week and compute slope of mentions (rolling 4-week).
    Tag clusters "🆙 trending" if slope > threshold.
    """
    current_time = time.time()
    four_weeks_ago = current_time - (4 * 7 * 24 * 3600)
    
    for cluster in clusters:
        try:
            # Initialize trend fields for all clusters
            cluster['trend_tag'] = ""
            cluster['trend_slope'] = 0
            
            # Get timestamps for all pain points in cluster
            if 'related_pain_points' not in cluster:
                continue
                
            timestamps = []
            for pain_point in cluster['related_pain_points']:
                if 'created_utc' in pain_point:
                    timestamps.append(pain_point['created_utc'])
            
            if len(timestamps) < 3:  # Need minimum data for trend
                continue
            
            # Filter to last 4 weeks
            recent_timestamps = [ts for ts in timestamps if ts >= four_weeks_ago]
            
            if len(recent_timestamps) < 2:
                continue
            
            # Bucket by week and count mentions
            week_buckets = {}
            for ts in recent_timestamps:
                week_start = int((ts - four_weeks_ago) // (7 * 24 * 3600))
                week_buckets[week_start] = week_buckets.get(week_start, 0) + 1
            
            # Calculate trend slope (simple linear regression)
            weeks = list(week_buckets.keys())
            counts = list(week_buckets.values())
            
            if len(weeks) >= 2:
                # Simple slope calculation
                n = len(weeks)
                sum_x = sum(weeks)
                sum_y = sum(counts)
                sum_xy = sum(w * c for w, c in zip(weeks, counts))
                sum_x2 = sum(w * w for w in weeks)
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                
                # Tag as trending if slope > 0.5 (more than 0.5 additional mentions per week)
                if slope > 0.5:
                    cluster['trend_tag'] = "🆙 trending"
                    cluster['trend_slope'] = round(slope, 2)
                else:
                    cluster['trend_tag'] = ""
                    cluster['trend_slope'] = round(slope, 2)
            else:
                cluster['trend_tag'] = ""
                cluster['trend_slope'] = 0
                
        except Exception as e:
            print(f"    ⚠️ Trend calculation failed for cluster: {str(e)}")
            cluster['trend_tag'] = ""
            cluster['trend_slope'] = 0
    
    return clusters

def parse_pain_points(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse pain points from posts and comments using LLM, then cluster and enhance with Phase 2 features.
    
    Args:
        posts: List of post dictionaries
        
    Returns:
        List of enhanced cluster dictionaries with engagement weighting and Phase 2 features
    """
    if not posts:
        return []
    
    client = get_openai_client()
    pain_points = []
    
    print("  🧠 Step 1: Extracting pain points from posts with enhanced context...")
    
    # Use GPT-4o as specified in task 11
    model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    # Step 1: Extract individual pain points with Phase 2 enhancements
    successful_parses = 0
    failed_parses = 0
    
    for i, post in enumerate(posts):
        result = parse_single_pain_point(post, client, model)
        if result:
            pain_points.append(result)
            successful_parses += 1
        else:
            failed_parses += 1
        
        # Add delay to avoid rate limiting
        if i > 0 and i % 5 == 0:  # Every 5 requests
            time.sleep(1)
    
    print(f"  ✅ Successfully parsed {successful_parses} posts, {failed_parses} failed")
    
    if not pain_points:
        print("  ❌ No pain points identified")
        return []
    
    print(f"  ✅ Extracted {len(pain_points)} individual pain points")
    
    # Step 2: Build frequency map using clustering with cosine similarity
    print("  🔄 Step 2: Clustering pain points with engagement weighting...")
    
    try:
        # Initialize sentence transformer for embeddings
        print("    📥 Loading sentence transformer model...")
        embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight but effective model
        
        # Create embeddings from pain point summaries
        pain_texts = [point['summary'] for point in pain_points]
        embeddings = embedder.encode(pain_texts)
        
        # Determine optimal number of clusters (but cap at reasonable number)
        n_clusters = min(max(2, len(pain_points) // 3), 8)  # Between 2-8 clusters
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        print(f"    🎯 Identified {n_clusters} pain point clusters")
        
    except Exception as e:
        print(f"  ⚠️ Clustering failed: {str(e)}, falling back to individual points")
        # Fallback: treat each pain point as its own cluster
        cluster_labels = list(range(len(pain_points)))
        n_clusters = len(pain_points)
    
    # Step 3: Group into clusters and calculate Phase 2 enhanced metrics
    clusters = {}
    for i, pain_point in enumerate(pain_points):
        cluster_id = int(cluster_labels[i])
        
        if cluster_id not in clusters:
            clusters[cluster_id] = {
                'pain_points': [],
                'embeddings': []
            }
        
        clusters[cluster_id]['pain_points'].append(pain_point)
        if 'embeddings' in locals():
            clusters[cluster_id]['embeddings'].append(embeddings[i])
    
    # Step 4: Create cluster representatives for deduping
    cluster_representatives = []
    for cluster_id, cluster_data in clusters.items():
        cluster_points = cluster_data['pain_points']
        
        # Phase 2 Task 1: Find representative post using engagement weight instead of just score
        representative_post = max(cluster_points, key=lambda x: x['engagement_weight'])
        representative_post['cluster_id'] = cluster_id
        representative_post['frequency'] = len(cluster_points)
        cluster_representatives.append(representative_post)
    
    # Step 5: Phase 2 Task 3 - LLM-assisted deduping
    print("  🔍 Step 3: LLM-assisted deduping of similar clusters...")
    deduplicated_representatives = dedupe_clusters_with_llm(cluster_representatives, client, model)
    
    # Step 6: Score desperation and create enhanced output
    print("  🔥 Step 4: Scoring desperation and creating enhanced output...")
    
    enhanced_clusters = []
    
    for representative in deduplicated_representatives:
        cluster_id = representative.get('cluster_id', 0)
        cluster_points = clusters.get(cluster_id, {}).get('pain_points', [representative])
        
        # Phase 2 Task 1: Calculate engagement-weighted metrics
        total_engagement_weight = sum(p['engagement_weight'] for p in cluster_points)
        total_frequency = len(cluster_points)
        avg_upvotes = np.mean([p['post_score'] for p in cluster_points])
        avg_pain_score = np.mean([p['pain_score'] for p in cluster_points])
        
        # Calculate market proxy data (Task 14)
        total_subscribers = sum(set(p['subreddit_subscribers'] for p in cluster_points))
        
        # Estimate posts per week (rough approximation based on post frequency)
        unique_subreddits = set(p['subreddit'] for p in cluster_points)
        posts_per_week = len(cluster_points) * 2  # Rough estimate
        
        # Score desperation via LLM (Task 13) with enhanced error handling
        try:
            desperation_prompt = f"""
Analyze this Reddit post for emotional desperation and urgency. Score from 1-10 where:
1-3: Mild frustration, casual mention
4-6: Notable concern, seeking solutions
7-8: High frustration, repeated failed attempts
9-10: Desperate, urgent, major impact on life/business

POST CONTENT:
{representative['full_post_content'][:1500]}...

Respond with ONLY a single number from 1-10, no explanation or additional text.
"""
            
            desp_response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert at measuring emotional intensity and desperation in text. Return only a single number from 1-10, nothing else."},
                    {"role": "user", "content": desperation_prompt}
                ],
                temperature=0.1,
                max_tokens=5
            )
            
            desperation_text = desp_response.choices[0].message.content.strip()
            
            # Extract number from response
            desperation_match = re.search(r'\b([1-9]|10)\b', desperation_text)
            if desperation_match:
                desperation_score = int(desperation_match.group(1))
            else:
                desperation_score = int(avg_pain_score)  # Fallback
                
        except Exception as e:
            print(f"    ⚠️ Desperation scoring failed for cluster {cluster_id}: {str(e)}")
            # Fallback to pain score if desperation scoring fails
            desperation_score = int(avg_pain_score)
        
        # Create enhanced cluster output (Task 15)
        enhanced_cluster = {
            "cluster_id": f"cluster_{cluster_id}",
            "topic": representative['summary'],
            "frequency": total_frequency,
            "desperation_score": desperation_score,
            "avg_pain_score": round(avg_pain_score, 1),
            # Phase 2 Task 1: Include engagement weight instead of just frequency
            "total_engagement_weight": round(total_engagement_weight, 2),
            "avg_engagement_weight": round(total_engagement_weight / total_frequency, 2),
            "market_proxy": {
                "subscribers": int(total_subscribers),
                "posts_per_week": posts_per_week,
                "unique_subreddits": len(unique_subreddits)
            },
            "sample_post": {
                "title": representative['post_title'],
                "subreddit": representative['subreddit'],
                "url": representative['source_url'],
                "score": representative['post_score']
            },
            "avg_upvotes": round(avg_upvotes, 1),
            "problem_category": representative['problem_category'],
            "mvp_suggestion": representative['mvp_suggestion'],
            "all_subreddits": list(unique_subreddits),
            "related_pain_points": [
                {
                    "summary": p['summary'],
                    "pain_score": p['pain_score'],
                    "engagement_weight": p['engagement_weight'],
                    "subreddit": p['subreddit'],
                    "created_utc": p.get('created_utc', 0)
                } for p in cluster_points
            ]
        }
        
        enhanced_clusters.append(enhanced_cluster)
        
        # Small delay to avoid rate limiting
        time.sleep(0.2)
    
    # Phase 2 Task 4: Add temporal trend analysis
    print("  📈 Step 5: Analyzing temporal trends...")
    enhanced_clusters = calculate_temporal_trends(enhanced_clusters)
    
    # Phase 2 Task 1: Sort clusters by engagement-weighted score instead of raw frequency
    enhanced_clusters.sort(
        key=lambda x: x['total_engagement_weight'] * x['desperation_score'] * x['avg_pain_score'], 
        reverse=True
    )
    
    print(f"  ✅ Created {len(enhanced_clusters)} enhanced pain point clusters with Phase 2 features")
    return enhanced_clusters 