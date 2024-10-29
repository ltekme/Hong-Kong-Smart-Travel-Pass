from chat_llm import Chat
from colorama import Fore, Style, init

# Initialize colorama
init()

# Define color constants
COLOR_AI = Fore.RED
COLOR_HUMAN = Fore.GREEN
COLOR_OTHER = Fore.BLUE
RESET = Style.RESET_ALL

chatId = "a5d44788-0954-4a26-bc47-7fb7e2466537"

chat = Chat()
chat.get_from_file("./chat_data/" + chatId + ".json")

chatPlayMsg = f"Playing Chat {chatId}"

print("\n" + "="*len(chatPlayMsg))
print(chatPlayMsg)
print("="*len(chatPlayMsg) + "\n")

for message in chat.as_list:
    if message.role == "ai":
        color = COLOR_AI
    elif message.role == "human":
        color = COLOR_HUMAN
    else:
        color = COLOR_OTHER

    print(color + "="*5 + f" {message.role.capitalize()} " + "="*5 + RESET)
    print(color + message.content.text + RESET)
    if message.content.images:
        print(color + "-" * 10 + " Images " + "-" * 10 + RESET)
        for img in message.content.images:
            print(color + "Image(snipped): " + img.data[:10] + RESET)
    print("\n" + "-"*20 + "\n")
