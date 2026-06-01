import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Implements the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 8):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        System prompt that instructs the agent to follow ReAct format.
        Includes:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""You are an intelligent assistant that solves problems step by step using tools.

You have access to the following tools:
{tool_descriptions}

You MUST follow this EXACT format for every step:

Thought: <your reasoning about what to do next>
Action: <tool_name(arg1, arg2, ...)>

After you receive an Observation (the result of the tool call), continue with another Thought/Action pair.

When you have gathered enough information to fully answer the user's question, respond with:
Thought: I now have all the information needed to answer.
Final Answer: <your complete, detailed answer with calculations>

IMPORTANT RULES:
1. Always start with a Thought before taking an Action.
2. Use ONLY the tools listed above. Do NOT invent tools.
3. Call only ONE tool per step.
4. Tool arguments must be simple values separated by commas. Numbers must be plain numbers like 2 or 0.5 (NOT expressions like 2*0.5 or 0e0.5). Strings must NOT be wrapped in quotes.
5. If a tool returns an error, carefully check your arguments and try again with corrected values.
6. Always end with "Final Answer:" when you have the complete answer.
7. Do ALL calculations yourself in the Final Answer. Show your math step by step.
8. For multi-step questions, plan ahead: identify ALL tools you need to call BEFORE starting.

Example 1 (Simple):
User: How much is a flight from Hanoi to Paris?
Thought: I need to check the flight prices from Hanoi to Paris.
Action: search_flights(Hanoi, Paris)
Observation: Flight found: VN Airlines. Price: 800
Thought: I now have all the information needed to answer.
Final Answer: A flight from Hanoi to Paris costs $800 on VN Airlines.

Example 2 (Multi-step with calculations):
User: I want to fly from Hanoi to Paris and stay for 3 nights. Also apply SUMMER promo. What's the total cost?
Thought: This is a multi-step problem. I need to: 1) check flight price, 2) check hotel rate in Paris, 3) check promo code, 4) calculate total cost. Let me start with flight.
Action: search_flights(Hanoi, Paris)
Observation: Flight found: VN Airlines. Price: 800
Thought: Flight costs 800. Now I need to check hotel rates in Paris.
Action: check_hotel(Paris)
Observation: Hotel found: Paris Grand Hotel. Rate: 150 per night.
Thought: Hotel costs 150 per night. Now I need to check the SUMMER promo code.
Action: check_promo(SUMMER)
Observation: Valid code. Discount: 10%
Thought: The discount is 10%. Now I will calculate the total cost for flight (800), hotel (150) for 3 nights, and a 10% discount.
Action: calculate_trip_cost(800, 150, 3, 10)
Observation: Total cost: $1125.00
Thought: I now have all the information needed to answer.
Final Answer: The total cost is $1125.00. Breakdown: Flight ($800) + Hotel for 3 nights ($450) = $1250 base cost, minus 10% discount = $1125.00.
"""

    def run(self, user_input: str) -> str:
        """
        ReAct loop logic:
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        current_prompt = user_input
        steps = 0
        total_tokens = 0
        consecutive_errors = 0

        while steps < self.max_steps:
            # Step 1: Generate LLM response
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            response_text = result["content"]
            total_tokens += result.get("usage", {}).get("total_tokens", 0)

            logger.log_event("AGENT_STEP", {
                "step": steps + 1,
                "response": response_text,
                "usage": result.get("usage", {}),
                "latency_ms": result.get("latency_ms", 0)
            })

            # Step 2: Check for Final Answer
            if "Final Answer:" in response_text:
                final_answer = response_text.split("Final Answer:")[-1].strip()
                
                # Guardrail: Check if final answer is empty
                if not final_answer:
                    consecutive_errors += 1
                    current_prompt = (
                        f"{current_prompt}\n\n"
                        f"{response_text}\n\n"
                        f"Error: Your Final Answer cannot be empty. Please provide a detailed answer."
                    )
                    steps += 1
                    continue

                logger.log_event("AGENT_END", {
                    "steps": steps + 1,
                    "status": "success",
                    "answer": final_answer,
                    "total_tokens": total_tokens
                })
                return final_answer
            
            # Step 3: Parse Action from response
            # Support formats: Action: tool(args) or Action: tool(arg1, arg2)
            action_match = re.search(r"Action:\s*(\w+)\(([^)]*)\)", response_text)
            
            if action_match:
                tool_name = action_match.group(1).strip()
                tool_args = action_match.group(2).strip()
                
                # Step 4: Execute tool
                observation = self._execute_tool(tool_name, tool_args)
                
                logger.log_event("TOOL_CALL", {
                    "step": steps + 1,
                    "tool": tool_name,
                    "args": tool_args,
                    "result": observation
                })
                
                # Guardrail: Check if the tool failed
                if str(observation).startswith("Error:"):
                    consecutive_errors += 1
                    logger.log_event("AGENT_RETRY", {
                        "step": steps + 1,
                        "reason": "Tool execution failed",
                        "error_msg": observation
                    })
                else:
                    consecutive_errors = 0  # Reset on successful execution
                
                # Infinite loop guardrail for tool errors
                if consecutive_errors >= 3:
                    logger.log_event("AGENT_ERROR", {
                        "step": steps + 1,
                        "error": "Too many consecutive tool errors. Aborting to save tokens."
                    })
                    return f"Error: Agent encountered too many consecutive tool errors and was aborted. Last error: {observation}"

                # Step 5: Append observation to prompt for next iteration
                current_prompt = (
                    f"{current_prompt}\n\n"
                    f"{response_text}\n"
                    f"Observation: {observation}\n"
                )
            else:
                consecutive_errors += 1
                
                # Infinite loop guardrail
                if consecutive_errors >= 3:
                    logger.log_event("AGENT_ERROR", {
                        "step": steps + 1,
                        "error": "Too many consecutive format errors. Aborting to save tokens."
                    })
                    return "Error: Agent got stuck in an infinite format loop and was aborted."
                # LLM did not output a valid Action - log parse error
                logger.log_event("PARSE_ERROR", {
                    "step": steps + 1,
                    "response": response_text
                })
                # Ask the LLM to correct its format
                current_prompt = (
                    f"{current_prompt}\n\n"
                    f"{response_text}\n\n"
                    f"Error: Could not parse your Action. "
                    f"Please use the EXACT format: Action: tool_name(arguments)\n"
                    f"Available tools: {', '.join([t['name'] for t in self.tools])}"
                )
            
            steps += 1
        
        # Max steps reached without Final Answer
        logger.log_event("AGENT_END", {
            "steps": steps,
            "status": "max_steps_reached",
            "total_tokens": total_tokens
        })
        return "I was unable to find a complete answer within the allowed number of steps. Please try rephrasing your question."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Execute a tool by name with the given arguments.
        Dynamically calls the tool's function with parsed arguments.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                try:
                    if args:
                        # Parse arguments: split by comma and clean up
                        parsed_args = [a.strip().strip("'\"") for a in args.split(",")]
                        result = tool['function'](*parsed_args)
                    else:
                        result = tool['function']()
                    return str(result)
                except TypeError as e:
                    logger.log_event("TOOL_ERROR", {
                        "tool": tool_name,
                        "args": args,
                        "error": f"Argument error: {str(e)}"
                    })
                    return f"Error calling {tool_name}: Wrong number or type of arguments. {str(e)}"
                except Exception as e:
                    logger.log_event("TOOL_ERROR", {
                        "tool": tool_name,
                        "args": args,
                        "error": str(e)
                    })
                    return f"Error executing {tool_name}: {str(e)}"
        
        available_tools = [t['name'] for t in self.tools]
        logger.log_event("TOOL_NOT_FOUND", {
            "tool": tool_name,
            "available": available_tools
        })
        return f"Error: Tool '{tool_name}' not found. Available tools: {', '.join(available_tools)}"
