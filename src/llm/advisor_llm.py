from dotenv import load_dotenv
from pydantic import BaseModel
from utils import Logger
from scripts.read_pattern_cat import get_patterns
import json
import sys
import os
from jinja2 import Environment, FileSystemLoader

logger = Logger("logs", sys.argv[2]).logger
load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

env = Environment(loader=FileSystemLoader(f"{USER_PREFIX}/src/llm/llm_prompts"))
optimization_patterns = f"{USER_PREFIX}/pattern_catalog/optimization_patterns.xlsx"
#with open(f"{USER_PREFIX}/src/llm/llm_prompts/advisor_prompt.txt", "r") as file:
#    advisor_prompt = file.read()

def filter_patterns(llm_assistant, code, ast, flame_report):
    class Pattern(BaseModel):
        type: str
        pattern_name: str
        pattern_description: str
        pattern_example: str
        optimized_metrics: str
        detection: str
        rank: str
        reasoning: str

    class PatternSelection(BaseModel):
        patterns: list[Pattern]

    patterns = get_patterns(file_path=optimization_patterns)
    #logger.info(f"Unformatted patterns: {patterns}")

    template = env.get_template("advisor_prompt.jinja")
    data = {
        "code": code,
        "ast": ast,
        "flame_report": flame_report,
        "patterns": patterns,
    }
    prompt = template.render(data)

    logger.info(f"filter patterns: Advisor LLM filtering patterns ....")
    llm_assistant.add_to_memory("user", prompt)
    if llm_assistant.generate_response(response_format=PatternSelection) != 1:
        return -1
    response = llm_assistant.get_last_msg()
    if response == None:
        return -1
    logger.info(response)

    try:
        if llm_assistant.is_openai_model() or llm_assistant.is_genai_studio():
            content_dict = json.loads(response["content"])
            patterns = "\n".join(
                f"Pattern Type:{entry['type']}\nPattern Name:{entry['pattern_name']}\nDescription:{entry['pattern_description']}\nExample:{entry['pattern_example']}\nOptimized Metrics:{'optimized_metrics'}\nDetection:{entry['detection']}\nRank:{entry['rank']}\nReasoning:{entry['reasoning']}"
                for entry in content_dict["patterns"]
            )
        else:
            patterns = "\n".join(
                f"Pattern Type:{entry['type']}\nPattern Name:{entry['pattern_name']}\nDescription:{entry['pattern_description']}\nExample:{entry['pattern_example']}\nOptimized Metrics:{'optimized_metrics'}\nDetection:{entry['detection']}\nRank:{entry['rank']}\nReasoning:{entry['reasoning']}"
                for entry in PatternSelection.model_validate_json(response["content"]).patterns
            )
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return

    return patterns
