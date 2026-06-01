import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        # Calculate token efficiency (completion_tokens / total_tokens). Higher is better.
        token_efficiency = 0.0
        if usage.get("total_tokens", 0) > 0:
            token_efficiency = round((usage.get("completion_tokens", 0) / usage.get("total_tokens", 0)) * 100, 2)

        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "token_efficiency_pct": token_efficiency,
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage) # Mock cost calculation
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Calculate estimated cost based on model pricing.
        Pricing is per 1K tokens (approximate as of 2024).
        """
        pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gemini-1.5-flash": {"input": 0.00025, "output": 0.0005},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        }
        model_price = pricing.get(model, {"input": 0.01, "output": 0.01})
        input_cost = (usage.get("prompt_tokens", 0) / 1000) * model_price["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1000) * model_price["output"]
        return round(input_cost + output_cost, 6)

    def print_session_summary(self):
        """Prints an industry-standard telemetry report at the end of the run."""
        if not self.session_metrics:
            print("\n📊 TELEMETRY: No requests made in this session.")
            return
            
        total_requests = len(self.session_metrics)
        total_tokens = sum(m["total_tokens"] for m in self.session_metrics)
        total_cost = sum(m["cost_estimate"] for m in self.session_metrics)
        avg_latency = sum(m["latency_ms"] for m in self.session_metrics) / total_requests
        avg_efficiency = sum(m["token_efficiency_pct"] for m in self.session_metrics) / total_requests
        
        print("\n" + "=" * 60)
        print("📊 TELEMETRY DASHBOARD (SESSION REPORT)")
        print("=" * 60)
        print(f"🔹 Total LLM Requests : {total_requests}")
        print(f"🔹 Total Tokens Used  : {total_tokens:,}")
        print(f"🔹 Estimated Cost     : ${total_cost:.6f}")
        print(f"🔹 Average Latency    : {avg_latency:.0f} ms / request")
        print(f"🔹 Avg Token Efficiency: {avg_efficiency:.1f}% (completion/total ratio)")
        print("=" * 60 + "\n")

# Global tracker instance
tracker = PerformanceTracker()
