import os

from langchain_core.messages import HumanMessage
from langchain_google_vertexai import ChatVertexAI

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

from google.oauth2.service_account import Credentials

# Define a new graph
workflow = StateGraph(state_schema=MessagesState)


credentialsFiles = list(filter(lambda f: f.startswith(
    'gcp_cred') and f.endswith('.json'), os.listdir('.')))
credentials = Credentials.from_service_account_file(
    credentialsFiles[0])

llm = ChatVertexAI(
    model="gemini-1.5-pro",
    temperature=0.9,
    max_tokens=4096,
    timeout=None,
    max_retries=2,
    credentials=credentials,
    project=credentials.project_id,
    region="us-central1",
)

# Define the function that calls the model
def call_model(state: MessagesState):
    response = llm.invoke(state["messages"])
    # Update message history with response:
    return {"messages": response}


# Define the (single) node in the graph
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Add memory
app = workflow.compile()

inputMessages = []

while True:
    msg = input("Enter your message: ")
    if msg == "exit":
        break
    inputMessages.append(HumanMessage(msg))
    response = app.invoke({"messages": inputMessages}, {
                          "configurable": {"thread_id": "abc123"}})
    print(response["messages"][-1].content)
    inputMessages.append(response["messages"][-1])
