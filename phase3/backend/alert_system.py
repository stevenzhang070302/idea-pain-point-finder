#!/usr/bin/env python3
"""
Alert system for Reddit Pain Finder - Phase 3
Sends weekly/daily digests of high-desperation pain point clusters
"""

import os
import sys
import sqlite3
import json
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from main import create_workflow, State

DATABASE_PATH = "../database/painpoints.db"

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DATABASE_PATH)

def get_pending_alerts():
    """Get alert subscriptions that need to be processed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get alerts that haven't been sent in their frequency period
    cursor.execute('''
        SELECT a.id, a.user_id, a.search_id, s.topic, s.keywords, 
               a.email, a.slack_webhook, a.frequency, a.min_desperation_score,
               s.last_run
        FROM alert_subscriptions a
        JOIN saved_searches s ON a.search_id = s.id
        WHERE s.is_active = TRUE
        AND (
            (a.frequency = 'daily' AND (s.last_run IS NULL OR s.last_run < DATE('now', '-1 day')))
            OR 
            (a.frequency = 'weekly' AND (s.last_run IS NULL OR s.last_run < DATE('now', '-7 days')))
        )
    ''')
    
    alerts = cursor.fetchall()
    conn.close()
    
    return [
        {
            "alert_id": alert[0],
            "user_id": alert[1],
            "search_id": alert[2],
            "topic": alert[3],
            "keywords": alert[4],
            "email": alert[5],
            "slack_webhook": alert[6],
            "frequency": alert[7],
            "min_desperation_score": alert[8],
            "last_run": alert[9]
        }
        for alert in alerts
    ]

async def run_analysis_for_alert(topic: str):
    """Run pain analysis for an alert topic."""
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
        return result['final_output']
        
    except Exception as e:
        print(f"❌ Error running analysis for {topic}: {str(e)}")
        return None

def filter_high_priority_clusters(clusters: List[Dict], min_desperation: int) -> List[Dict]:
    """Filter clusters by minimum desperation score and other criteria."""
    return [
        cluster for cluster in clusters
        if (
            cluster.get('desperation_score', 0) >= min_desperation
            or cluster.get('trend_tag', '').startswith('🆙')  # Include trending
            or cluster.get('total_engagement_weight', 0) > 50  # High engagement
        )
    ]

def format_email_content(topic: str, clusters: List[Dict], analysis_summary: Dict) -> str:
    """Format email content for pain point digest."""
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .cluster {{ border: 1px solid #dee2e6; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .high-priority {{ border-left: 4px solid #dc3545; }}
            .trending {{ border-left: 4px solid #28a745; }}
            .metric {{ display: inline-block; margin-right: 20px; }}
            .score {{ font-weight: bold; color: #dc3545; }}
            .engagement {{ font-weight: bold; color: #007bff; }}
            .url {{ color: #6c757d; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔥 Pain Point Alert: {topic}</h1>
            <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>High-Priority Clusters Found:</strong> {len(clusters)}</p>
            <p><strong>Total Engagement Weight:</strong> {analysis_summary.get('total_engagement_weight', 0):.2f}</p>
        </div>
        
        <h2>🚨 High-Priority Pain Points</h2>
    """
    
    for i, cluster in enumerate(clusters[:10], 1):  # Top 10 clusters
        trend_class = "trending" if cluster.get('trend_tag', '').startswith('🆙') else ""
        priority_class = "high-priority" if cluster.get('desperation_score', 0) >= 8 else ""
        css_class = f"cluster {trend_class} {priority_class}".strip()
        
        html_content += f"""
        <div class="{css_class}">
            <h3>{i}. {cluster.get('topic', 'Unknown')} {cluster.get('trend_tag', '')}</h3>
            
            <div class="metric">
                <span class="score">Desperation: {cluster.get('desperation_score', 0)}/10</span>
            </div>
            <div class="metric">
                <span class="engagement">Engagement: {cluster.get('total_engagement_weight', 0):.2f}</span>
            </div>
            <div class="metric">
                Frequency: {cluster.get('frequency', 0)} posts
            </div>
            <div class="metric">
                Avg Upvotes: {cluster.get('avg_upvotes', 0)}
            </div>
            
            <p><strong>Problem Category:</strong> {cluster.get('problem_category', 'Unknown')}</p>
            <p><strong>Subreddits:</strong> {', '.join(cluster.get('all_subreddits', []))}</p>
            <p><strong>Market Size:</strong> {cluster.get('market_proxy', {}).get('subscribers', 0):,} subscribers</p>
            
            <p><strong>MVP Opportunity:</strong> {cluster.get('mvp_suggestion', 'No suggestion available')}</p>
            
            <p><strong>Sample Post:</strong> {cluster.get('sample_post', {}).get('title', 'No title')[:100]}...</p>
            <p class="url"><a href="{cluster.get('sample_post', {}).get('url', '#')}">View Post</a></p>
        </div>
        """
    
    html_content += """
        <div style="margin-top: 30px; padding: 20px; background-color: #e9ecef; border-radius: 5px;">
            <h3>💡 Next Steps</h3>
            <ul>
                <li>Review trending clusters (🆙) for immediate opportunities</li>
                <li>Validate high-desperation problems with potential customers</li>
                <li>Research existing solutions for high-engagement clusters</li>
                <li>Consider building MVPs for problems with strong market indicators</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html_content

def format_slack_message(topic: str, clusters: List[Dict], analysis_summary: Dict) -> Dict:
    """Format Slack message for pain point digest."""
    trending_count = len([c for c in clusters if c.get('trend_tag', '').startswith('🆙')])
    high_desperation_count = len([c for c in clusters if c.get('desperation_score', 0) >= 8])
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔥 Pain Point Alert: {topic}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*High-Priority Clusters:* {len(clusters)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Trending:* {trending_count} 🆙"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*High Desperation (8+):* {high_desperation_count}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Total Engagement:* {analysis_summary.get('total_engagement_weight', 0):.2f}"
                }
            ]
        }
    ]
    
    # Add top 3 clusters
    for i, cluster in enumerate(clusters[:3], 1):
        trend_emoji = cluster.get('trend_tag', '')
        desperation = cluster.get('desperation_score', 0)
        engagement = cluster.get('total_engagement_weight', 0)
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{i}. {cluster.get('topic', 'Unknown')} {trend_emoji}*\n"
                        f"🔥 Desperation: {desperation}/10 | ⚡ Engagement: {engagement:.2f}\n"
                        f"📊 {cluster.get('frequency', 0)} posts | 👥 {cluster.get('market_proxy', {}).get('subscribers', 0):,} subs\n"
                        f"💡 _{cluster.get('mvp_suggestion', 'No suggestion')}_"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Post"
                },
                "url": cluster.get('sample_post', {}).get('url', '#')
            }
        })
    
    return {"blocks": blocks}

def send_email_alert(email: str, subject: str, html_content: str):
    """Send email alert using SMTP."""
    try:
        # Email configuration (you'll need to set these environment variables)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', smtp_username)
        
        if not all([smtp_username, smtp_password]):
            print("❌ Email credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = email
        
        # Add HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Email sent to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {email}: {str(e)}")
        return False

def send_slack_alert(webhook_url: str, message: Dict):
    """Send Slack alert using webhook."""
    try:
        response = requests.post(webhook_url, json=message)
        if response.status_code == 200:
            print(f"✅ Slack message sent")
            return True
        else:
            print(f"❌ Failed to send Slack message: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send Slack message: {str(e)}")
        return False

def update_search_last_run(search_id: int):
    """Update the last_run timestamp for a saved search."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE saved_searches 
        SET last_run = DATETIME('now')
        WHERE id = ?
    ''', (search_id,))
    
    conn.commit()
    conn.close()

async def process_alerts():
    """Main function to process all pending alerts."""
    print(f"🚀 Starting alert processing at {datetime.now()}")
    
    pending_alerts = get_pending_alerts()
    print(f"📧 Found {len(pending_alerts)} pending alerts")
    
    for alert in pending_alerts:
        print(f"\n🔍 Processing alert for topic: {alert['topic']}")
        
        # Run analysis
        analysis_results = await run_analysis_for_alert(alert['topic'])
        
        if not analysis_results:
            print(f"❌ Failed to get analysis results for {alert['topic']}")
            continue
        
        # Filter high-priority clusters
        all_clusters = analysis_results.get('clusters', [])
        high_priority_clusters = filter_high_priority_clusters(
            all_clusters, 
            alert['min_desperation_score']
        )
        
        if not high_priority_clusters:
            print(f"ℹ️ No high-priority clusters found for {alert['topic']}")
            update_search_last_run(alert['search_id'])
            continue
        
        print(f"🔥 Found {len(high_priority_clusters)} high-priority clusters")
        
        # Prepare content
        subject = f"🔥 Pain Point Alert: {alert['topic']} ({len(high_priority_clusters)} high-priority)"
        analysis_summary = analysis_results.get('analysis_summary', {})
        
        # Send email if configured
        if alert['email']:
            html_content = format_email_content(alert['topic'], high_priority_clusters, analysis_summary)
            send_email_alert(alert['email'], subject, html_content)
        
        # Send Slack if configured
        if alert['slack_webhook']:
            slack_message = format_slack_message(alert['topic'], high_priority_clusters, analysis_summary)
            send_slack_alert(alert['slack_webhook'], slack_message)
        
        # Update last run timestamp
        update_search_last_run(alert['search_id'])
    
    print(f"\n✅ Alert processing completed at {datetime.now()}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(process_alerts()) 