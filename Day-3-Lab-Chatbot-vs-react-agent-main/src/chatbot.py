"""
Chatbot Baseline - Simple LLM chatbot WITHOUT tools.
Used to demonstrate limitations compared to the ReAct Agent.
"""
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class Chatbot:
    """
    A simple chatbot that directly queries an LLM without any tool access.
    This serves as the baseline to compare against the ReAct Agent.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def chat(self, user_input: str) -> str:
        """Send user input directly to the LLM and return the response."""
        logger.log_event("CHATBOT_START", {
            "input": user_input,
            "model": self.llm.model_name
        })

        result = self.llm.generate(
            prompt=user_input,
            system_prompt="You are a helpful assistant. Answer the user's question to the best of your ability."
        )

        logger.log_event("CHATBOT_END", {
            "output": result["content"],
            "usage": result.get("usage", {}),
            "latency_ms": result.get("latency_ms", 0)
        })

        return result["content"]
