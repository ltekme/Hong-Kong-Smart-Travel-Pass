from ChatLLM import ChatRecord, ChatMessage
import copy

# deep copy test
# found bug that object will not be copied when deepcopy is called
new_c = ChatRecord()
new_c.append(ChatMessage("human", "Fuck1"))
new_c.append(ChatMessage("ai", "Fuck1"))
new_c.save_to_file("./data/abc.json")
print(new_c.as_list[-1].content.text)
print(new_c.as_list[-1].role)
new_b = copy.deepcopy(new_c)
print(new_c.as_list[-1].content.text)
print(new_c.as_list[-1].role)
new_b.remove_system_message()
new_b.append(ChatMessage("human", "Fuck2"))
print(new_c.as_list[-1].content.text)
print(new_c.as_list[-1].role)
print(len(new_c.as_list))
print(new_b.as_list[-1].content.text)
print(new_b.as_list[-1].role)
print(len(new_b.as_list))
new_c.append(ChatMessage("human", "Fuck2"))
new_b.remove_last_message()
new_c.save_to_file("./data/af_anc.json")
new_b.save_to_file("./data/fk_abc.json")
