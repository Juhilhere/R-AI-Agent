from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import search_tool, wiki_tool, save_tool, save_to_txt
import os

# loads .env file
load_dotenv()

# we are simply defining a simple python class that will specify the type of content
# that we want our llm to generate.
class ResearchResponse(BaseModel):
    topic: str # topic of the research is of type string
    content: str # detailed research content 
    summary: str # brief summary of the research
    sources: list[str] # sources of the research is of type list
    tools_used: list[str] # tools used in the research is of type list

# setup the Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash") # we create "llm" object.
# response = llm.invoke("What is cryogenic engine?") # response is an object.
# print(response.content)

# model setup done

# Setting prompt template
parser = PydanticOutputParser(pydantic_object = ResearchResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",            """
            You are a research assistant that will help generate comprehensive research papers.
            For each query:
            1. Use the search tool to find current information and data
            2. Use the wikipedia tool to get foundational knowledge
            3. Compile a detailed research paper with:
               - An introduction/overview
               - Detailed technical explanations
               - Current developments and applications
               - Future prospects
               - References and citations
            4. Make sure content is at least as long as requested (20,000 words if specified)
            5. Use the save tool to save the final research
            
            Wrap the output in this format and provide no other text\n{format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

tools = [search_tool, wiki_tool, save_tool]
agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
query = input("What can i help you research? ")
raw_response = agent_executor.invoke({"query": query})

try:
    structured_response = parser.parse(raw_response["output"])
    # Get topic for filename
    topic = structured_response.topic.split(':')[0]  # Take first part before colon
    topic = "".join(x for x in topic if x.isalnum() or x in [' ', '-', '_'])  # Remove special chars
    topic = topic.replace(' ', '_')[:50]  # Replace spaces with underscore and limit length
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{topic}_{timestamp}.txt"
    
    # Save the research output
    save_to_txt({
        "topic": structured_response.topic,
        "content": structured_response.content,
        "summary": structured_response.summary,
        "sources": structured_response.sources,
        "tools_used": structured_response.tools_used
    })
    print(f"Research completed and saved to {filename}")
except Exception as e:
    print("Error parsing response:", e)
    print("Raw Response:", raw_response)