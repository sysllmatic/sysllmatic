from dotenv import load_dotenv
from utils import Logger
import sys
import os
from pydantic import BaseModel
import json
from jinja2 import Environment, FileSystemLoader

logger = Logger("logs", sys.argv[2]).logger
load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
    
env = Environment(loader=FileSystemLoader(f"{USER_PREFIX}/src/llm/llm_prompts"))

class Feedback(BaseModel):
    feedback: str

def evaluator_llm(evaluator_feedback_data, llm_assistant):

    #extract original
    original_source_code = evaluator_feedback_data["original"]["source_code"]

    current_source_code = evaluator_feedback_data["current"]["source_code"]  
    avg_speedup = evaluator_feedback_data["current"]["avg_speedup"]

    if "flame_report" in evaluator_feedback_data:
        flame_report = evaluator_feedback_data["flame_report"]
    else:
        flame_report = ""
            
    template = env.get_template("evaluator_prompt.jinja")
    data = {
        "original_source_code": original_source_code,
        "current_source_code": current_source_code,
        "avg_speedup": avg_speedup,
        "flame_report": flame_report
    }
    
    prompt = template.render(data)

    llm_assistant.add_to_memory("user", prompt)
    llm_assistant.generate_response(response_format=Feedback)
    response = llm_assistant.get_last_msg()

    try:
        if llm_assistant.is_openai_model():
            content_dict = json.loads(response["content"])
            feedback = content_dict["feedback"]
        else:
            feedback = Feedback.model_validate_json(response["content"]).feedback
        return feedback
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return