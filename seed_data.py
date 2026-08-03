import os
import django
from django.utils import timezone
from datetime import timedelta, date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syncfloww.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Profile
from ai_agents.models import AIAgent, AIModel
from workspaces.models import Workspace, WorkspaceMember, WorkspaceSetting
from social.models import Brand, BrandVoice, BrandGuideline, SocialAccount, OAuthToken
from analytics.models import AnalyticsSnapshot, DailyAnalytics, PlatformMetric
from notifications.models import Notification, NotificationSetting

from crm.models import Lead, Deal
from finance.models import RevenueRecord, ExpenseRecord, Subscription
from customer_success.models import SupportTicket, CustomerHealth
from hr.models import Employee, LeaveRequest
from marketplace.models import MarketplaceApp
from developer.models import APIKey, WebhookEndpoint

def seed():
    # 1. Seed AI Agents
    agents_data = [
        {
            'id': 'content-strategist',
            'name': 'Content Strategist',
            'description': 'Develops high-level content themes, campaign calendars, and omni-channel strategic roadmaps.',
            'task_type': 'strategy'
        },
        {
            'id': 'copywriter',
            'name': 'Copywriter',
            'description': 'Drafts persuasive long-form and short-form marketing copy with high conversion hooks.',
            'task_type': 'copywriting'
        },
        {
            'id': 'brand-guardian',
            'name': 'Brand Guardian',
            'description': 'Ensures tone consistency, voice compliance, and style guide adherence across all marketing channels.',
            'task_type': 'brand'
        },
        {
            'id': 'seo-agent',
            'name': 'SEO Agent',
            'description': 'Performs keyword clustering, search intent analysis, and on-page metadata optimization.',
            'task_type': 'seo'
        },
        {
            'id': 'research-agent',
            'name': 'Research Agent',
            'description': 'Monitors competitor movements, industry trends, and synthesizes audience insights.',
            'task_type': 'research'
        },
        {
            'id': 'analytics-agent',
            'name': 'Analytics Agent',
            'description': 'Analyzes cross-platform engagement metrics, ROI trends, and recommends actionable optimization steps.',
            'task_type': 'analytics'
        },
        {
            'id': 'publishing-agent',
            'name': 'Publishing Agent',
            'description': 'Schedules, formats, and dispatches social media posts across active social accounts.',
            'task_type': 'publish'
        },
        {
            'id': 'community-manager',
            'name': 'Community Manager',
            'description': 'Monitors brand mentions, handles customer comments, and drafts contextual automated responses.',
            'task_type': 'community'
        },
        {
            'id': 'idea-generator',
            'name': 'Idea & Hook Generator',
            'description': 'Generates trending video topics, clickbait titles, and viral hooks based on your niche.',
            'task_type': 'idea'
        },
        {
            'id': 'scriptwriter',
            'name': 'AI Video Scriptwriter',
            'description': 'Drafts complete video scripts including visual cues, sound effect suggestions, and spoken dialogue.',
            'task_type': 'script'
        },
        {
            'id': 'video-editor',
            'name': 'Automated Video Editor',
            'description': 'Stitches clips, adds overlays, synchronizes subtitles, and applies background audio tracks.',
            'task_type': 'video'
        },
        {
            'id': 'social-publisher',
            'name': 'Multi-Platform Publisher',
            'description': 'Schedules and cross-posts completed videos across YouTube, TikTok, and Instagram with optimized metadata.',
            'task_type': 'publish'
        }
    ]

    for agent_data in agents_data:
        agent, created = AIAgent.objects.get_or_create(
            id=agent_data['id'],
            defaults={
                'name': agent_data['name'],
                'description': agent_data['description'],
                'task_type': agent_data['task_type'],
                'is_active': True
            }
        )
        if created:
            print(f"Created Agent: {agent.name}")
        else:
            print(f"Agent already exists: {agent.name}")

    # 2. Seed Default User
    email = 'partnermarvel55@gmail.com'
    username = 'partnermarvel55'
    password = 'password123'

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        user.set_password(password)
        user.save()
        print(f"Created Superuser: {username}")
    else:
        print(f"Superuser already exists: {username}")

    # 3. Create or update profile
    profile, created = Profile.objects.get_or_create(
        user=user,
        defaults={
            'full_name': 'Marvel Partner',
            'avatar_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
            'email_confirmed': True,
            'provider': 'email'
        }
    )
    if created:
        print("Created Profile for User")
    else:
        print("Profile already exists")

    # 4. Seed Workspace
    workspace, created = Workspace.objects.get_or_create(
        owner=user,
        name="Marvel Workspace",
        defaults={
            'description': 'Main startup marketing workspace'
        }
    )
    if created:
        WorkspaceMember.objects.get_or_create(
            workspace=workspace,
            user=user,
            defaults={'role': 'owner'}
        )
        WorkspaceSetting.objects.get_or_create(workspace=workspace)
        print("Created default workspace & setting.")

    # 5. Seed Brand
    brand, created = Brand.objects.get_or_create(
        workspace=workspace,
        name="Marvel Tech",
        defaults={
            'created_by': user,
            'description': 'Cutting edge AI SaaS tools for next-gen productivity.',
            'logo_url': 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=150&q=80',
            'voice': 'Inspirational & Technical',
            'target_audience': 'Developers, Product Managers, Indie Hackers',
            'niche': 'AI & Productivity SaaS'
        }
    )
    if created:
        # Create brand voice
        BrandVoice.objects.get_or_create(
            brand=brand,
            defaults={
                'tone': 'Inspirational, direct, high-value, witty',
                'goal': 'Educate and convert technical builders',
                'keywords': ['workflow', 'agents', 'artificial intelligence', 'automation'],
                'examples': 'Stop manual work. Here is the workflow to completely automate your video pipeline...'
            }
        )
        # Create brand guideline
        BrandGuideline.objects.get_or_create(
            brand=brand,
            defaults={
                'fonts': ['Space Grotesk', 'Inter'],
                'colors': ['#000000', '#3B82F6', '#10B981'],
                'mission': 'Empowering builders with intelligent automated agents.',
                'website': 'https://marveltech.ai',
                'industry': 'AI Technology'
            }
        )
        print("Created Brand with detailed Voice and Guidelines.")

    # 6. Seed Connected Social Accounts & Tokens
    platforms = ['youtube', 'tiktok', 'instagram', 'linkedin']
    for plat in platforms:
        soc_acc, s_created = SocialAccount.objects.get_or_create(
            user=user,
            brand=brand,
            platform=plat,
            defaults={
                'username': f'marvel_{plat}',
                'display_name': f'Marvel Tech {plat.capitalize()}',
                'profile_image_url': f'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80',
                'is_active': True
            }
        )
        if s_created:
            OAuthToken.objects.get_or_create(
                social_account=soc_acc,
                defaults={
                    'access_token': f'access_tok_{plat}_seed',
                    'refresh_token': f'refresh_tok_{plat}_seed'
                }
            )

    print("Seed social accounts complete.")

    # 7. Seed AI Models
    models_data = [
        {'model_id': 'gemini-3.5-flash', 'name': 'Gemini 3.5 Flash', 'provider': 'gemini', 'cost': 0.00015},
        {'model_id': 'gemini-3.5-pro', 'name': 'Gemini 3.5 Pro', 'provider': 'gemini', 'cost': 0.00125},
        {'model_id': 'deepseek-chat', 'name': 'DeepSeek Chat', 'provider': 'deepseek', 'cost': 0.00008},
        {'model_id': 'gpt-4o', 'name': 'GPT-4o', 'provider': 'openai', 'cost': 0.00250},
    ]
    for md in models_data:
        AIModel.objects.get_or_create(
            model_id=md['model_id'],
            defaults={
                'name': md['name'],
                'provider': md['provider'],
                'cost_per_1k_tokens': md['cost']
            }
        )

    # 8. Seed Analytics Snapshots & Metrics
    for i, plat in enumerate(platforms):
        snap = AnalyticsSnapshot.objects.create(
            user=user,
            brand=brand,
            platform=plat,
            followers_count=12400 + (i * 3500),
            engagement_rate=3.14 + (i * 0.85),
            posts_count=42 + (i * 12),
            views_count=154000 + (i * 98000)
        )
        PlatformMetric.objects.create(snapshot=snap, name='likes', value=8430 + (i * 1200))
        PlatformMetric.objects.create(snapshot=snap, name='comments', value=492 + (i * 100))
        PlatformMetric.objects.create(snapshot=snap, name='shares', value=1280 + (i * 450))

    # Seed daily historical analytics for charts
    for day_offset in range(15):
        analytic_date = date.today() - timedelta(days=day_offset)
        for i, plat in enumerate(platforms):
            factor = (15 - day_offset) * 1.5
            DailyAnalytics.objects.get_or_create(
                brand=brand,
                platform=plat,
                date=analytic_date,
                defaults={
                    'likes': int(120 + factor + (i * 30)),
                    'shares': int(20 + factor + (i * 5)),
                    'comments': int(10 + factor + (i * 2)),
                    'views': int(1500 + (factor * 50) + (i * 600))
                }
            )

    print("Seed analytics complete.")

    # 9. Seed Notifications
    Notification.objects.get_or_create(
        user=user,
        title="Welcome to SyncflowAI MVP!",
        message="Your workspaces, default brand guidelines, and linked social accounts have been successfully provisioned. Try executing your first agent!",
        notification_type="success"
    )
    Notification.objects.get_or_create(
        user=user,
        title="Workspace setup complete",
        message="Marvel Workspace is configured. You now have access to multi-platform publishing and campaign templates.",
        notification_type="info"
    )
    NotificationSetting.objects.get_or_create(user=user)

    # 10. Seed Phase 4 - CRM
    print("Seeding CRM...")
    lead1, _ = Lead.objects.get_or_create(
        user=user, name="Alice Smith", company="Acme Corp", email="alice@acme.com",
        defaults={"status": "qualified", "deal_size": 25000.00}
    )
    lead2, _ = Lead.objects.get_or_create(
        user=user, name="Bob Jones", company="Stark Industries", email="bob@stark.com",
        defaults={"status": "new", "deal_size": 80000.00}
    )
    lead3, _ = Lead.objects.get_or_create(
        user=user, name="Charlie Miller", company="Cyberdyne Systems", email="charlie@cyberdyne.com",
        defaults={"status": "contacted", "deal_size": 45000.00}
    )
    Lead.objects.get_or_create(
        user=user, name="Diana Prince", company="Wayne Enterprises", email="diana@wayne.co",
        defaults={"status": "lost", "deal_size": 12000.00}
    )
    Deal.objects.get_or_create(
        user=user, lead=lead1, title="Acme Syncflow Platform Enterprise Integration",
        defaults={"amount": 25000.00, "stage": "negotiation", "probability": 60, "expected_close_date": date.today() + timedelta(days=30)}
    )
    Deal.objects.get_or_create(
        user=user, lead=lead2, title="Stark AI Marketing Agent Workforce",
        defaults={"amount": 80000.00, "stage": "prospecting", "probability": 20, "expected_close_date": date.today() + timedelta(days=60)}
    )

    # 11. Seed Phase 4 - Finance
    print("Seeding Finance...")
    Subscription.objects.get_or_create(
        user=user, company_name="Hooli Inc", defaults={"plan_name": "Enterprise Plan", "mrr": 2499.00, "status": "active", "start_date": date.today() - timedelta(days=180)}
    )
    Subscription.objects.get_or_create(
        user=user, company_name="Initech", defaults={"plan_name": "Pro Plan", "mrr": 299.00, "status": "active", "start_date": date.today() - timedelta(days=90)}
    )
    Subscription.objects.get_or_create(
        user=user, company_name="Soylent Corp", defaults={"plan_name": "Team Plan", "mrr": 149.00, "status": "cancelled", "start_date": date.today() - timedelta(days=120)}
    )
    RevenueRecord.objects.get_or_create(
        user=user, source="subscription", amount=2798.00, date=date.today() - timedelta(days=5), defaults={"description": "SaaS Recurring MRR Billing Cycle"}
    )
    RevenueRecord.objects.get_or_create(
        user=user, source="consulting", amount=5000.00, date=date.today() - timedelta(days=10), defaults={"description": "Custom Workflow Consulting"}
    )
    ExpenseRecord.objects.get_or_create(
        user=user, category="hosting", amount=820.00, date=date.today() - timedelta(days=5), defaults={"description": "AWS Instances & Gemini API Credits"}
    )
    ExpenseRecord.objects.get_or_create(
        user=user, category="marketing", amount=1500.00, date=date.today() - timedelta(days=12), defaults={"description": "Google Search PPC Campaigns"}
    )

    # 12. Seed Phase 4 - Support & CS
    print("Seeding Customer Success...")
    SupportTicket.objects.get_or_create(
        user=user, title="API Key Handshake Failing", customer_name="Initech",
        defaults={"priority": "high", "status": "open", "description": "We are receiving a 403 Forbidden error when trying to fetch campaign metrics using our custom developer token. Please verify."}
    )
    SupportTicket.objects.get_or_create(
        user=user, title="Billing Profile Update Request", customer_name="Hooli Inc",
        defaults={"priority": "low", "status": "resolved", "description": "Requesting update to our corporate VAT registration number on invoices."}
    )
    CustomerHealth.objects.get_or_create(
        user=user, customer_name="Hooli Inc", defaults={"health_score": 95, "risk_status": "low", "last_interaction": date.today() - timedelta(days=1)}
    )
    CustomerHealth.objects.get_or_create(
        user=user, customer_name="Initech", defaults={"health_score": 68, "risk_status": "medium", "last_interaction": date.today() - timedelta(days=3)}
    )

    # 13. Seed Phase 4 - HR
    print("Seeding HR...")
    emp1, _ = Employee.objects.get_or_create(
        user=user, name="Eleanor Vance", role="Chief Executive Officer", department="Executive",
        defaults={"salary": 180000.00, "performance_rating": 4.90, "status": "active", "hired_at": date.today() - timedelta(days=365)}
    )
    emp2, _ = Employee.objects.get_or_create(
        user=user, name="Marcus Sterling", role="VP of Finance / AI CFO", department="Finance",
        defaults={"salary": 140000.00, "performance_rating": 4.80, "status": "active", "hired_at": date.today() - timedelta(days=300)}
    )
    emp3, _ = Employee.objects.get_or_create(
        user=user, name="Sarah Jenkins", role="VP of Growth / CMO", department="Marketing",
        defaults={"salary": 110000.00, "performance_rating": 4.70, "status": "active", "hired_at": date.today() - timedelta(days=250)}
    )
    emp4, _ = Employee.objects.get_or_create(
        user=user, name="Dr. Aris Thorne", role="Lead Platform Architect", department="Engineering",
        defaults={"salary": 150000.00, "performance_rating": 4.95, "status": "active", "hired_at": date.today() - timedelta(days=350)}
    )
    emp5, _ = Employee.objects.get_or_create(
        user=user, name="Clara Moss", role="Director of Talent Operations", department="HR",
        defaults={"salary": 95000.00, "performance_rating": 4.60, "status": "active", "hired_at": date.today() - timedelta(days=200)}
    )
    LeaveRequest.objects.get_or_create(
        user=user, employee=emp5, leave_type="vacation", start_date=date.today() + timedelta(days=15), end_date=date.today() + timedelta(days=20),
        defaults={"status": "approved", "reason": "Summer family trip"}
    )

    # 14. Seed Phase 4 - Marketplace
    print("Seeding Marketplace...")
    MarketplaceApp.objects.get_or_create(
        name="Salesforce Connector", defaults={"description": "Sync CRM leads, custom fields, and deals from Salesforce into SyncFloww instantly.", "category": "connector", "price": 49.00, "is_installed": False, "rating": 4.80, "icon": "☁️"}
    )
    MarketplaceApp.objects.get_or_create(
        name="Slack Alert Agent", defaults={"description": "Receive beautiful, rich real-time notifications inside Slack for deals won, campaigns completed, and HR leave requests.", "category": "agent", "price": 0.00, "is_installed": True, "rating": 4.90, "icon": "💬"}
    )
    MarketplaceApp.objects.get_or_create(
        name="Predictive Forecaster Pro", defaults={"description": "Unlocks advanced deep learning neural networks to predict customer churn, subscription MRR growth, and expense burn rates.", "category": "utility", "price": 99.00, "is_installed": False, "rating": 4.70, "icon": "📈"}
    )
    MarketplaceApp.objects.get_or_create(
        name="Stripe Billing Connector", defaults={"description": "Auto-reconcile subscription status, invoices, and MRR metrics from Stripe to Syncflow Finance board.", "category": "connector", "price": 19.00, "is_installed": True, "rating": 4.80, "icon": "💳"}
    )

    # 15. Seed Phase 4 - Developer
    print("Seeding Developer...")
    APIKey.objects.get_or_create(
        user=user, name="Production Core Key", prefix="sf_live_4a2c9e1b",
        defaults={"secret_key": "sf_sec_e83bc29aa98dfd7e102f43d81b98a0c2834b92c", "is_active": True}
    )
    WebhookEndpoint.objects.get_or_create(
        user=user, url="https://api.initech.com/syncflow-receiver",
        defaults={"description": "Primary server payload handler for real-time campaign updates", "secret_token": "whsec_091b2c3d4e5f6a7b", "event_types": "campaign.created,task.completed", "is_active": True}
    )

    print("Seed complete successfully!")

if __name__ == '__main__':
    seed()
