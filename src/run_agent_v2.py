from src.agent.agent_v2 import ReActAgentV2
from src.core.provider_factory import create_provider
from src.tools.basic_tools import get_tools


def main():
    llm = create_provider()
    agent = ReActAgentV2(llm=llm, tools=get_tools(), max_steps=6)

    print("ReAct Agent v2 is ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        answer = agent.run(user_input)
        print("Agent v2:", answer)


if __name__ == "__main__":
    main()
