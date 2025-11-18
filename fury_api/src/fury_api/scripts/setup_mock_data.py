#!/usr/bin/env python3
"""
Comprehensive script to set up all mock data including plugins, sources, and content.
Handles the entire dependency chain automatically.

Usage:
    python setup_mock_data.py --api-url http://localhost:3000 --token YOUR_AUTH_TOKEN
"""

import argparse
import os
import sys
from typing import Any

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install it with: pip install requests")
    sys.exit(1)


# ============================================================================
# MOCK DATA
# ============================================================================

MOCK_PLUGINS = [
    {
        "data_source": "twitter",
        "title": "Twitter/X Integration",
        "credentials": {},
        "properties": {"platform": "twitter"}
    },
    {
        "data_source": "medium",
        "title": "Medium Blog",
        "credentials": {},
        "properties": {"platform": "medium"}
    },
    {
        "data_source": "notion",
        "title": "Notion Workspace",
        "credentials": {},
        "properties": {"platform": "notion"}
    },
    {
        "data_source": "github",
        "title": "GitHub Repository",
        "credentials": {},
        "properties": {"platform": "github"}
    },
    {
        "data_source": "linkedin",
        "title": "LinkedIn Profile",
        "credentials": {},
        "properties": {"platform": "linkedin"}
    },
]

# Sources will reference plugin_id after plugins are created
MOCK_SOURCES = [
    {
        "plugin_index": 0,  # Twitter
        "source_type": "twitter_account",
        "external_id": "user_123456",
        "display_name": "Tech Enthusiast",
        "handle": "@tech_enthusiast",
        "avatar_url": "https://avatar.example.com/twitter.jpg",
        "profile_url": "https://twitter.com/tech_enthusiast",
        "platform_type": "twitter",
        "is_active": True,
        "sync_status": "active"
    },
    {
        "plugin_index": 1,  # Medium
        "source_type": "medium_publication",
        "external_id": "pub_789012",
        "display_name": "Engineering Blog",
        "handle": "@engineering-blog",
        "avatar_url": "https://avatar.example.com/medium.jpg",
        "profile_url": "https://medium.com/@engineering-blog",
        "platform_type": "medium",
        "is_active": True,
        "sync_status": "active"
    },
    {
        "plugin_index": 2,  # Notion
        "source_type": "notion_workspace",
        "external_id": "workspace_345678",
        "display_name": "Personal Knowledge Base",
        "platform_type": "notion",
        "is_active": True,
        "sync_status": "active"
    },
    {
        "plugin_index": 3,  # GitHub
        "source_type": "github_repo",
        "external_id": "repo_901234",
        "display_name": "awesome-project",
        "handle": "username/awesome-project",
        "profile_url": "https://github.com/username/awesome-project",
        "platform_type": "github",
        "is_active": True,
        "sync_status": "active"
    },
    {
        "plugin_index": 4,  # LinkedIn
        "source_type": "linkedin_profile",
        "external_id": "profile_567890",
        "display_name": "Professional Profile",
        "handle": "professional-user",
        "avatar_url": "https://avatar.example.com/linkedin.jpg",
        "profile_url": "https://linkedin.com/in/professional-user",
        "platform_type": "linkedin",
        "is_active": True,
        "sync_status": "active"
    },
]

# Content will reference source_id after sources are created
MOCK_CONTENT = [
    {
        "source_index": 0,  # Twitter
        "external_id": "tweet_001",
        "external_url": "https://twitter.com/user/status/123456789",
        "title": "Insights on AI Development",
        "body": "Just finished reading an amazing paper on transformer architectures. The attention mechanism is truly revolutionary for natural language processing!",
        "excerpt": "Just finished reading an amazing paper on transformer architectures...",
        "published_at": "2025-11-15T10:30:00",
        "synced_at": "2025-11-17T08:00:00",
        "platform_metadata": {"likes": 42, "retweets": 15, "platform": "twitter"}
    },
    {
        "source_index": 1,  # Medium
        "external_id": "article_002",
        "external_url": "https://medium.com/@author/article-slug",
        "title": "Building Scalable APIs with FastAPI",
        "body": "FastAPI has become my go-to framework for building modern APIs. Its automatic documentation, type hints, and async support make development incredibly efficient. In this article, I'll share some best practices I've learned over the past year.",
        "excerpt": "FastAPI has become my go-to framework for building modern APIs...",
        "published_at": "2025-11-10T14:20:00",
        "synced_at": "2025-11-17T08:05:00",
        "platform_metadata": {"claps": 128, "reading_time_minutes": 8, "platform": "medium"}
    },
    {
        "source_index": 0,  # Twitter
        "external_id": "tweet_003",
        "external_url": "https://twitter.com/user/status/987654321",
        "title": None,
        "body": "Hot take: Documentation is just as important as the code itself. Future you will thank present you! 📚✨",
        "excerpt": "Hot take: Documentation is just as important as the code itself...",
        "published_at": "2025-11-16T16:45:00",
        "synced_at": "2025-11-17T08:10:00",
        "platform_metadata": {"likes": 87, "retweets": 23, "platform": "twitter"}
    },
    {
        "source_index": 2,  # Notion
        "external_id": "note_004",
        "external_url": None,
        "title": "Meeting Notes - Product Roadmap Q4",
        "body": "Discussed upcoming features for Q4: 1) Enhanced search functionality with semantic search, 2) Real-time collaboration features, 3) Mobile app development kickoff. Action items: Schedule design review for search UI, Assign backend team to research vector databases.",
        "excerpt": "Discussed upcoming features for Q4: Enhanced search, real-time collaboration...",
        "published_at": "2025-11-14T09:00:00",
        "synced_at": "2025-11-17T08:15:00",
        "platform_metadata": {"attendees": 5, "duration_minutes": 60, "platform": "notion"}
    },
    {
        "source_index": 1,  # Medium
        "external_id": "article_005",
        "external_url": "https://dev.to/author/microservices-patterns",
        "title": "Design Patterns for Microservices Architecture",
        "body": "Microservices have transformed how we build scalable applications. This comprehensive guide covers essential patterns including Circuit Breaker, Service Discovery, API Gateway, and Event Sourcing. Learn when and how to apply each pattern effectively.",
        "excerpt": "Microservices have transformed how we build scalable applications...",
        "published_at": "2025-11-12T11:15:00",
        "synced_at": "2025-11-17T08:20:00",
        "platform_metadata": {"reactions": 245, "comments": 18, "reading_time_minutes": 12, "platform": "dev.to"}
    },
    {
        "source_index": 0,  # Twitter
        "external_id": "tweet_006",
        "external_url": "https://twitter.com/user/status/456789123",
        "title": None,
        "body": "Debugging tip: When you're stuck, explain the problem out loud to a rubber duck (or a colleague). The act of explaining often reveals the solution! 🦆💡",
        "excerpt": "Debugging tip: When you're stuck, explain the problem out loud...",
        "published_at": "2025-11-13T08:20:00",
        "synced_at": "2025-11-17T08:25:00",
        "platform_metadata": {"likes": 156, "retweets": 42, "platform": "twitter"}
    },
    {
        "source_index": 3,  # GitHub
        "external_id": "github_007",
        "external_url": "https://github.com/user/awesome-repo/discussions/42",
        "title": "RFC: Implementing WebSocket Support",
        "body": "Proposing to add WebSocket support for real-time features. This would enable live updates, collaborative editing, and instant notifications. Implementation would use Socket.IO for browser compatibility and automatic reconnection handling.",
        "excerpt": "Proposing to add WebSocket support for real-time features...",
        "published_at": "2025-11-11T15:30:00",
        "synced_at": "2025-11-17T08:30:00",
        "platform_metadata": {"upvotes": 34, "comments": 12, "platform": "github"}
    },
    {
        "source_index": 2,  # Notion
        "external_id": "note_008",
        "external_url": None,
        "title": "Research: Vector Databases Comparison",
        "body": "Compared three vector database solutions: Pinecone, Weaviate, and Qdrant. Key findings: Pinecone offers best ease of use, Weaviate has superior filtering capabilities, Qdrant provides best performance for our use case. Recommendation: Start with Qdrant for cost-effectiveness and performance.",
        "excerpt": "Compared three vector database solutions for semantic search...",
        "published_at": "2025-11-09T13:45:00",
        "synced_at": "2025-11-17T08:35:00",
        "platform_metadata": {"collaborators": 3, "platform": "notion"}
    },
    {
        "source_index": 0,  # Twitter
        "external_id": "tweet_009",
        "external_url": "https://twitter.com/user/status/789123456",
        "title": None,
        "body": "TIL: Python's 'walrus operator' (:=) can make your code more concise. Instead of assigning and checking in separate lines, you can do both at once! Mind = blown 🤯",
        "excerpt": "TIL: Python's 'walrus operator' can make your code more concise...",
        "published_at": "2025-11-08T17:10:00",
        "synced_at": "2025-11-17T08:40:00",
        "platform_metadata": {"likes": 203, "retweets": 67, "platform": "twitter"}
    },
    {
        "source_index": 1,  # Medium
        "external_id": "article_010",
        "external_url": "https://medium.com/@author/react-performance",
        "title": "React Performance Optimization: A Deep Dive",
        "body": "Performance optimization in React applications requires understanding the rendering lifecycle. This article explores useMemo, useCallback, React.memo, and virtualization techniques. Includes practical examples and benchmarks showing 60% performance improvement in a real-world application.",
        "excerpt": "Performance optimization in React applications requires understanding...",
        "published_at": "2025-11-07T10:00:00",
        "synced_at": "2025-11-17T08:45:00",
        "platform_metadata": {"claps": 342, "reading_time_minutes": 15, "platform": "medium"}
    },
    {
        "source_index": 4,  # LinkedIn
        "external_id": "linkedin_011",
        "external_url": "https://linkedin.com/posts/user_activity123",
        "title": "Lessons Learned: Scaling to 1M Users",
        "body": "Reflecting on our journey from 0 to 1 million users. Key takeaways: 1) Start with a monolith, 2) Monitor everything from day one, 3) Database optimization is crucial, 4) Horizontal scaling beats vertical scaling, 5) Culture matters more than technology. Happy to share more details in the comments!",
        "excerpt": "Reflecting on our journey from 0 to 1 million users...",
        "published_at": "2025-11-06T09:30:00",
        "synced_at": "2025-11-17T08:50:00",
        "platform_metadata": {"likes": 1247, "comments": 89, "shares": 156, "platform": "linkedin"}
    },
    {
        "source_index": 2,  # Notion
        "external_id": "note_012",
        "external_url": None,
        "title": "Design System Guidelines v2.0",
        "body": "Updated design system with new components and patterns. Major changes: Dark mode support, new color palette with better accessibility, responsive spacing scale, updated typography system. All components now support both light and dark themes. Migration guide available in the wiki.",
        "excerpt": "Updated design system with new components and patterns...",
        "published_at": "2025-11-05T14:15:00",
        "synced_at": "2025-11-17T08:55:00",
        "platform_metadata": {"pages": 8, "last_edited_by": "design_team", "platform": "notion"}
    },
    {
        "source_index": 0,  # Twitter
        "external_id": "tweet_013",
        "external_url": "https://twitter.com/user/status/321654987",
        "title": None,
        "body": "Code review best practice: Start with positive feedback. Point out what's done well before suggesting improvements. This creates a more collaborative and less defensive environment. 🤝",
        "excerpt": "Code review best practice: Start with positive feedback...",
        "published_at": "2025-11-04T12:00:00",
        "synced_at": "2025-11-17T09:00:00",
        "platform_metadata": {"likes": 412, "retweets": 98, "platform": "twitter"}
    },
    {
        "source_index": 3,  # GitHub
        "external_id": "github_014",
        "external_url": "https://github.com/user/project/issues/156",
        "title": "Feature Request: Add Export Functionality",
        "body": "Users have been requesting the ability to export their data in multiple formats (CSV, JSON, PDF). This would improve data portability and enable integration with external tools. Proposed implementation: Add export button in settings, support batch exports, include filters for date range and content type.",
        "excerpt": "Users requesting ability to export data in multiple formats...",
        "published_at": "2025-11-03T16:20:00",
        "synced_at": "2025-11-17T09:05:00",
        "platform_metadata": {"upvotes": 67, "comments": 23, "labels": ["enhancement", "user-request"], "platform": "github"}
    },
    {
        "source_index": 1,  # Medium
        "external_id": "article_015",
        "external_url": "https://dev.to/author/testing-strategies",
        "title": "Testing Strategies for Modern Web Applications",
        "body": "Comprehensive guide to testing: unit tests for business logic, integration tests for API endpoints, E2E tests for critical user flows. The testing pyramid is outdated - consider the testing trophy instead. Includes setup guides for Jest, Pytest, and Playwright with real-world examples.",
        "excerpt": "Comprehensive guide to testing modern web applications...",
        "published_at": "2025-11-02T11:45:00",
        "synced_at": "2025-11-17T09:10:00",
        "platform_metadata": {"reactions": 389, "comments": 45, "reading_time_minutes": 18, "platform": "dev.to"}
    },
]


# ============================================================================
# API FUNCTIONS
# ============================================================================

def api_request(
    method: str,
    url: str,
    headers: dict[str, str],
    json_data: dict[str, Any] | None = None,
    timeout: int = 10
) -> tuple[bool, Any]:
    """Make an API request and return (success, result)."""
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_data,
            timeout=timeout
        )

        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, str(e)


def create_plugins(api_url: str, auth_token: str) -> list[dict[str, Any]]:
    """Create all plugins and return their IDs."""
    print("\n" + "="*70)
    print("STEP 1: Creating Plugins")
    print("="*70)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    created_plugins = []

    for i, plugin_data in enumerate(MOCK_PLUGINS, 1):
        print(f"[{i}/{len(MOCK_PLUGINS)}] Creating plugin: {plugin_data['title']}...", end=" ")

        success, result = api_request(
            "POST",
            f"{api_url}/api/v1/plugins",
            headers,
            plugin_data
        )

        if success:
            print(f"✅ Success (ID: {result['id']})")
            created_plugins.append(result)
        else:
            print("❌ Failed")
            print(f"    Error: {result}")
            sys.exit(1)

    return created_plugins


def create_sources(api_url: str, auth_token: str, plugins: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create all sources and return their IDs."""
    print("\n" + "="*70)
    print("STEP 2: Creating Sources")
    print("="*70)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    created_sources = []

    for i, source_data in enumerate(MOCK_SOURCES, 1):
        # Get plugin_id from the created plugins
        plugin_index = source_data.pop("plugin_index")
        source_data["plugin_id"] = plugins[plugin_index]["id"]

        print(f"[{i}/{len(MOCK_SOURCES)}] Creating source: {source_data['display_name']}...", end=" ")

        success, result = api_request(
            "POST",
            f"{api_url}/api/v1/sources",
            headers,
            source_data
        )

        if success:
            print(f"✅ Success (ID: {result['id']})")
            created_sources.append(result)
        else:
            print("❌ Failed")
            print(f"    Error: {result}")
            sys.exit(1)

    return created_sources


def create_content(api_url: str, auth_token: str, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create all content items and return their IDs."""
    print("\n" + "="*70)
    print("STEP 3: Creating Content")
    print("="*70)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    created_content = []

    for i, content_data in enumerate(MOCK_CONTENT, 1):
        # Get source_id from the created sources
        source_index = content_data.pop("source_index")
        content_data["source_id"] = sources[source_index]["id"]

        print(f"[{i}/{len(MOCK_CONTENT)}] Creating content: {content_data['external_id']}...", end=" ")

        success, result = api_request(
            "POST",
            f"{api_url}/api/v1/content",
            headers,
            content_data
        )

        if success:
            print(f"✅ Success (ID: {result['id']})")
            created_content.append(result)
        else:
            print("❌ Failed")
            print(f"    Error: {result}")
            sys.exit(1)

    return created_content


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Set up complete mock data for the application")
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_URL", "http://localhost:3000"),
        help="API base URL (default: http://localhost:3000 or $API_URL)"
    )
    parser.add_argument(
        "--token",
        default=os.getenv("AUTH_TOKEN"),
        help="Authentication token (default: $AUTH_TOKEN)"
    )

    args = parser.parse_args()

    if not args.token:
        print("❌ Error: Authentication token required. Use --token or set AUTH_TOKEN environment variable.")
        sys.exit(1)

    print("🚀 Mock Data Setup Script")
    print(f"🌐 API URL: {args.api_url}")
    print(f"🔑 Auth token: {args.token[:20]}...")

    # Step 1: Create Plugins
    plugins = create_plugins(args.api_url, args.token)

    # Step 2: Create Sources
    sources = create_sources(args.api_url, args.token, plugins)

    # Step 3: Create Content
    content = create_content(args.api_url, args.token, sources)

    # Summary
    print("\n" + "="*70)
    print("✅ SETUP COMPLETE!")
    print("="*70)
    print(f"📦 Created {len(plugins)} plugins")
    print(f"📦 Created {len(sources)} sources")
    print(f"📦 Created {len(content)} content items")
    print("\n🎉 All mock data has been successfully inserted!")


if __name__ == "__main__":
    main()
