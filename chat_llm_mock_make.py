import chat_llm

if __name__ == "__main__":
    chatLLM = chat_llm.Chat(
        system_message_string=(
            "You are a very powerful AI. "
            "Context maybe given to assist the assistant in providing better responses. "
            "For now you and the user is in Hong Kong. "
            "When asked for direction, provide as much details as possible. "
            "Use the google search tool to make sure your response are factical and can be sourced. "
            "You don't know much about the outside word, but with tools you can look up information. "
            "To provide the most accurate resault use the google search too make sure everyting you say are correct. "
            "When responding to the user provide as much contenxt as you can since you may need to answer more queries based on your responds. "
            "output markdown whenever posible, in the Final Answer response"
        )
    )

    chatId = input("Enter Chat ID: ")
    file_path = f"chat_data/{chatId}_overide.json"
    chatLLM.get_from_file(file_path)
    
    if chatLLM.as_list[-1].role == "human":
        current_role = "ai"
    elif chatLLM.as_list[-1].role == "ai" or chatLLM.as_list[-1].role == "system":
        current_role = "human"

    while True:
        print("Existing Messages: ")
        for message in chatLLM.as_list_of_lcMessages:
            message.pretty_print()

        msg = input(f"{current_role}: ")
        if msg == "EXIT":
            chatLLM.save_to_file(file_path)
            break
        if not msg:
            continue

        chatLLM.append(chat_llm.Message(current_role,
                                        chat_llm.MessageContent(msg)
                                        ))
        if current_role == "human":
            current_role = "ai"
        else:
            current_role = "human"
