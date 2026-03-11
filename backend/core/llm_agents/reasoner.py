class AgentReasoner:

    def analyze(self, response):
        if "comment" in response.lower():
            return "comment_reply"
        
        if "post" in response.lower():
            return "content_generation"

        if "dm" in response.lower() or "message" in response.lower():
            return "dm_reply"

        if "hate" in response.lower() or "love" in response.lower():
            return "sentiment_analysis"

        return "general_response"
