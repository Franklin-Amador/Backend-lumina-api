from pydantic import BaseModel, field_validator
from typing import Optional
import re

from utils.globalf import validate_sql_injection

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str]

    @field_validator('password')
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if not re.search("[0-9]", v):
            raise ValueError('Password must contain at least one number')
        if not re.search("[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search("[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if re.search(r'(012|123|234|345|456|567|678|789)', v):
            raise ValueError('Password cannot contain a sequence of 3 consecutive numbers')
        return v
    
    @field_validator('name')
    def name_length(cls, v):
        if validate_sql_injection(v):
            raise ValueError('Invalid name')
        return v
    

class MailSend(BaseModel):
    email: str
    password: Optional[str]
    
    