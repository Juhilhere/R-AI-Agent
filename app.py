from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import search_tool, wiki_tool, save_tool, save_to_txt
import os

app = Flask(__name__)

# loads .env file
load_dotenv()

class ResearchResponse(BaseModel):
    topic: str
    content: str
    summary: str
    sources: list[str]
    tools_used: list[str]

def setup_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    parser = PydanticOutputParser(pydantic_object=ResearchResponse)
    
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
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
            """
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]).partial(format_instructions=parser.get_format_instructions())

    tools = [search_tool, wiki_tool, save_tool]
    agent = create_tool_calling_agent(llm=llm, prompt=prompt, tools=tools)
    return AgentExecutor(agent=agent, tools=tools, verbose=True), parser

agent_executor, parser = setup_agent()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/research', methods=['POST'])
def research():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        raw_response = agent_executor.invoke({"query": query})
        structured_response = parser.parse(raw_response["output"])
        
        # Generate filename
        topic = structured_response.topic.split(':')[0]
        topic = "".join(x for x in topic if x.isalnum() or x in [' ', '-', '_'])
        topic = topic.replace(' ', '_')[:50]
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{topic}_{timestamp}.txt"
        
        # Save research
        save_to_txt({
            "topic": structured_response.topic,
            "content": structured_response.content,
            "summary": structured_response.summary,
            "sources": structured_response.sources,
            "tools_used": structured_response.tools_used
        }, filename)
        
        return jsonify({
            'message': f'Research completed and saved to {filename}',
            'filename': filename,
            'summary': structured_response.summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True)
