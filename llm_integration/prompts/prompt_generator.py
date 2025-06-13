from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
from extractors.tool_extractor import ToolExtractor
from groq import Groq
import asyncio
import os


class PromptGenerator:
     
    def __init__(self, mcp_base_url: str = "http://localhost:8003"):
        """
        Initialize the PromptGenerator with the base URL of the MCP server.
        
        Args:
            mcp_base_url (str): The base URL of the MCP server.
        """
        self.tool_extractor = ToolExtractor(mcp_base_url=mcp_base_url)
        self.client = Groq()
    
    async def generate_description(self, server_name: str):
        
        prompt_template_str = """Generate a concise and comprehensive description of **{server_name}** as a tool, detailing its **core capabilities** and the **specific functionalities** it offers. The description should be detailed enough to capture the essence of the tool and its uses, yet direct to facilitate the creation of embeddings.
            Include the following information:
            1.  **General overview of {server_name}**: What it is and its primary purpose.

            2.  **Key use cases**: Examples of scenarios where {server_name} is indispensable (e.g., version control, team collaboration, software project management).

            3.  **Available functionalities**: Mention the following specific tools/actions that can be performed with {server_name}:

            {tools}

            Ensure the description is coherent, flows naturally, and that the functionalities are integrated seamlessly into the text, highlighting their purpose.

            Return it as a json object with the following structure:
            ```json
            {{
                "{server_name}": "Your detailed description here"
            }}
            ```"""
        
        prompt_template = PromptTemplate(template=prompt_template_str,
                                         input_variables=["server_name","tools"])
        tools = await self.tool_extractor.get_tools_names(server_name=server_name)
        
        formatted_prompt = prompt_template.format(
            server_name=server_name,
            tools=tools  
        )
        
        completion = self.client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": formatted_prompt,
            }],
            temperature=1,
            max_completion_tokens=2048,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        return completion
    
async def test_prompt_generator():
    generator = PromptGenerator()

    # Test with Google Maps
    print("Testing Google Maps:")
    Maps_description = await generator.generate_description("google-maps")
    print(Maps_description)
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    # Run the asynchronous test function
    asyncio.run(test_prompt_generator())