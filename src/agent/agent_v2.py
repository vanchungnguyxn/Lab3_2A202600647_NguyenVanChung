import json
import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgentV2:
    """
    Improved ReAct Agent for Lab 3.

    Improvements over v1:
    - Stricter system prompt and tool contract.
    - Robust parser for normal Action format and simple JSON action format.
    - Parser-error recovery through Observation feedback.
    - Tool allowlist and safe TOOL_NOT_FOUND handling.
    - max_steps termination guard.
    - Structured telemetry with agent_version='v2'.
    """

    def __init__(
        self,
        llm: LLMProvider,
        tools: List[Dict[str, Any]],
        max_steps: int = 6,
    ):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.tool_map = {tool["name"]: tool for tool in tools}
        self.tool_names = sorted(self.tool_map.keys())

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [
                f"- {tool['name']}: {tool['description']}"
                for tool in self.tools
            ]
        )

        return f"""
You are ReAct Agent v2, a careful tool-using assistant.

Available tools:
{tool_descriptions}

Strict rules:
1. Use tools only when they are necessary.
2. Never invent tools. Available tools are: {", ".join(self.tool_names)}.
3. Never claim that you performed an action unless a tool observation confirms it.
4. For unavailable or high-risk tools such as bank_transfer, refund, delete_account, or payment, refuse safely.
5. If an order lookup returns order_not_found, do not hallucinate order details.
6. Stop as soon as you have enough information.

You must respond in exactly one of these formats:

Format A - Call a tool:
Thought: brief reason for the next action.
Action: tool_name(argument)

Format B - Final answer:
Thought: brief reason why the task is complete.
Final Answer: answer to the user

Do not wrap Action in Markdown.
Do not call more than one tool in a single step.
Do not output JSON unless you cannot follow the Action format.
""".strip()

    def run(self, user_input: str) -> str:
        logger.log_event(
            "AGENT_START",
            {
                "agent_version": "v2",
                "input": user_input,
                "model": self.llm.model_name,
                "max_steps": self.max_steps,
                "tools": self.tool_names,
            },
        )

        scratchpad = ""

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
                    "agent_version": "v2",
                    "step": step,
                    "llm_output": content,
                    "latency_ms": latency_ms,
                    "usage": usage,
                },
            )

            final_answer = self._parse_final_answer(content)
            if final_answer:
                logger.log_event(
                    "AGENT_END",
                    {
                        "agent_version": "v2",
                        "status": "success",
                        "steps": step,
                    },
                )
                return final_answer

            action = self._parse_action(content)
            if not action:
                observation = (
                    "parser_error: Output must be exactly "
                    "Action: tool_name(argument) or Final Answer: ..."
                )
                logger.log_event(
                    "AGENT_PARSE_ERROR",
                    {
                        "agent_version": "v2",
                        "step": step,
                        "output": content,
                        "reason": "No valid Action or Final Answer found",
                    },
                )
                scratchpad += f"\n{content}\nObservation: {observation}\n"
                continue

            tool_name, args = action

            if tool_name not in self.tool_map:
                observation = (
                    f"tool_not_found: {tool_name}. "
                    f"Available tools: {', '.join(self.tool_names)}"
                )
                logger.log_event(
                    "TOOL_NOT_FOUND",
                    {
                        "agent_version": "v2",
                        "step": step,
                        "tool_name": tool_name,
                        "args": args,
                        "available_tools": self.tool_names,
                    },
                )
                scratchpad += f"\n{content}\nObservation: {observation}\n"
                continue

            observation = self._execute_tool(tool_name, args)
            logger.log_event(
                "TOOL_CALL",
                {
                    "agent_version": "v2",
                    "step": step,
                    "tool_name": tool_name,
                    "args": args,
                    "observation": observation,
                },
            )

            scratchpad += f"\n{content}\nObservation: {observation}\n"

        logger.log_event(
            "AGENT_END",
            {
                "agent_version": "v2",
                "status": "max_steps_exceeded",
                "steps": self.max_steps,
            },
        )
        return (
            "I could not complete the task within the allowed number of steps. "
            "Please simplify the request or provide more information."
        )

    def _build_prompt(self, user_input: str, scratchpad: str) -> str:
        if not scratchpad:
            return f"User question: {user_input}"

        return (
            f"User question: {user_input}\n\n"
            f"Previous reasoning and observations:\n{scratchpad}\n"
            "Continue from the latest Observation. "
            "Use Final Answer if the task is complete."
        )

    def _parse_final_answer(self, text: str) -> str:
        cleaned = self._clean_model_output(text)
        match = re.search(r"Final Answer\s*:\s*(.*)", cleaned, re.DOTALL | re.IGNORECASE)
        if not match:
            return ""
        return match.group(1).strip()

    def _parse_action(self, text: str) -> Optional[Tuple[str, str]]:
        cleaned = self._clean_model_output(text)

        # Preferred ReAct format: Action: tool_name(argument)
        match = re.search(
            r"Action\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)",
            cleaned,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            tool_name = match.group(1).strip()
            args = match.group(2).strip().strip('"').strip("'")
            return tool_name, args

        # Backup parser for simple JSON action format:
        # {"action": "calculator", "input": "1 + 1"}
        json_obj = self._extract_json_object(cleaned)
        if json_obj:
            action_name = json_obj.get("action") or json_obj.get("tool") or json_obj.get("tool_name")
            action_input = json_obj.get("input") or json_obj.get("argument") or json_obj.get("args")
            if action_name and action_input is not None:
                return str(action_name).strip(), str(action_input).strip()

        return None

    def _clean_model_output(self, text: str) -> str:
        cleaned = text.strip()

        # Remove fenced code blocks while keeping their content.
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        return cleaned.strip()

    def _extract_json_object(self, text: str) -> Optional[Dict[str, Any]]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        candidate = text[start : end + 1]
        try:
            data = json.loads(candidate)
        except Exception:
            return None

        if isinstance(data, dict):
            return data
        return None

    def _execute_tool(self, tool_name: str, args: str) -> str:
        tool = self.tool_map[tool_name]
        try:
            return str(tool["func"](args))
        except Exception as exc:
            logger.log_event(
                "TOOL_ERROR",
                {
                    "agent_version": "v2",
                    "tool_name": tool_name,
                    "args": args,
                    "error": str(exc),
                },
            )
            return f"tool_error: {exc}"
