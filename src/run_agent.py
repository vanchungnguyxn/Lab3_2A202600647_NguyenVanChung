from src.agent.agent import ReActAgent
from src.core.provider_factory import create_provider
from src.tools.basic_tools import get_tools


def main():
    llm = create_provider()
    agent = ReActAgent(llm=llm, tools=get_tools(), max_steps=5)

    print("ReAct Agent is ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        answer = agent.run(user_input)
        print("Agent:", answer)


if __name__ == "__main__":
    main()
