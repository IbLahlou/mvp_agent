from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from googletrans import Translator
import logging
from src.services.prompt_engineering import PromptEngineering  # Import the class

router = APIRouter(tags=["agent"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

translator = Translator()
prompt_engine = PromptEngineering()  # Create instance

# [Keep all the existing Enum and Model classes...]


# [Keep the remaining GET endpoints as they are...]