# src/anubis/utils/model

import logging
logger = logging.getLogger(__name__)


from typing import Optional

from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()

""" TODO: Prevent Rate Limiting and Token Limiting Errors and Handle Message Failures """

def init_model(tools=[], 
               tool_choice: str = "auto", 
               response_format = None, 
               image_to_text_model: bool = True):
    
    # context = GlobalContext()
    model_name = os.getenv("MODEL")
    base_url = os.getenv("LLAMA_API_BASE_URL")
    api_key = os.getenv("LLAMA_API_KEY")
    dev = os.getenv("DEV")

    logger.info(f"dev: {dev}")
    logger.info(f"base_url: {base_url}")
    logger.info(f"model_name: {model_name}")

    # if dev == 'TRUE':
    from langchain_openai import ChatOpenAI
    

    if response_format is None:
        model = ChatOpenAI(
                    model = model_name,
                    base_url = base_url,
                    temperature=0.1,
                    top_p=0.1,
                    api_key = api_key,
                ).bind_tools(
                    # method='json_schema', 
                    tools=tools, 
                    tool_choice=tool_choice, # auto: zero or more tools
                    # strict=True, # model output will be guaranteed to match the schema
                    # include_raw=True # model response (JSON e.g.) and the parsed response (Pydantic e.g.) will be returned
                )
    else: 
        model = ChatOpenAI(
            model = model_name,
            base_url = base_url,
            temperature=0.1,
            top_p=0.1,
            api_key = api_key,
        )
        model = model.with_structured_output(schema=response_format)
    # else: 
    #     from langchain_together import ChatTogether
    #     model = ChatTogether(model=model_name, temperature=0.1)
    return model

