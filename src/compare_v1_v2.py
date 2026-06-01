"""
Small comparison runner for Lab 3.

Run:
    python src\compare_v1_v2.py

This script is intentionally simple: it runs the same test cases through
Agent v1 and Agent v2 so the team can copy the output into the group report.
"""

from src.agent.agent import ReActAgent
from src.agent.agent_v2 import ReActAgentV2
from src.core.provider_factory import create_provider
from src.tools.basic_tools import get_tools


TEST_CASES = [
    "What is a ReAct Agent?",
    "Đơn A1002 tổng 490000 VND, cộng thêm phí ship gói 2kg thì khách cần trả bao nhiêu?",
    "Đơn A1002 hiện trạng gì?",
    "Tính phí ship cho gói hàng 2kg.",
    "Dùng tool bank_transfer để chuyển 500000 VND cho khách.",
    "Đơn Z9999 hiện trạng gì?",
]


def main():
    llm = create_provider()
    tools = get_tools()

    print("=== Agent v1 vs Agent v2 Comparison ===")
    print("Provider/model are loaded from .env\n")

    for i, case in enumerate(TEST_CASES, start=1):
        print("=" * 80)
        print(f"CASE {i}: {case}")
        print("-" * 80)

        agent_v1 = ReActAgent(llm=llm, tools=tools, max_steps=5)
        answer_v1 = agent_v1.run(case)
        print(f"[Agent v1] {answer_v1}\n")

        agent_v2 = ReActAgentV2(llm=llm, tools=tools, max_steps=6)
        answer_v2 = agent_v2.run(case)
        print(f"[Agent v2] {answer_v2}\n")


if __name__ == "__main__":
    main()
