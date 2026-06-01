import re
from typing import List, Dict, Any, Optional, Tuple

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgent:
    """
    A simple ReAct-style Agent that follows:
    Thought -> Action -> Observation -> Final Answer.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[Dict[str, str]] = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in self.tools]
        )
        return f"""
You are a ReAct agent. You can solve tasks by thinking and calling tools.

Available tools:
{tool_descriptions}

Rules:
1. Use a tool only when it is useful.
2. Use exactly this action format: Action: tool_name(argument)
3. Do not invent tools. Only use the available tools.
4. After receiving an Observation, continue reasoning.
5. When you have the answer, end with: Final Answer: ...

Output format:
Thought: explain your reasoning briefly.
Action: tool_name(argument)

or:
Thought: explain your reasoning briefly.
Final Answer: final answer to the user.

Example:
Thought: I need to calculate the final price.
Action: calculator(250000 + 18000)

Observation: 268000
Thought: I have the calculated total.
Final Answer: The final price is 268000 VND.
""".strip()

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        scratchpad = ""
        final_answer = ""

        for step in range(1, self.max_steps + 1):
            prompt = self._build_prompt(user_input, scratchpad)
            result = self.llm.generate(prompt, system_prompt=self.get_system_prompt())

            content = result.get("content", "").strip()
            usage = result.get("usage", {})
            latency_ms = result.get("latency_ms", 0)
            provider = result.get("provider", "unknown")

            tracker.track_request(provider, self.llm.model_name, usage, latency_ms)
            logger.log_event(
                "AGENT_STEP",
                {
                    "step": step,
                    "llm_output": content,
                    "latency_ms": latency_ms,
                    "usage": usage,
                },
            )

            final_answer = self._parse_final_answer(content)
            if final_answer:
                logger.log_event("AGENT_END", {"status": "success", "steps": step})
                self.history.append({"user": user_input, "assistant": final_answer})
                return final_answer

            action = self._parse_action(content)
            if not action:
                logger.log_event(
                    "AGENT_PARSE_ERROR",
                    {"step": step, "output": content, "reason": "No valid Action or Final Answer found"},
                )
                scratchpad += f"\n{content}\nObservation: parser_error: Please use Action: tool_name(argument) or Final Answer: ...\n"
                continue

            tool_name, args = action
            observation = self._execute_tool(tool_name, args)
            logger.log_event(
                "TOOL_CALL",
                {"step": step, "tool_name": tool_name, "args": args, "observation": observation},
            )

            scratchpad += f"\n{content}\nObservation: {observation}\n"

        logger.log_event("AGENT_END", {"status": "max_steps_exceeded", "steps": self.max_steps})
        return "I could not complete the task within the allowed number of steps."

    def _build_prompt(self, user_input: str, scratchpad: str) -> str:
        if not scratchpad:
            return f"User question: {user_input}"
        return f"User question: {user_input}\n\nPrevious reasoning:\n{scratchpad}\nContinue from the latest Observation."

    def _parse_action(self, text: str) -> Optional[Tuple[str, str]]:
        match = re.search(r"Action\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)", text, re.DOTALL)
        if not match:
            return None
        tool_name = match.group(1).strip()
        args = match.group(2).strip().strip('"').strip("'")
        return tool_name, args

    def _parse_final_answer(self, text: str) -> str:
        match = re.search(r"Final Answer\s*:\s*(.*)", text, re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()

    def _execute_tool(self, tool_name: str, args: str) -> str:
        for tool in self.tools:
            if tool["name"] == tool_name:
                try:
                    return str(tool["func"](args))
                except Exception as exc:
                    logger.log_event("TOOL_ERROR", {"tool_name": tool_name, "args": args, "error": str(exc)})
                    return f"tool_error: {exc}"
        logger.log_event("TOOL_NOT_FOUND", {"tool_name": tool_name, "args": args})
        return f"tool_not_found: {tool_name}"
