from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool
from datetime import datetime
import os

def save_to_txt(data: dict, filename: str = None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create a filename based on the topic and timestamp if not provided
    if filename is None:
        # Get topic and sanitize it for filename use
        topic = data.get('topic', 'Research').split(':')[0]  # Take first part before colon
        topic = "".join(x for x in topic if x.isalnum() or x in [' ', '-', '_'])  # Remove special chars
        topic = topic.replace(' ', '_')[:50]  # Replace spaces with underscore and limit length
        filename = f"{topic}_{timestamp}.txt"
    
    # Check if running on PythonAnywhere
    if 'PYTHONANYWHERE_SITE' in os.environ:
        # Use the appropriate directory for PythonAnywhere
        filename = os.path.join('/home/YourUsername/research_papers', filename)
    
    formatted_text = f"--- Research Output ---\nTimestamp: {timestamp}\n\n"
    
    # Add topic and content sections
    formatted_text += f"Research Topic: {data.get('topic', '')}\n\n"
    formatted_text += data.get('content', data.get('summary', '')) + "\n\n"  # Try content first, fall back to summary
    
    # Add sources if present
    if data.get('sources'):
        formatted_text += "Sources:\n"
        for source in data['sources']:
            formatted_text += f"- {source}\n"
        formatted_text += "\n"
    
    # Add tools used if present
    if data.get('tools_used'):
        formatted_text += "Tools Used:\n"
        for tool in data['tools_used']:
            formatted_text += f"- {tool}\n"
        formatted_text += "\n"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(formatted_text)
    
    return f"Data successfully saved to {filename}"

save_tool = Tool(
    name="save_text_to_file",
    func=save_to_txt,
    description="Saves structured research data to a text file.",
)

search = DuckDuckGoSearchRun()
search_tool = Tool(
    name="search",
    func=search.run,
    description="Search the web for information",
)

api_wrapper = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=20000)
wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)
