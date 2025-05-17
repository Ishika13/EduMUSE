from langchain.agents import Tool, initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory


def summarize_topic(input_text: str) -> str:
    return f"Summary: Climate change refers to long-term shifts in temperatures and weather patterns. ({input_text[:20]})"

def generate_quiz(summary: str) -> str:
    return """1. What does climate change refer to?
A. Short-term weather
B. Ocean currents
C. Long-term shifts in temperature
Answer: C"""

summarizer_tool = Tool(
    name="SummarizerTool",
    func=summarize_topic,
    description="Summarizes a given topic or paragraph."
)

quiz_tool = Tool(
    name="QuizTool",
    func=generate_quiz,
    description="Creates 3 MCQs from a summary."
)

llm = ChatOpenAI(temperature=0.3)  
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent = initialize_agent(
    tools=[summarizer_tool, quiz_tool],
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

query = "Please summarize the topic 'climate change' and create a quiz for students."
response = agent.run(query)
print(response)