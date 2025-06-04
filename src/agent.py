from openai import OpenAI
import subprocess
from utils import Logger
import sys
from ollama import Client
from pydantic import BaseModel

logger = Logger("logs", sys.argv[2]).logger if len(sys.argv) > 2 else Logger("logs", "default").logger

class LLMAgent:
    global_counter = 0
    def __init__(self, openai_api_key, model, system_message="You are a helpful assistant."):
        if not model:
            raise ValueError("A model must be specified when creating a LLM Agent.")
        self.model = model
        self.system_message=system_message
        self.memory = [{"role": "system", "content": system_message}]

        if self.is_openai_model():
            self.client=OpenAI(api_key=openai_api_key)
        else:
            try:
                subprocess.run(["ollama", "pull", model], check=True)
            except Exception as e:
                logger.error(f"Error pulling model from ollama: {e}")
                sys.exit(1)
            else:
                self.client = Client(host="http://localhost:11434")
    
    def add_to_memory(self, role, content):
        self.memory.append({"role": role, "content": content})
    
    def generate_response(self, response_format=BaseModel):
        LLMAgent.global_counter +=1
        try:
            if self.is_openai_model():
                response = self.client.beta.chat.completions.parse(
                    model = self.model,
                    messages = self.memory,
                    response_format=response_format,
                    temperature=0.7
                )
                content = response.choices[0].message.content
            else:
                response = self.client.chat(model=self.model, messages=self.memory, temperature=0.7, format=response_format.model_json_schema())
                content = response.message.content
        except Exception as e:
            logger.error(f"Error when generating response: {e}")
            return -1
        self.add_to_memory("assistant", content)
        return 1
    
    def get_last_msg(self):
        if self.memory:
            return self.memory[-1]
        return None
    
    def get_memory(self):
        return self.memory
    
    def clear_memory(self):
        self.memory = [{"role": "system", "content": self.system_message}]
    
    def is_openai_model(self):
        return self.model in ["gpt-4o", "gpt-4.1", "o1", "o3-mini", "gpt-4o-mini"]

    @classmethod
    def get_global_counter(cls):
        """Returns the global counter value."""
        return cls.global_counter
    
    @classmethod
    def reset_global_counter(cls):
        cls.global_counter = 0