# app/jira_client.py
"""
Jira API integration for querying tickets.

Env vars expected:
  JIRA_DOMAIN          -> e.g., yourcompany.atlassian.net
  JIRA_EMAIL           -> your email for Jira Cloud
  JIRA_API_TOKEN       -> API token from https://id.atlassian.com/manage-profile/security/api-tokens
  JIRA_PROJECT_KEY     -> optional; default project key (e.g., TECH, DEV)
  SLACK_TECH_CHANNEL_ID -> Slack channel ID for tech team notifications
"""

import os
from typing import Optional, List, Dict
import httpx
from base64 import b64encode

JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")
SLACK_TECH_CHANNEL_ID = os.getenv("SLACK_TECH_CHANNEL_ID")

# Print Jira configuration status on module load
print("=" * 50)
print("🔧 Jira Configuration Status:")
print(f"  JIRA_DOMAIN: {'✅ Set' if JIRA_DOMAIN else '❌ Missing'}")
print(f"  JIRA_EMAIL: {'✅ Set' if JIRA_EMAIL else '❌ Missing'}")
print(f"  JIRA_API_TOKEN: {'✅ Set' if JIRA_API_TOKEN else '❌ Missing'}")
print(f"  JIRA_PROJECT_KEY: {JIRA_PROJECT_KEY or '(not set - will query last 30 days)'}")
if JIRA_DOMAIN and JIRA_EMAIL and JIRA_API_TOKEN:
    print("  ✅ Jira integration is ENABLED")
else:
    print("  ⚠️  Jira integration is DISABLED (missing credentials)")
print("=" * 50)


def _get_auth_header() -> Optional[str]:
    """Generate Basic Auth header for Jira Cloud."""
    if not JIRA_EMAIL or not JIRA_API_TOKEN:
        return None
    
    credentials = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    encoded = b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


async def search_jira_tickets(
    jql: Optional[str] = None,
    project_key: Optional[str] = None,
    max_results: int = 20
) -> Dict:
    """
    Search Jira tickets using JQL (Jira Query Language).
    
    Args:
        jql: Custom JQL query (optional)
        project_key: Project key to filter by (optional, uses JIRA_PROJECT_KEY if not provided)
        max_results: Maximum number of results to return
    
    Returns:
        Dict with 'success', 'tickets', 'total', and optional 'error'
    """
    if not JIRA_DOMAIN:
        return {
            "success": False,
            "error": "JIRA_DOMAIN not configured",
            "tickets": [],
            "total": 0
        }
    
    auth_header = _get_auth_header()
    if not auth_header:
        return {
            "success": False,
            "error": "Jira credentials not configured (JIRA_EMAIL and JIRA_API_TOKEN required)",
            "tickets": [],
            "total": 0
        }
    
    # Build JQL query
    if not jql:
        proj_key = project_key or JIRA_PROJECT_KEY
        if proj_key:
            jql = f"project = {proj_key} ORDER BY created DESC"
        else:
            # Fallback: Use a date restriction to avoid unbounded queries
            # This gets tickets from the last 30 days across all projects
            jql = "created >= -30d ORDER BY created DESC"
    
    url = f"https://{JIRA_DOMAIN}/rest/api/3/search/jql"
    headers = {
        "Authorization": auth_header,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "jql": jql,
        "maxResults": max_results,
        "fields": ["summary", "status", "assignee", "priority", "created", "updated", "issuetype"]
    }

    print(f"🔍 Executing Jira query:")
    print(f"   URL: {url}")
    print(f"   JQL: {jql}")
    print(f"   Max Results: {max_results}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            print(f"📡 Jira API response status: {response.status_code}")
            print(f"📊 Total issues found: {data.get('total', 0)}")

            # Format tickets for easier consumption
            tickets = []
            for issue in data.get("issues", []):
                try:
                    fields = issue.get("fields", {}) or {}
                    assignee = fields.get("assignee")

                    # Safe nested dict access with fallbacks
                    status_obj = fields.get("status") or {}
                    priority_obj = fields.get("priority") or {}
                    issuetype_obj = fields.get("issuetype") or {}

                    tickets.append({
                        "key": issue.get("key") or "N/A",
                        "summary": fields.get("summary") or "No summary",
                        "status": status_obj.get("name") if isinstance(status_obj, dict) else "Unknown",
                        "priority": priority_obj.get("name") if isinstance(priority_obj, dict) else "None",
                        "assignee": assignee.get("displayName") if (assignee and isinstance(assignee, dict)) else "Unassigned",
                        "type": issuetype_obj.get("name") if isinstance(issuetype_obj, dict) else "Unknown",
                        "created": fields.get("created") or "N/A",
                        "updated": fields.get("updated") or "N/A",
                        "url": f"https://{JIRA_DOMAIN}/browse/{issue.get('key')}"
                    })
                except Exception as e:
                    print(f"⚠️ Error parsing issue {issue.get('key', 'unknown')}: {e}")
                    continue

            return {
                "success": True,
                "tickets": tickets,
                "total": data.get("total", 0),
                "jql": jql
            }
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Jira API error: {e.response.status_code}"
        try:
            error_detail = e.response.json()
            error_msg += f" - {error_detail.get('errorMessages', [])}"
        except:
            pass

        print(f"❌ HTTP Error: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "tickets": [],
            "total": 0
        }
    except Exception as e:
        import traceback
        error_msg = f"Error querying Jira: {str(e)}"
        print(f"❌ Exception in search_jira_tickets: {error_msg}")
        print(traceback.format_exc())

        return {
            "success": False,
            "error": error_msg,
            "tickets": [],
            "total": 0
        }


def format_tickets_for_display(tickets: List[Dict]) -> str:
    """Format tickets for chat display."""
    if not tickets:
        return "No tickets found."

    lines = [f"📋 **{len(tickets)} Jira Ticket(s) Found**\n"]

    for i, ticket in enumerate(tickets, 1):
        # Clean format - ticket key is bolded, URL on separate line to avoid auto-unfurling
        lines.append(
            f"{i}. **{ticket['key']}** - {ticket['summary']}\n"
            f"   • Status: `{ticket['status']}` | Priority: `{ticket['priority']}` | "
            f"Assignee: {ticket['assignee']}\n"
            f"   • Link: {ticket['url']}"
        )

    return "\n".join(lines)


def format_tickets_for_slack(tickets: List[Dict], user_query: str) -> str:
    """Format tickets for Slack tech team notification."""
    lines = [
        f"🎫 *Jira Query from FinStackAI*",
        f"User asked: _{user_query}_\n",
        f"Found {len(tickets)} ticket(s):\n"
    ]
    
    for ticket in tickets[:10]:  # Limit to 10 for Slack
        lines.append(
            f"• *<{ticket['url']}|{ticket['key']}>* - {ticket['summary']}\n"
            f"  Status: {ticket['status']} | Priority: {ticket['priority']} | "
            f"Assignee: {ticket['assignee']}"
        )
    
    if len(tickets) > 10:
        lines.append(f"\n_...and {len(tickets) - 10} more tickets_")
    
    return "\n".join(lines)
