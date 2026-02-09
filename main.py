from agents.agent_connector import new_session_id, reset_session, send_message


def main():
    session_id = new_session_id()

    print("Interactive mode. Type 'exit' or 'quit' to stop.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            reset_session(session_id)
            break

        output, _ = send_message(session_id=session_id, user_message=user_input)

        print(f"Agent: {output}\n")


if __name__ == "__main__":
    main()