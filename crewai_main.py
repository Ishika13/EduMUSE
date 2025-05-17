from crewai import Agent, Task, Crew
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(temperature=0.3)

summarizer = Agent(
    role="Summarizer",
    goal="Summarize educational content clearly",
    backstory="Expert in compressing topics into short, digestible notes",
    llm=llm,
    verbose=True
)

quiz_maker = Agent(
    role="Quiz Creator",
    goal="Generate accurate multiple-choice questions",
    backstory="Experienced educator skilled in writing quiz questions",
    llm=llm,
    verbose=True
)

task1 = Task(
    description="Summarize the topic: climate change.",
    expected_output="Short summary of climate change in 2–3 sentences.",
    agent=summarizer
)

task2 = Task(
    description="Create 3 MCQs based on the above summary.",
    expected_output="List of 3 MCQs with answers.",
    agent=quiz_maker
)

edu_crew = Crew(
    agents=[summarizer, quiz_maker],
    tasks=[task1, task2],
    verbose=True
)

result = edu_crew.run()
print(result)