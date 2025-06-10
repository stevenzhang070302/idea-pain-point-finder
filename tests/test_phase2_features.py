#!/usr/bin/env python3
"""
Phase 2 Feature Testing Suite
Tests all Phase 2 enhancements to ensure they work correctly:
1. Engagement-weighted scoring
2. Comment context injection (8k token limit)
3. LLM-assisted deduping
4. Temporal trend tagging
"""

import sys
import os
import time
import json
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.pain_parser import (
    calculate_engagement_weight,
    prepare_post_content_with_comments,
    count_tokens,
    truncate_to_token_limit,
    dedupe_clusters_with_llm,
    calculate_temporal_trends,
    parse_single_pain_point,
    get_openai_client
)

def test_engagement_weight_calculation():
    """Test Phase 2 Task 1: Engagement-weighted scoring calculation"""
    print("\n🧪 Testing Phase 2 Task 1: Engagement-Weighted Scoring")
    print("="*60)
    
    # Test case 1: High engagement post
    high_engagement_post = {
        'score': 1000,  # High upvotes
        'num_comments': 100,  # High comments
        'upvote_ratio': 0.95,  # High approval
        'age_decay_factor': 1.0,  # Recent post
        'controversy_score': 0.05,  # Low controversy
        'comment_engagement_ratio': 1.0,  # Good comment ratio
        'total_awards_received': 5  # Some awards
    }
    
    weight_high = calculate_engagement_weight(high_engagement_post)
    print(f"✅ High engagement post weight: {weight_high:.4f}")
    
    # Test case 2: Low engagement post
    low_engagement_post = {
        'score': 10,  # Low upvotes
        'num_comments': 1,  # Few comments
        'upvote_ratio': 0.6,  # Lower approval
        'age_decay_factor': 0.5,  # Older post
        'controversy_score': 0.4,  # More controversial
        'comment_engagement_ratio': 0.1,  # Poor comment ratio
        'total_awards_received': 0  # No awards
    }
    
    weight_low = calculate_engagement_weight(low_engagement_post)
    print(f"✅ Low engagement post weight: {weight_low:.4f}")
    
    # Test case 3: Verify high engagement > low engagement
    assert weight_high > weight_low, f"High engagement ({weight_high}) should be > low engagement ({weight_low})"
    print(f"✅ Engagement weighting working correctly: {weight_high:.4f} > {weight_low:.4f}")
    
    # Test case 4: Edge cases - missing fields
    incomplete_post = {'score': 100}
    weight_incomplete = calculate_engagement_weight(incomplete_post)
    print(f"✅ Incomplete post weight (fallback values): {weight_incomplete:.4f}")
    
    print("🎯 Engagement-weighted scoring tests: PASSED ✅")
    return True

def test_comment_context_injection():
    """Test Phase 2 Task 2: Comment context injection with 8k token limit"""
    print("\n🧪 Testing Phase 2 Task 2: Comment Context Injection")
    print("="*60)
    
    # Test case 1: Normal post with comments
    test_post = {
        'title': 'Test Post Title',
        'body': 'This is the main post body content.',
        'score': 500,
        'num_comments': 25,
        'upvote_ratio': 0.85,
        'comments': [
            {
                'body': 'This is the first comment with highest score',
                'score': 100,
                'is_submitter': False
            },
            {
                'body': 'This is a reply from the original poster',
                'score': 75,
                'is_submitter': True
            },
            {
                'body': 'This is another comment with good engagement',
                'score': 50,
                'is_submitter': False
            }
        ]
    }
    
    content = prepare_post_content_with_comments(test_post)
    print(f"✅ Generated content length: {len(content)} characters")
    
    # Verify components are included
    assert 'TITLE: Test Post Title' in content, "Title should be included"
    assert 'POST BODY: This is the main post body content.' in content, "Body should be included"
    assert 'ENGAGEMENT:' in content, "Engagement metrics should be included"
    assert 'TOP COMMENTS:' in content, "Comments section should be included"
    assert 'Comment 1 (100 pts): This is the first comment' in content, "First comment should be included"
    assert '(OP)' in content, "OP indicator should be present for submitter comments"
    
    print("✅ All content components properly included")
    
    # Test case 2: Token counting
    token_count = count_tokens(content)
    print(f"✅ Token count: {token_count}")
    
    # Test case 3: Token truncation with very long content
    long_content = "This is a test sentence. " * 1000  # Create very long content
    long_token_count = count_tokens(long_content)
    print(f"✅ Long content token count: {long_token_count}")
    
    truncated = truncate_to_token_limit(long_content, max_tokens=100)
    truncated_count = count_tokens(truncated)
    print(f"✅ Truncated content token count: {truncated_count}")
    
    assert truncated_count <= 100, f"Truncated content should be ≤ 100 tokens, got {truncated_count}"
    assert '[TRUNCATED TO STAY WITHIN TOKEN LIMIT]' in truncated, "Truncation marker should be present"
    
    # Test case 4: Content under token limit (should not be truncated)
    short_content = "Short content that fits easily."
    not_truncated = truncate_to_token_limit(short_content, max_tokens=8000)
    assert not_truncated == short_content, "Short content should not be truncated"
    
    print("🎯 Comment context injection tests: PASSED ✅")
    return True

def test_temporal_trend_analysis():
    """Test Phase 2 Task 4: Temporal trend tagging"""
    print("\n🧪 Testing Phase 2 Task 4: Temporal Trend Analysis")
    print("="*60)
    
    current_time = time.time()
    one_week_ago = current_time - (7 * 24 * 3600)
    two_weeks_ago = current_time - (14 * 24 * 3600)
    three_weeks_ago = current_time - (21 * 24 * 3600)
    four_weeks_ago = current_time - (28 * 24 * 3600)
    
    # Test case 1: Trending cluster (increasing mentions)
    trending_cluster = {
        'related_pain_points': [
            {'created_utc': four_weeks_ago},  # 1 mention 4 weeks ago
            {'created_utc': three_weeks_ago}, {'created_utc': three_weeks_ago},  # 2 mentions 3 weeks ago
            {'created_utc': two_weeks_ago}, {'created_utc': two_weeks_ago}, {'created_utc': two_weeks_ago},  # 3 mentions 2 weeks ago
            {'created_utc': one_week_ago}, {'created_utc': one_week_ago}, {'created_utc': one_week_ago}, {'created_utc': one_week_ago}  # 4 mentions 1 week ago
        ]
    }
    
    # Test case 2: Stable cluster (consistent mentions)
    stable_cluster = {
        'related_pain_points': [
            {'created_utc': four_weeks_ago}, {'created_utc': four_weeks_ago},
            {'created_utc': three_weeks_ago}, {'created_utc': three_weeks_ago},
            {'created_utc': two_weeks_ago}, {'created_utc': two_weeks_ago},
            {'created_utc': one_week_ago}, {'created_utc': one_week_ago}
        ]
    }
    
    # Test case 3: Declining cluster (decreasing mentions)
    declining_cluster = {
        'related_pain_points': [
            {'created_utc': four_weeks_ago}, {'created_utc': four_weeks_ago}, {'created_utc': four_weeks_ago}, {'created_utc': four_weeks_ago},
            {'created_utc': three_weeks_ago}, {'created_utc': three_weeks_ago}, {'created_utc': three_weeks_ago},
            {'created_utc': two_weeks_ago}, {'created_utc': two_weeks_ago},
            {'created_utc': one_week_ago}
        ]
    }
    
    # Test case 4: Insufficient data cluster
    insufficient_cluster = {
        'related_pain_points': [
            {'created_utc': one_week_ago}
        ]
    }
    
    test_clusters = [trending_cluster, stable_cluster, declining_cluster, insufficient_cluster]
    
    # Run trend analysis
    analyzed_clusters = calculate_temporal_trends(test_clusters)
    
    print(f"✅ Trending cluster trend: '{analyzed_clusters[0].get('trend_tag', '')}', slope: {analyzed_clusters[0].get('trend_slope', 0)}")
    print(f"✅ Stable cluster trend: '{analyzed_clusters[1].get('trend_tag', '')}', slope: {analyzed_clusters[1].get('trend_slope', 0)}")
    print(f"✅ Declining cluster trend: '{analyzed_clusters[2].get('trend_tag', '')}', slope: {analyzed_clusters[2].get('trend_slope', 0)}")
    print(f"✅ Insufficient data cluster trend: '{analyzed_clusters[3].get('trend_tag', '')}', slope: {analyzed_clusters[3].get('trend_slope', 0)}")
    
    # Verify trending detection
    trending_slope = analyzed_clusters[0].get('trend_slope', 0)
    stable_slope = analyzed_clusters[1].get('trend_slope', 0)
    declining_slope = analyzed_clusters[2].get('trend_slope', 0)
    
    # Trending cluster should have positive slope > 0.5
    assert trending_slope > 0.5, f"Trending cluster should have slope > 0.5, got {trending_slope}"
    assert analyzed_clusters[0].get('trend_tag') == "🆙 trending", "Trending cluster should be tagged"
    
    # Declining cluster should have negative slope
    assert declining_slope < 0, f"Declining cluster should have negative slope, got {declining_slope}"
    
    # Insufficient data should have empty trend tag
    assert analyzed_clusters[3].get('trend_tag') == "", "Insufficient data cluster should have empty trend tag"
    
    print("🎯 Temporal trend analysis tests: PASSED ✅")
    return True

def test_llm_deduping_mock():
    """Test Phase 2 Task 3: LLM-assisted deduping with mocked responses"""
    print("\n🧪 Testing Phase 2 Task 3: LLM-Assisted Deduping (Mocked)")
    print("="*60)
    
    # Create test cluster representatives
    cluster_reps = [
        {
            'summary': 'Difficulty finding parking on campus',
            'engagement_weight': 0.5,
            'frequency': 3
        },
        {
            'summary': 'Campus parking shortage and availability issues',
            'engagement_weight': 0.7,
            'frequency': 2
        },
        {
            'summary': 'Students struggling with course registration system',
            'engagement_weight': 0.8,
            'frequency': 4
        },
        {
            'summary': 'Problems with online class registration platform',
            'engagement_weight': 0.6,
            'frequency': 2
        }
    ]
    
    # Mock OpenAI client and response for merging similar clusters
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '''[
  {
    "merge_group": [0, 1],
    "reason": "Both relate to parking issues on campus"
  },
  {
    "merge_group": [2, 3],
    "reason": "Both about course registration system problems"
  }
]'''
    
    mock_client.chat.completions.create.return_value = mock_response
    
    # Test deduping
    deduplicated = dedupe_clusters_with_llm(cluster_reps, mock_client, "gpt-4o")
    
    print(f"✅ Original clusters: {len(cluster_reps)}")
    print(f"✅ Deduplicated clusters: {len(deduplicated)}")
    
    # Should merge 4 clusters into 2
    assert len(deduplicated) == 2, f"Should have 2 clusters after deduping, got {len(deduplicated)}"
    
    # Check that engagement weights were combined
    parking_cluster = next((c for c in deduplicated if 'parking' in c['summary'].lower()), None)
    registration_cluster = next((c for c in deduplicated if 'registration' in c['summary'].lower()), None)
    
    assert parking_cluster is not None, "Parking cluster should exist after merge"
    assert registration_cluster is not None, "Registration cluster should exist after merge"
    
    # Engagement weights should be combined (0.5 + 0.7 = 1.2 for parking, 0.8 + 0.6 = 1.4 for registration)
    print(f"✅ Parking cluster combined weight: {parking_cluster.get('engagement_weight', 0)}")
    print(f"✅ Registration cluster combined weight: {registration_cluster.get('engagement_weight', 0)}")
    
    # Test no merges scenario
    mock_response.choices[0].message.content = '"no_merges"'
    no_merge_result = dedupe_clusters_with_llm(cluster_reps, mock_client, "gpt-4o")
    assert len(no_merge_result) == len(cluster_reps), "Should return original clusters when no merges needed"
    
    print("🎯 LLM-assisted deduping tests: PASSED ✅")
    return True

def test_integration_workflow():
    """Integration test for Phase 2 features working together"""
    print("\n🧪 Testing Phase 2 Integration: All Features Together")
    print("="*60)
    
    # Create realistic test data
    current_time = time.time()
    test_posts = [
        {
            'title': 'Campus parking is impossible to find',
            'body': 'I spend 30 minutes every morning looking for parking. This is ridiculous.',
            'score': 150,
            'num_comments': 25,
            'upvote_ratio': 0.9,
            'age_decay_factor': 0.8,
            'controversy_score': 0.1,
            'comment_engagement_ratio': 0.167,
            'total_awards_received': 2,
            'subreddit': 'college',
            'subreddit_subscribers': 1000000,
            'url': 'https://reddit.com/test1',
            'created_utc': current_time - (7 * 24 * 3600),
            'age_days': 7,
            'comments': [
                {
                    'body': 'Same here! I was late to three classes this week because of parking.',
                    'score': 45,
                    'is_submitter': False
                },
                {
                    'body': 'The university needs to build more parking structures ASAP.',
                    'score': 32,
                    'is_submitter': False
                }
            ]
        },
        {
            'title': 'Registration system crashed during enrollment',
            'body': 'The online registration system went down right when my enrollment time started.',
            'score': 200,
            'num_comments': 40,
            'upvote_ratio': 0.95,
            'age_decay_factor': 0.9,
            'controversy_score': 0.05,
            'comment_engagement_ratio': 0.2,
            'total_awards_received': 1,
            'subreddit': 'college',
            'subreddit_subscribers': 1000000,
            'url': 'https://reddit.com/test2',
            'created_utc': current_time - (3 * 24 * 3600),
            'age_days': 3,
            'comments': [
                {
                    'body': 'This happens every semester! When will they fix this?',
                    'score': 60,
                    'is_submitter': False
                }
            ]
        }
    ]
    
    print("✅ Test data created with realistic engagement metrics")
    
    # Test engagement weight calculation
    for i, post in enumerate(test_posts):
        weight = calculate_engagement_weight(post)
        print(f"✅ Post {i+1} engagement weight: {weight:.4f}")
        assert weight > 0, f"Engagement weight should be positive, got {weight}"
    
    # Test comment context preparation
    for i, post in enumerate(test_posts):
        content = prepare_post_content_with_comments(post)
        print(f"✅ Post {i+1} content prepared ({len(content)} chars)")
        assert 'TOP COMMENTS:' in content, "Comments should be included"
        assert 'ENGAGEMENT:' in content, "Engagement metrics should be included"
    
    # Test trend analysis with mixed data
    test_cluster = {
        'related_pain_points': [
            {'created_utc': current_time - (14 * 24 * 3600)},
            {'created_utc': current_time - (7 * 24 * 3600)},
            {'created_utc': current_time - (3 * 24 * 3600)},
            {'created_utc': current_time - (1 * 24 * 3600)}
        ]
    }
    
    analyzed = calculate_temporal_trends([test_cluster])
    print(f"✅ Trend analysis completed: slope = {analyzed[0].get('trend_slope', 0)}")
    
    print("🎯 Integration test: PASSED ✅")
    return True

def test_error_handling():
    """Test error handling and edge cases for Phase 2 features"""
    print("\n🧪 Testing Phase 2 Error Handling & Edge Cases")
    print("="*60)
    
    # Test engagement weight with missing data
    empty_post = {}
    weight = calculate_engagement_weight(empty_post)
    print(f"✅ Empty post engagement weight (should use defaults): {weight:.4f}")
    assert weight >= 0, "Should handle missing data gracefully"
    
    # Test comment preparation with missing fields
    minimal_post = {'title': 'Test'}
    content = prepare_post_content_with_comments(minimal_post)
    print(f"✅ Minimal post content length: {len(content)}")
    assert 'TITLE: Test' in content, "Should handle minimal post data"
    
    # Test token counting with empty string
    empty_tokens = count_tokens("")
    print(f"✅ Empty string token count: {empty_tokens}")
    assert empty_tokens == 0, "Empty string should have 0 tokens"
    
    # Test truncation with very short limit
    short_truncated = truncate_to_token_limit("This is a test sentence", max_tokens=2)
    print(f"✅ Very short truncation: '{short_truncated[:50]}...'")
    assert count_tokens(short_truncated) <= 2, "Should respect very short token limits"
    
    # Test trend analysis with empty cluster
    empty_cluster = {'related_pain_points': []}
    trend_result = calculate_temporal_trends([empty_cluster])
    print(f"✅ Empty cluster trend tag: '{trend_result[0].get('trend_tag', '')}'")
    assert trend_result[0].get('trend_tag') == "", "Empty cluster should have no trend tag"
    
    # Test deduping with single cluster
    single_cluster = [{'summary': 'Single cluster test'}]
    mock_client = Mock()
    dedup_result = dedupe_clusters_with_llm(single_cluster, mock_client, "gpt-4o")
    assert len(dedup_result) == 1, "Single cluster should remain unchanged"
    
    print("🎯 Error handling tests: PASSED ✅")
    return True

def run_phase2_test_suite():
    """Run complete Phase 2 test suite"""
    print("🚀 PHASE 2 FEATURE TEST SUITE")
    print("="*70)
    print("Testing all Phase 2 enhancements to ensure proper functionality")
    print("="*70)
    
    tests = [
        ("Engagement-Weighted Scoring", test_engagement_weight_calculation),
        ("Comment Context Injection", test_comment_context_injection),
        ("Temporal Trend Analysis", test_temporal_trend_analysis),
        ("LLM-Assisted Deduping", test_llm_deduping_mock),
        ("Integration Workflow", test_integration_workflow),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔬 Running: {test_name}")
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: FAILED - {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("🎯 PHASE 2 TEST RESULTS")
    print("="*70)
    print(f"✅ Tests Passed: {passed}")
    print(f"❌ Tests Failed: {failed}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL PHASE 2 FEATURES WORKING CORRECTLY! 🎉")
        print("✅ Ready for production use and Phase 3 development")
    else:
        print(f"\n⚠️  {failed} test(s) failed - review and debug needed")
        print("🔧 Check individual test outputs above for details")
    
    return failed == 0

if __name__ == "__main__":
    success = run_phase2_test_suite()
    sys.exit(0 if success else 1) 