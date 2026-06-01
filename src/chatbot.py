from src.core.provider_factory import create_provider


SYSTEM_PROMPT = """
You are a simple baseline chatbot.

You answer directly using only the text provided by the user and your general language ability.
You do NOT have access to tools.
You cannot call order_lookup, shipping_fee, calculator, database, browser, or external APIs.

If the user asks for order status, shipping fee, or exact calculation that requires tools,
you should answer that you cannot verify it without tool access.
"""


def main():
    llm = create_provider()

    print("Baseline Chatbot is ready. Type 'exit' to quit.")
    print("Note: This chatbot does NOT use tools.\n")

    while True:
        user_input = input("User: ").strip()

        if user_input.lower() == "exit":
            break

        response = llm.generate(
            prompt=user_input,
            system_prompt=SYSTEM_PROMPT,
        )

        print(f"Chatbot: {response['content']}\n")


if __name__ == "__main__":
    main()