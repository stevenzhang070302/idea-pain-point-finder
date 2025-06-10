import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any
from agents.subreddit_finder import find_subreddits
from agents.post_retriever import retrieve_posts
from agents.pain_parser import parse_pain_points
import json

load_dotenv()

class State(TypedDict):
    """State object for the LangGraph workflow."""
    topic: str
    subreddits: List[str]
    posts: List[Dict[str, Any]]
    pain_clusters: List[Dict[str, Any]]  # Updated to handle clusters
    final_output: Dict[str, Any]

def start_node(state: State) -> State:
    """Starting node that validates input."""
    print(f"🚀 Starting pain point analysis for topic: {state['topic']}")
    return state

def find_subreddits_node(state: State) -> State:
    """Node to find relevant subreddits for the topic."""
    print(f"🔎 Finding subreddits for: {state['topic']}")
    subreddits = find_subreddits(state['topic'])
    state['subreddits'] = subreddits
    print(f"📍 Found subreddits: {subreddits}")
    return state

def retrieve_posts_node(state: State) -> State:
    """Node to retrieve posts from subreddits."""
    print("📄 Retrieving posts from subreddits...")
    posts = retrieve_posts(state['subreddits'])
    state['posts'] = posts
    print(f"📊 Retrieved {len(posts)} posts total")
    return state

def parse_pain_node(state: State) -> State:
    """Node to parse and cluster pain points from posts."""
    print("🧠 Analyzing posts for pain points...")
    pain_clusters = parse_pain_points(state['posts'])
    state['pain_clusters'] = pain_clusters
    print(f"⚠️ Identified {len(pain_clusters)} pain point clusters")
    return state

def output_node(state: State) -> State:
    """Final output node that formats results and emits enhanced JSON with Phase 2 features."""
    print("📊 Generating final output with Phase 2 enhancements...")
    
    # Calculate summary statistics
    total_clusters = len(state['pain_clusters'])
    if total_clusters == 0:
        print("\n❌ No significant pain points identified. Try a different topic or check subreddit activity.")
        state['final_output'] = {
            'topic': state['topic'],
            'clusters': [],
            'summary': {'total_clusters': 0}
        }
        return state
    
    total_pain_points = sum(cluster['frequency'] for cluster in state['pain_clusters'])
    avg_desperation = sum(cluster['desperation_score'] for cluster in state['pain_clusters']) / total_clusters
    avg_pain_score = sum(cluster['avg_pain_score'] for cluster in state['pain_clusters']) / total_clusters
    high_priority_clusters = [c for c in state['pain_clusters'] if c['desperation_score'] >= 7]
    
    # Phase 2: Enhanced statistics
    total_engagement_weight = sum(cluster.get('total_engagement_weight', 0) for cluster in state['pain_clusters'])
    trending_clusters = [c for c in state['pain_clusters'] if c.get('trend_tag', '').startswith('🆙')]
    avg_engagement_weight = sum(cluster.get('avg_engagement_weight', 0) for cluster in state['pain_clusters']) / total_clusters
    
    # Enhanced JSON output (Task 15) with Phase 2 features
    enhanced_output = {
        'topic': state['topic'],
        'analysis_summary': {
            'total_subreddits': len(state['subreddits']),
            'total_posts': len(state['posts']),
            'total_clusters': total_clusters,
            'total_pain_points': total_pain_points,
            'average_desperation_score': round(avg_desperation, 1),
            'average_pain_score': round(avg_pain_score, 1),
            'high_priority_clusters': len(high_priority_clusters),
            # Phase 2 enhanced metrics
            'total_engagement_weight': round(total_engagement_weight, 2),
            'average_engagement_weight': round(avg_engagement_weight, 2),
            'trending_clusters': len(trending_clusters),
            'phase_2_features': {
                'engagement_weighted_scoring': True,
                'comment_context_injection': True,
                'llm_assisted_deduping': True,
                'temporal_trend_analysis': True
            }
        },
        'clusters': state['pain_clusters'],
        'subreddits_analyzed': state['subreddits']
    }
    
    state['final_output'] = enhanced_output
    
    # Print formatted output for humans with Phase 2 enhancements
    print("\n" + "="*70)
    print(f"🎯 ENHANCED PAIN POINT ANALYSIS (PHASE 2): {state['topic'].upper()}")
    print("="*70)
    print(f"📊 Summary: {total_clusters} clusters found across {len(state['subreddits'])} subreddits")
    print(f"📈 Total Pain Points: {total_pain_points}")
    print(f"🔥 Average Desperation Score: {avg_desperation:.1f}/10")
    print(f"📊 Average Pain Score: {avg_pain_score:.1f}/10")
    print(f"🚨 High Priority Clusters (7+ desperation): {len(high_priority_clusters)}")
    print(f"⚡ Total Engagement Weight: {total_engagement_weight:.2f}")
    print(f"📈 Trending Clusters: {len(trending_clusters)}")
    
    # Show top clusters with Phase 2 metrics
    print(f"\n🔥 TOP PAIN POINT CLUSTERS (by engagement-weighted priority):")
    print("-" * 50)
    
    for i, cluster in enumerate(state['pain_clusters'][:5], 1):  # Top 5 clusters
        desperation = cluster['desperation_score']
        frequency = cluster['frequency']
        avg_pain = cluster['avg_pain_score']
        market_data = cluster['market_proxy']
        engagement_weight = cluster.get('total_engagement_weight', 0)
        trend_tag = cluster.get('trend_tag', '')
        
        print(f"\n{i}. 🎯 Cluster: {cluster['cluster_id']} {trend_tag}")
        print(f"   📝 Problem: {cluster['topic']}")
        print(f"   🔥 Desperation Score: {desperation}/10 | Pain Score: {avg_pain}/10")
        print(f"   📊 Frequency: {frequency} posts | Avg Upvotes: {cluster['avg_upvotes']}")
        print(f"   ⚡ Engagement Weight: {engagement_weight:.2f} | Avg Weight: {cluster.get('avg_engagement_weight', 0):.2f}")
        if cluster.get('trend_slope') is not None:
            print(f"   📈 Trend Slope: {cluster.get('trend_slope', 0):.2f} posts/week")
        print(f"   📍 Subreddits: {', '.join(cluster['all_subreddits'])}")
        print(f"   👥 Market: {market_data['subscribers']:,} subscribers, ~{market_data['posts_per_week']} posts/week")
        print(f"   💡 MVP Opportunity: {cluster['mvp_suggestion']}")
        print(f"   🔗 Sample: {cluster['sample_post']['title'][:80]}...")
        print(f"      📎 {cluster['sample_post']['url']}")
    
    # Show detailed breakdown with Phase 2 features
    print(f"\n📊 DETAILED CLUSTER BREAKDOWN (Phase 2 Enhanced):")
    print("-" * 50)
    
    for cluster in state['pain_clusters']:
        trend_indicator = f" {cluster.get('trend_tag', '')}" if cluster.get('trend_tag') else ""
        print(f"\n🎯 {cluster['cluster_id']}{trend_indicator} - {cluster['topic']}")
        print(f"   Category: {cluster['problem_category']} | Frequency: {cluster['frequency']}")
        print(f"   Engagement Weight: {cluster.get('total_engagement_weight', 0):.2f}")
        print(f"   Related Pain Points (with engagement weights):")
        for pain in cluster['related_pain_points'][:3]:  # Show top 3 related
            weight = pain.get('engagement_weight', 0)
            print(f"     • [{pain['pain_score']}/10, W:{weight:.2f}] r/{pain['subreddit']}: {pain['summary'][:80]}...")
    
    # Save enhanced JSON output to file
    try:
        output_filename = f"pain_analysis_{state['topic'].replace(' ', '_')}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(enhanced_output, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Enhanced JSON output saved to: {output_filename}")
    except Exception as e:
        print(f"\n⚠️ Could not save JSON file: {str(e)}")
    
    # Print JSON to console as well (Task 15)
    print(f"\n📋 PHASE 2 ENHANCED JSON OUTPUT:")
    print("-" * 50)
    print(json.dumps(state['pain_clusters'], indent=2))
    
    print(f"\n💡 PHASE 2 ANALYSIS COMPLETE - NEXT STEPS:")
    print("🔥 PRIORITIZATION (Phase 2 Enhanced):")
    print("- Focus on clusters with high engagement weights AND high desperation scores")
    print("- Pay special attention to trending clusters (🆙) for immediate opportunities")
    print("- Clusters with controversy scores may indicate unsolved problems")
    print("- Consider the age decay factor when evaluating urgency")
    
    print(f"\n⚡ ENGAGEMENT INSIGHTS:")
    print("- Higher engagement weights indicate more passionate communities")
    print("- Comment-to-upvote ratios reveal discussion intensity")
    print("- Awards and high upvote ratios signal community consensus")
    
    print(f"\n📈 TRENDING ANALYSIS:")
    trending_count = len(trending_clusters)
    if trending_count > 0:
        print(f"- {trending_count} clusters are trending upward")
        print("- These represent emerging pain points with growing demand")
        print("- Consider building MVPs for trending problems first")
    else:
        print("- No strongly trending clusters identified")
        print("- Focus on high engagement weight clusters for stable demand")
    
    print(f"\n📊 VALIDATION RECOMMENDATIONS:")
    print("- Research existing solutions for high-engagement problems")
    print("- Engage with these communities to validate assumptions")
    print("- Build MVPs for clusters with high engagement + trending status")
    print("- Use the enhanced JSON data for programmatic analysis")
    print("- Consider temporal patterns when timing product launches")
    
    return state

def create_workflow():
    """Create and configure the LangGraph workflow."""
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("start", start_node)
    workflow.add_node("find_subreddits", find_subreddits_node)
    workflow.add_node("retrieve_posts", retrieve_posts_node)
    workflow.add_node("parse_pain", parse_pain_node)
    workflow.add_node("output", output_node)
    
    # Add edges
    workflow.add_edge(START, "start")
    workflow.add_edge("start", "find_subreddits")
    workflow.add_edge("find_subreddits", "retrieve_posts")
    workflow.add_edge("retrieve_posts", "parse_pain")
    workflow.add_edge("parse_pain", "output")
    workflow.add_edge("output", END)
    
    return workflow.compile()

def main():
    """Main function to run the enhanced pain point finder."""
    print("🎯 Enhanced Reddit Pain Point Finder")
    print("=" * 45)
    
    # Get topic from user
    topic = input("Enter a topic/niche to analyze: ").strip()
    
    if not topic:
        print("❌ Please enter a valid topic.")
        return
    
    # Create and run workflow
    app = create_workflow()
    
    initial_state = {
        'topic': topic,
        'subreddits': [],
        'posts': [],
        'pain_clusters': [],  # Updated to handle clusters
        'final_output': {}
    }
    
    try:
        result = app.invoke(initial_state)
        print("\n✅ Enhanced analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        print("Please check your API keys and try again.")

if __name__ == "__main__":
    main() 