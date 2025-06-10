#!/usr/bin/env python3
"""
Comprehensive test script for the Reddit Pain Point Finder
"""

import os
import json
import re
from dotenv import load_dotenv
from typing import Dict, Any, List

def test_api_keys():
    """Test if API keys are properly configured."""
    load_dotenv()
    
    openai_key = os.getenv('OPENAI_API_KEY')
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
    reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    
    print("🔧 Testing API Configuration...")
    print(f"OpenAI API Key: {'✅ Set' if openai_key else '❌ Missing'}")
    print(f"Reddit Client ID: {'✅ Set' if reddit_client_id else '❌ Missing'}")
    print(f"Reddit Client Secret: {'✅ Set' if reddit_client_secret else '❌ Missing'}")
    
    if not all([openai_key, reddit_client_id, reddit_client_secret]):
        print("\n❌ Missing API keys! Please:")
        print("1. Copy env.example to .env")
        print("2. Add your OpenAI API key")
        print("3. Add your Reddit API credentials")
        print("4. Get Reddit credentials from: https://www.reddit.com/prefs/apps")
        return False
    
    return True

def test_subreddit_finder():
    """Test the subreddit finder agent."""
    try:
        from agents.subreddit_finder import find_subreddits
        print("\n🔎 Testing Subreddit Finder...")
        
        test_topic = "college students"
        subreddits = find_subreddits(test_topic)
        
        print(f"Topic: {test_topic}")
        print(f"Found subreddits: {subreddits}")
        
        if subreddits and len(subreddits) > 0:
            print("✅ Subreddit finder working!")
            return True
        else:
            print("❌ Subreddit finder failed")
            return False
            
    except Exception as e:
        print(f"❌ Subreddit finder error: {str(e)}")
        return False

def test_json_parsing_robustness():
    """Test various JSON parsing scenarios that might fail."""
    print("\n🧪 Testing JSON Parsing Robustness...")
    
    test_cases = [
        # Valid JSON
        ('{"summary": "Test", "pain_score": 5, "mvp_suggestion": "Build app", "problem_category": "tech"}', True),
        
        # JSON with extra text before
        ('Here is the analysis:\n{"summary": "Test", "pain_score": 5, "mvp_suggestion": "Build app", "problem_category": "tech"}', True),
        
        # JSON with extra text after
        ('{"summary": "Test", "pain_score": 5, "mvp_suggestion": "Build app", "problem_category": "tech"}\n\nThis is my analysis.', True),
        
        # JSON with markdown code blocks
        ('```json\n{"summary": "Test", "pain_score": 5, "mvp_suggestion": "Build app", "problem_category": "tech"}\n```', True),
        
        # Malformed JSON - missing quote
        ('{"summary": "Test, "pain_score": 5, "mvp_suggestion": "Build app", "problem_category": "tech"}', False),
        
        # Malformed JSON - trailing comma
        ('{"summary": "Test", "pain_score": 5, "mvp_suggestion": "Build app", "problem_category": "tech",}', False),
        
        # Not JSON at all
        ('This is not JSON. The pain point is about marketing struggles.', False),
        
        # JSON with escaped quotes in values
        ('{"summary": "User says \\"I can\'t afford it\\"", "pain_score": 8, "mvp_suggestion": "Free tier", "problem_category": "finance"}', True),
        
        # JSON with newlines in values
        ('{"summary": "User says:\\nI hate this process", "pain_score": 7, "mvp_suggestion": "Simplify", "problem_category": "ux"}', True),
    ]
    
    def extract_and_parse_json(response_text: str) -> Dict[Any, Any]:
        """Enhanced JSON extraction and parsing with multiple fallback strategies."""
        
        # Strategy 1: Try direct JSON parse
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Look for JSON in code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Extract first complete JSON object
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(response_text):
            if char == '{':
                if start_idx == -1:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    try:
                        json_str = response_text[start_idx:i+1]
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        start_idx = -1
        
        # Strategy 4: Try to fix common JSON errors
        cleaned_text = response_text.strip()
        
        # Remove common prefixes
        prefixes_to_remove = [
            'Here is the analysis:',
            'Analysis:',
            'The pain point analysis:',
            'JSON response:',
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned_text.startswith(prefix):
                cleaned_text = cleaned_text[len(prefix):].strip()
        
        # Remove trailing text after JSON
        if cleaned_text.startswith('{'):
            brace_count = 0
            for i, char in enumerate(cleaned_text):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        cleaned_text = cleaned_text[:i+1]
                        break
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass
        
        # If all strategies fail, raise the original error
        raise json.JSONDecodeError("Could not extract valid JSON", response_text, 0)
    
    # Test each case
    passed = 0
    failed = 0
    
    for i, (test_input, should_succeed) in enumerate(test_cases, 1):
        try:
            result = extract_and_parse_json(test_input)
            if should_succeed:
                print(f"✅ Test {i}: Successfully parsed JSON")
                print(f"   Result: {result}")
                passed += 1
            else:
                print(f"❌ Test {i}: Should have failed but succeeded")
                print(f"   Input: {test_input[:100]}...")
                failed += 1
        except json.JSONDecodeError as e:
            if not should_succeed:
                print(f"✅ Test {i}: Correctly failed to parse invalid JSON")
                passed += 1
            else:
                print(f"❌ Test {i}: Failed to parse valid JSON")
                print(f"   Input: {test_input[:100]}...")
                print(f"   Error: {str(e)}")
                failed += 1
        except Exception as e:
            print(f"❌ Test {i}: Unexpected error: {str(e)}")
            failed += 1
    
    print(f"\nJSON Parsing Tests: {passed} passed, {failed} failed")
    return failed == 0

def test_pain_parser_with_mock_data():
    """Test pain parser with controlled mock data to identify JSON issues."""
    print("\n🧠 Testing Pain Parser with Mock Data...")
    
    # Create mock post data that might cause JSON issues
    mock_posts = [
        {
            'subreddit': 'test',
            'title': 'Quit my job, built a Chrome extension, now have pa...',
            'body': 'I quit my corporate job to build a Chrome extension. After 6 months, I\'m struggling with user acquisition and haven\'t made any money. The extension helps with productivity but I can\'t seem to get traction. I\'m running out of savings and considering going back to a job.',
            'comments': [
                {'body': 'Same here, marketing is so hard', 'score': 15},
                {'body': 'Have you tried posting on Product Hunt?', 'score': 8},
            ],
            'url': 'https://reddit.com/test1',
            'score': 156,
            'num_comments': 45,
            'created_utc': 1234567890,
            'author': 'testuser',
            'upvote_ratio': 0.87,
            'subreddit_subscribers': 100000
        },
        {
            'subreddit': 'test',
            'title': 'How I made $0 in one month with $0 ads...',
            'body': 'This is a story about failure. I launched my SaaS product with zero marketing budget and made exactly zero dollars. Here\'s what went wrong and what I learned about the importance of marketing.',
            'comments': [
                {'body': 'Marketing budget is essential', 'score': 25},
                {'body': 'You need to validate before building', 'score': 12},
            ],
            'url': 'https://reddit.com/test2',
            'score': 89,
            'num_comments': 23,
            'created_utc': 1234567891,
            'author': 'testuser2',
            'upvote_ratio': 0.92,
            'subreddit_subscribers': 100000
        }
    ]
    
    try:
        # Import and test pain parser with limited data to avoid rate limiting
        from agents.pain_parser import get_openai_client
        from openai import OpenAI
        import time
        
        client = get_openai_client()
        model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        
        print(f"Testing with model: {model}")
        
        for i, post in enumerate(mock_posts, 1):
            print(f"\n🔍 Testing post {i}: {post['title'][:50]}...")
            
            # Prepare post content
            post_content = f"Title: {post['title']}\n"
            if post.get('body'):
                post_content += f"Post Body: {post['body']}\n"
            
            comments_text = ""
            for j, comment in enumerate(post.get('comments', [])[:5], 1):
                comments_text += f"Comment {j}: {comment['body']}\n"
            
            if comments_text:
                post_content += f"Top Comments:\n{comments_text}"
            
            # Create the same prompt used in the real parser
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

Respond in JSON format:
{{
    "summary": "Brief description of the main pain point",
    "pain_score": 5,
    "mvp_suggestion": "Potential MVP solution to address this problem",
    "problem_category": "Category of the problem (e.g., productivity, finance, education, etc.)"
}}

Only return valid JSON, no additional text.
"""

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert business analyst who identifies problems and opportunities from social discussions. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=400
                )
                
                response_text = response.choices[0].message.content.strip()
                print(f"   Raw response: {response_text[:200]}...")
                
                # Test JSON parsing
                try:
                    parsed = json.loads(response_text)
                    print(f"   ✅ Successfully parsed JSON")
                    print(f"   Summary: {parsed.get('summary', 'N/A')}")
                    print(f"   Pain Score: {parsed.get('pain_score', 'N/A')}")
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON parsing failed: {str(e)}")
                    print(f"   Full response: {response_text}")
                    
                    # Try enhanced parsing
                    print("   🔧 Trying enhanced JSON extraction...")
                    try:
                        # Use the enhanced parsing logic from our test above
                        enhanced_result = extract_and_parse_json_enhanced(response_text)
                        print(f"   ✅ Enhanced parsing succeeded!")
                        print(f"   Summary: {enhanced_result.get('summary', 'N/A')}")
                    except Exception as enhanced_error:
                        print(f"   ❌ Enhanced parsing also failed: {str(enhanced_error)}")
                
                # Small delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ API call failed: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Pain parser test error: {str(e)}")
        return False

def extract_and_parse_json_enhanced(response_text: str) -> Dict[Any, Any]:
    """Enhanced JSON extraction with comprehensive error handling."""
    
    # Strategy 1: Direct parse
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Find JSON in code blocks
    json_patterns = [
        r'```(?:json)?\s*(\{.*?\})\s*```',
        r'```(\{.*?\})```',
        r'`(\{.*?\})`'
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    
    # Strategy 3: Extract JSON object manually
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
    
    # Strategy 4: Try cleaning common issues
    cleaned = response_text.strip()
    
    # Remove common LLM prefixes
    prefixes = [
        "Here's the analysis:",
        "Here is the analysis:",
        "Analysis:",
        "The JSON response is:",
        "JSON:",
        "Result:",
    ]
    
    for prefix in prefixes:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
    
    # Remove trailing explanations
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
    
    raise json.JSONDecodeError("All parsing strategies failed", response_text, 0)

def main():
    """Run comprehensive tests."""
    print("🧪 Reddit Pain Point Finder - Comprehensive Tests")
    print("=" * 60)
    
    # Test API keys
    if not test_api_keys():
        return
    
    # Test subreddit finder
    if not test_subreddit_finder():
        return
    
    # Test JSON parsing robustness
    if not test_json_parsing_robustness():
        print("⚠️ JSON parsing tests revealed issues")
    
    # Test pain parser with real API calls
    print("\n" + "="*60)
    print("🚨 IMPORTANT: The following test makes real API calls")
    print("This will use your OpenAI credits and may take a moment...")
    user_input = input("Continue with API tests? (y/N): ").strip().lower()
    
    if user_input == 'y':
        if not test_pain_parser_with_mock_data():
            print("⚠️ Pain parser tests revealed issues")
    else:
        print("Skipping API tests.")
    
    print("\n✅ Tests completed! Key findings:")
    print("- If JSON parsing fails, implement the enhanced parsing logic")
    print("- Check if LLM responses include extra text before/after JSON")
    print("- Consider adding retry logic for malformed responses")
    print("\nYou can now run: python main.py")
    
if __name__ == "__main__":
    main() 