from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.tools.basic_tools import get_tools, calculator, order_lookup, shipping_fee


class FakeProvider(LLMProvider):
    def __init__(self):
        super().__init__("fake-model")
        self.calls = 0

    def generate(self, prompt, system_prompt=None):
        self.calls += 1
        if self.calls == 1:
            content = "Thought: I need to calculate.\nAction: calculator(2 + 3)"
        else:
            content = "Thought: I know the result.\nFinal Answer: 5"
        return {
            "content": content,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "latency_ms": 1,
            "provider": "fake",
        }

    def stream(self, prompt, system_prompt=None):
        yield ""


def test_tools():
    assert calculator("2 + 3") == "5"
    assert "shipping" in order_lookup("A1002")
    assert shipping_fee("2") == "25000 VND"


def test_react_agent_loop():
    agent = ReActAgent(llm=FakeProvider(), tools=get_tools(), max_steps=3)
    assert agent.run("What is 2 + 3?") == "5"
