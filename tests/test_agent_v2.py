from src.agent.agent_v2 import ReActAgentV2
from src.tools.basic_tools import get_tools


class FakeLLM:
    model_name = "fake-llm"

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.i = 0

    def generate(self, prompt, system_prompt=None):
        if self.i >= len(self.outputs):
            content = "Thought: done.\nFinal Answer: fallback"
        else:
            content = self.outputs[self.i]
            self.i += 1
        return {
            "content": content,
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            "latency_ms": 1,
            "provider": "fake",
        }

    def stream(self, prompt, system_prompt=None):
        yield ""


def test_agent_v2_json_action_parser():
    llm = FakeLLM([
        '{"action":"calculator","input":"490000 + 25000"}',
        "Thought: I have the result.\nFinal Answer: 515000",
    ])
    agent = ReActAgentV2(llm=llm, tools=get_tools(), max_steps=3)
    assert agent.run("calculate") == "515000"


def test_agent_v2_parser_recovery():
    llm = FakeLLM([
        "I should calculate this, but I used a wrong format.",
        "Thought: retry with valid format.\nAction: calculator(1 + 1)",
        "Thought: done.\nFinal Answer: 2",
    ])
    agent = ReActAgentV2(llm=llm, tools=get_tools(), max_steps=4)
    assert agent.run("calculate") == "2"


def test_agent_v2_tool_not_found_recovery():
    llm = FakeLLM([
        "Thought: try unavailable tool.\nAction: bank_transfer(500000)",
        "Thought: the tool is unavailable.\nFinal Answer: I cannot perform bank transfer because the tool is not available.",
    ])
    agent = ReActAgentV2(llm=llm, tools=get_tools(), max_steps=3)
    assert "cannot perform bank transfer" in agent.run("transfer money")
