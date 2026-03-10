from langchain.tools import tool
import time

@tool
def post_to_social_media(content: str, platform: str) -> str:
    """
    Simulates posting content to a specified social media platform.
    Args:
        content (str): The body of the post.
        platform (str): 'twitter', 'linkedin', etc.
    """
    # In a real scenario, this connects to your SocialAccount models 
    # to fetch the OAuth tokens and use requests.post()
    print(f"[TOOL EXECUTION] Preparing to post on {platform}...")
    time.sleep(1) # Simulate network call
    print(f"[TOOL EXECUTION] Successfully posted: '{content}'")
    
    return "SUCCESS: Post published."

@tool
def fetch_trending_topics(n: int = 3) -> str:
    """
    Simulates finding top trending topics.
    Args:
        n (int): Number of top trending topics.
    """
    return "1. #AI, 2. #Django, 3. #Automation"
