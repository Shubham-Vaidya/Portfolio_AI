import os
# from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("API key kaha hai bhai")

client=Groq(api_key=my_api_key)

model="openai/gpt-oss-120b"

prompt = input("you:")
message={
    "role": "user",
    "content": prompt
}
sys_prompt= """

You are a helpful assistant that explains complex topics in simple terms.
"""

message_system={
    "role": "system",
    "content": sys_prompt
}
messages=[message_system, message]

response=client.chat.completions.create(messages=messages, model=model)
answer=response.choices[0].message.content
print(answer)