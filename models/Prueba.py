#models/Prueba.py
from pydantic import BaseModel, validator
from typing import Optional
import re


class Prueba(BaseModel):
    username: str
    name: str
    email: str
    active: Optional[int] = 1
    
    
    