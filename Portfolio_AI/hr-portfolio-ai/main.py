# configuration

import os
# from pathlib import Path
import json
from profile import profile
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("API key kaha hai bhai")

client=Groq(api_key=my_api_key)

model="openai/gpt-oss-120b"

# Profile content as JSON string
profile_json=json.dumps(profile, indent=4)

##############################################################

sys_prompt= f"""

    You are a helpful assistant that explains complex topics in simple terms. use profile's content to answer as it is your only knowledge base. Do not make up any information. If the information is not present in profile.py, respond with "I don't know".

    this is the profile {profile_json}
    """

message_system={
        "role": "system",
        "content": sys_prompt
    }   
messages=[message_system]  


  
def ask_llm(messages, model):
    response=client.chat.completions.create(messages=messages, model=model)
    answer=response.choices[0].message.content
    return answer   


def run_chat():
    #LLM communication loop 
    while True:

        prompt = input("Ask me anything (type 'exit' to quit): ")
        if prompt.lower() == 'exit':
            break

        # prompt = """
        # What language does he know?
        # """
        message={
        "role": "user",
        "content": prompt
            }
        
        messages.append(message)
    
        answer = ask_llm(messages, model)
        print("Answer:", answer)
        messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    run_chat()