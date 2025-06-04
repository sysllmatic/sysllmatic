from dotenv import load_dotenv
from pydantic import BaseModel
import sys
from utils import Logger
import json
import os
from jinja2 import Environment, FileSystemLoader

logger = Logger("logs", sys.argv[2]).logger
load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

env = Environment(loader=FileSystemLoader(f"{USER_PREFIX}/src/llm/llm_prompts"))

def llm_optimize(code, llm_assistant, evaluator_feedback=None, ast=None, flame_report=None, optimization_patterns=None):
    class OptimizationReasoning(BaseModel):
        analysis: str
        optimization_opportunities: str
        selected_strategy: str
        final_code: str
        
    # logger.info(f"flamegraph: {flame_report}")

    if not evaluator_feedback or evaluator_feedback == "":
        template = env.get_template("generator_prompt.jinja")
        data = {
            "code": code,
            "ast": ast,
            "flame_report": flame_report,
            "optimization_patterns": optimization_patterns,
        }
        prompt = template.render(data)
    else:
        template = env.get_template("generator_feedback_prompt.jinja")
        data = {
            "code": code,
            "ast": ast,
            "flame_report": flame_report,
            "optimization_patterns": optimization_patterns,
            "evaluator_feedback": evaluator_feedback,
        }
        prompt = template.render(data)    

    logger.info(f"llm_optimize: Generator LLM Optimizing ....")

    logger.info(f"Generator prompt: {prompt}")

    llm_assistant.add_to_memory("user", prompt)
    llm_assistant.generate_response(OptimizationReasoning)

    response = llm_assistant.get_last_msg()
    logger.info(response)
    
    try:
        if llm_assistant.is_openai_model():
            content_dict = json.loads(response["content"])
            final_code = content_dict["final_code"]
        else:
            final_code = OptimizationReasoning.model_validate_json(response["content"]).final_code
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return

    if final_code == "":
        logger.error("Error in llm completion")
        return
    
    return final_code

def handle_error(error_message, llm_assistant):
    class ErrorReasoning(BaseModel):
        analysis: str
        final_code: str
    
    template = env.get_template("error_prompt.jinja")
    data = {
        "error_message": error_message
    }
    error_prompt = template.render(data)
    logger.info(f"Prompt: {error_prompt}")
    logger.info(f"llm_optimize: Generator LLM Handling Error ....")
    
    llm_assistant.add_to_memory("user", error_prompt)
    llm_assistant.generate_response(ErrorReasoning)
    response = llm_assistant.get_last_msg()

    try:
        if llm_assistant.is_openai_model():
            content_dict = json.loads(response["content"])
            final_code = content_dict["final_code"]
        else:
            final_code = ErrorReasoning.model_validate_json(response["content"]).final_code
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return
        
    if final_code == "":
        logger.error("Error in llm completion")
        return

    return final_code