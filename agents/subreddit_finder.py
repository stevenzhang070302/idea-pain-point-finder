import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_openai_client():
    """Initialize OpenAI client."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found in .env file")
    return OpenAI(api_key=api_key)

def find_subreddits(topic: str) -> list[str]:
    """
    Use LLM to find the 3 most relevant subreddits for a given topic.
    
    Args:
        topic: The topic/niche to find subreddits for
        
    Returns:
        List of exactly 3 subreddit names (without r/ prefix)
    """
    client = get_openai_client()
    
    prompt = f"""
You are an expert at identifying the most active Reddit communities for finding pain points and startup opportunities. Given a topic, find the 3 BEST subreddits where people actively discuss problems, frustrations, and pain points.

Topic: "{topic}"

Requirements:
- Find exactly 3 subreddits with the highest activity and pain point discussions
- Prioritize communities where people frequently complain, ask for help, or share frustrations
- Focus on active communities with regular posts and engagement
- Avoid niche/dead subreddits - prioritize larger, more active communities
- Return ONLY the subreddit names without "r/" prefix
- Return one subreddit per line
- No explanations or additional text
- Order by relevance and activity level (most active first)

Example for "college students":
college
StudentLoans
ApplyingToCollege

Now find the 3 best subreddits for: "{topic}"
"""

    try:
        # Use GPT-4o as specified in task 11
        model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert Reddit analyst focused on finding communities with high pain point discussions for startup research."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Lower temperature for more consistent results
            max_tokens=150
        )
        
        # Extract subreddit names from response
        content = response.choices[0].message.content.strip()
        
        # Parse subreddit names (remove any r/ prefixes and clean up)
        subreddits = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                # Remove r/ prefix if present
                subreddit = re.sub(r'^r/', '', line)
                # Remove any extra characters and keep only valid subreddit names
                subreddit = re.sub(r'[^a-zA-Z0-9_]', '', subreddit)
                if subreddit and len(subreddit) > 2:  # Basic validation
                    subreddits.append(subreddit)
        
        # Ensure exactly 3 subreddits
        return subreddits[:3]
        
    except Exception as e:
        print(f"Error finding subreddits: {str(e)}")
        # Fallback to some general subreddits if API fails
        return ["AskReddit", "LifeProTips", "mildlyinfuriating"][:3] 