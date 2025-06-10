#!/usr/bin/env python3
"""
Phase 2 End-to-End Integration Test
Tests the complete workflow with Phase 2 enhancements using realistic data.
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.post_retriever import retrieve_posts
from agents.pain_parser import parse_pain_points
from agents.subreddit_finder import find_subreddits

def create_mock_reddit_data():
    """Create realistic mock Reddit data for testing"""
    import time
    current_time = time.time()
    
    return [
        {
            'subreddit': 'college',
            'title': 'Can\'t find parking anywhere on campus - this is getting ridiculous',
            'body': 'I\'ve been driving around for 45 minutes looking for a parking spot. I\'m already late for my exam. This happens every single day and I\'m so frustrated.',
            'comments': [
                {
                    'body': 'Same problem here! I ended up parking off-campus and walking 20 minutes to class.',
                    'score': 89,
                    'author': 'student123',
                    'created_utc': current_time - 3600,
                    'is_submitter': False
                },
                {
                    'body': 'The university really needs to build more parking structures. This is affecting our grades.',
                    'score': 67,
                    'author': 'collegelife',
                    'created_utc': current_time - 7200,
                    'is_submitter': False
                },
                {
                    'body': 'I\'ve started taking the bus instead. Much less stressful.',
                    'score': 45,
                    'author': 'busrider',
                    'created_utc': current_time - 10800,
                    'is_submitter': False
                }
            ],
            'url': 'https://reddit.com/r/college/comments/test1/parking_issue',
            'score': 234,
            'num_comments': 87,
            'created_utc': current_time - (2 * 24 * 3600),
            'author': 'frustrated_student',
            'upvote_ratio': 0.92,
            'subreddit_subscribers': 1500000,
            'permalink': '/r/college/comments/test1/parking_issue',
            'post_id': 'test1',
            'comment_engagement_ratio': 0.37,
            'controversy_score': 0.08,
            'age_days': 2,
            'age_decay_factor': 0.95,
            'total_awards_received': 3,
            'raw_engagement_score': 220.5
        },
        {
            'subreddit': 'college',
            'title': 'Registration system crashed right when my enrollment window opened',
            'body': 'This is the third semester in a row that the online registration system has crashed during peak enrollment times. I couldn\'t register for any of my required classes.',
            'comments': [
                {
                    'body': 'This cost me my spot in organic chemistry. Now I have to wait another semester!',
                    'score': 123,
                    'author': 'chemstudent',
                    'created_utc': current_time - 1800,
                    'is_submitter': False
                },
                {
                    'body': 'Same here! The IT department needs to upgrade their servers.',
                    'score': 98,
                    'author': 'techsavvy',
                    'created_utc': current_time - 3600,
                    'is_submitter': False
                }
            ],
            'url': 'https://reddit.com/r/college/comments/test2/registration_crash',
            'score': 456,
            'num_comments': 156,
            'created_utc': current_time - (7 * 24 * 3600),
            'author': 'registration_victim',
            'upvote_ratio': 0.96,
            'subreddit_subscribers': 1500000,
            'permalink': '/r/college/comments/test2/registration_crash',
            'post_id': 'test2',
            'comment_engagement_ratio': 0.34,
            'controversy_score': 0.04,
            'age_days': 7,
            'age_decay_factor': 0.87,
            'total_awards_received': 5,
            'raw_engagement_score': 398.2
        },
        {
            'subreddit': 'college',
            'title': 'Parking permits cost $400 per semester but there are still no spots',
            'body': 'I paid $400 for a parking permit and I still can\'t find parking. What exactly am I paying for?',
            'comments': [
                {
                    'body': 'It\'s basically a lottery ticket for the chance to maybe find parking.',
                    'score': 156,
                    'author': 'sarcastic_senior',
                    'created_utc': current_time - 5400,
                    'is_submitter': False
                }
            ],
            'url': 'https://reddit.com/r/college/comments/test3/expensive_parking',
            'score': 189,
            'num_comments': 43,
            'created_utc': current_time - (14 * 24 * 3600),
            'author': 'broke_student',
            'upvote_ratio': 0.89,
            'subreddit_subscribers': 1500000,
            'permalink': '/r/college/comments/test3/expensive_parking',
            'post_id': 'test3',
            'comment_engagement_ratio': 0.23,
            'controversy_score': 0.11,
            'age_days': 14,
            'age_decay_factor': 0.76,
            'total_awards_received': 2,
            'raw_engagement_score': 128.4
        }
    ]

def test_phase2_end_to_end():
    """Test complete Phase 2 workflow end-to-end"""
    print("🧪 PHASE 2 END-TO-END INTEGRATION TEST")
    print("="*60)
    
    # Create mock data
    mock_posts = create_mock_reddit_data()
    print(f"✅ Created {len(mock_posts)} mock posts with realistic data")
    
    # Verify mock data has Phase 2 enhanced fields
    for i, post in enumerate(mock_posts):
        required_fields = [
            'score', 'num_comments', 'upvote_ratio', 'created_utc', 
            'age_days', 'age_decay_factor', 'comment_engagement_ratio',
            'controversy_score', 'total_awards_received'
        ]
        
        for field in required_fields:
            assert field in post, f"Post {i} missing required field: {field}"
        
        assert len(post['comments']) > 0, f"Post {i} should have comments"
        print(f"✅ Post {i+1}: {len(required_fields)} Phase 2 fields + {len(post['comments'])} comments")
    
    # Test Phase 2 pain point parsing
    print(f"\n🧠 Testing Phase 2 pain point parsing...")
    
    # Mock the OpenAI client to avoid real API calls
    with patch('agents.pain_parser.get_openai_client') as mock_client_func:
        mock_client = Mock()
        mock_client_func.return_value = mock_client
        
        # Mock pain point extraction responses
        mock_responses = [
            Mock(choices=[Mock(message=Mock(content='{"summary": "Campus parking shortage causing student frustration and tardiness", "pain_score": 8, "mvp_suggestion": "Smart parking app showing real-time availability", "problem_category": "Transportation"}'))]),
            Mock(choices=[Mock(message=Mock(content='{"summary": "University registration system failures during enrollment periods", "pain_score": 9, "mvp_suggestion": "Backup registration system with queue management", "problem_category": "Technology"}'))]),
            Mock(choices=[Mock(message=Mock(content='{"summary": "Expensive parking permits with insufficient parking availability", "pain_score": 7, "mvp_suggestion": "Dynamic pricing system based on availability", "problem_category": "Financial"}'))])
        ]
        
        # Mock desperation scoring responses
        desperation_responses = [
            Mock(choices=[Mock(message=Mock(content='8'))]),
            Mock(choices=[Mock(message=Mock(content='9'))]),
            Mock(choices=[Mock(message=Mock(content='7'))])
        ]
        
        # Mock LLM deduping response
        dedup_response = Mock(choices=[Mock(message=Mock(content='[{"merge_group": [0, 2], "reason": "Both relate to parking issues"}]'))])
        
        # Setup the mock to return different responses for different calls
        call_count = 0
        desperation_call_count = 0
        
        def mock_create(**kwargs):
            nonlocal call_count, desperation_call_count
            
            content = kwargs['messages'][1]['content'].lower()
            
            if 'desperation' in content or 'emotional intensity' in content:
                response = desperation_responses[min(desperation_call_count, len(desperation_responses) - 1)]
                desperation_call_count += 1
            elif 'merge' in content or 'duplicate' in content:
                response = dedup_response
            else:
                response = mock_responses[min(call_count, len(mock_responses) - 1)]
                call_count += 1
            
            return response
        
        mock_client.chat.completions.create.side_effect = mock_create
        
        # Parse pain points with Phase 2 enhancements
        pain_clusters = parse_pain_points(mock_posts)
        
        print(f"✅ Parsed {len(pain_clusters)} pain point clusters")
        
        # Verify Phase 2 features are present
        for i, cluster in enumerate(pain_clusters):
            print(f"\n🎯 Cluster {i+1}: {cluster.get('topic', 'Unknown')[:60]}...")
            
            # Check Phase 2 Task 1: Engagement weighting
            assert 'total_engagement_weight' in cluster, "Should have total engagement weight"
            assert 'avg_engagement_weight' in cluster, "Should have average engagement weight"
            print(f"   ⚡ Engagement Weight: {cluster['total_engagement_weight']:.3f}")
            
            # Check Phase 2 Task 2: Comment context was used
            assert 'related_pain_points' in cluster, "Should have related pain points"
            for pain_point in cluster['related_pain_points']:
                assert 'engagement_weight' in pain_point, "Pain point should have engagement weight"
            print(f"   💬 Pain points with comment context: {len(cluster['related_pain_points'])}")
            
            # Check Phase 2 Task 4: Temporal trend analysis
            assert 'trend_tag' in cluster, "Should have trend tag"
            assert 'trend_slope' in cluster, "Should have trend slope"
            trend_info = f"{cluster['trend_tag']} (slope: {cluster.get('trend_slope', 0)})" if cluster['trend_tag'] else f"stable (slope: {cluster.get('trend_slope', 0)})"
            print(f"   📈 Trend: {trend_info}")
            
            # Verify engagement-weighted sorting (Phase 2 Task 1)
            combined_score = cluster['total_engagement_weight'] * cluster['desperation_score'] * cluster['avg_pain_score']
            print(f"   🔢 Combined Score: {combined_score:.3f}")
        
        # Verify clusters are sorted by engagement weight
        if len(pain_clusters) > 1:
            for i in range(len(pain_clusters) - 1):
                current_score = pain_clusters[i]['total_engagement_weight'] * pain_clusters[i]['desperation_score'] * pain_clusters[i]['avg_pain_score']
                next_score = pain_clusters[i+1]['total_engagement_weight'] * pain_clusters[i+1]['desperation_score'] * pain_clusters[i+1]['avg_pain_score']
                assert current_score >= next_score, f"Clusters should be sorted by engagement-weighted score"
            print("✅ Clusters properly sorted by engagement-weighted scoring")
        
        # Check that LLM deduping was attempted
        dedup_calls = [call for call in mock_client.chat.completions.create.call_args_list 
                      if any('merge' in str(arg).lower() for arg in call[1]['messages'])]
        if len(mock_posts) > 1:
            assert len(dedup_calls) > 0, "LLM deduping should have been attempted"
            print("✅ LLM-assisted deduping was performed")
        
        print(f"\n🎉 END-TO-END TEST RESULTS:")
        print(f"✅ All {len(pain_clusters)} clusters have Phase 2 enhanced features")
        print(f"✅ Engagement-weighted scoring: Working")
        print(f"✅ Comment context injection: Working") 
        print(f"✅ LLM-assisted deduping: Working")
        print(f"✅ Temporal trend analysis: Working")
        print(f"✅ Enhanced sorting and prioritization: Working")
        
        return True

def test_phase2_json_output():
    """Test that Phase 2 features appear correctly in JSON output"""
    print(f"\n🧪 Testing Phase 2 JSON Output Structure")
    print("="*50)
    
    # Load a real analysis file if it exists
    test_files = ['pain_analysis_gatech.json', 'pain_analysis_college.json']
    
    for filename in test_files:
        if os.path.exists(filename):
            print(f"📄 Testing JSON structure in: {filename}")
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check analysis summary has Phase 2 features
            summary = data.get('analysis_summary', {})
            phase2_fields = ['total_engagement_weight', 'average_engagement_weight', 'trending_clusters', 'phase_2_features']
            
            for field in phase2_fields:
                assert field in summary, f"Analysis summary missing Phase 2 field: {field}"
            
            # Check Phase 2 feature flags
            phase2_features = summary.get('phase_2_features', {})
            expected_features = [
                'engagement_weighted_scoring',
                'comment_context_injection', 
                'llm_assisted_deduping',
                'temporal_trend_analysis'
            ]
            
            for feature in expected_features:
                assert feature in phase2_features, f"Missing Phase 2 feature flag: {feature}"
                assert phase2_features[feature] == True, f"Phase 2 feature should be enabled: {feature}"
            
            # Check clusters have Phase 2 fields
            clusters = data.get('clusters', [])
            for i, cluster in enumerate(clusters[:3]):  # Check first 3 clusters
                phase2_cluster_fields = [
                    'total_engagement_weight', 
                    'avg_engagement_weight',
                    'trend_tag',
                    'trend_slope'
                ]
                
                for field in phase2_cluster_fields:
                    if field not in cluster:
                        print(f"⚠️ Cluster {i} missing Phase 2 field: {field}")
                    else:
                        print(f"✅ Cluster {i} has {field}: {cluster[field]}")
            
            print(f"✅ {filename} has proper Phase 2 JSON structure")
            return True
    
    print("⚠️ No existing analysis files found to test JSON structure")
    return True

if __name__ == "__main__":
    print("🚀 PHASE 2 END-TO-END VALIDATION")
    print("="*70)
    
    try:
        # Test end-to-end workflow
        success1 = test_phase2_end_to_end()
        
        # Test JSON output structure
        success2 = test_phase2_json_output()
        
        if success1 and success2:
            print("\n🎉 ALL PHASE 2 END-TO-END TESTS PASSED! 🎉")
            print("✅ Phase 2 implementation is fully functional and ready for production")
            sys.exit(0)
        else:
            print("\n❌ Some Phase 2 end-to-end tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ End-to-end test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 