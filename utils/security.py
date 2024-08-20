#utils/security.py

import os
import secrets
import hashlib
import base64
import jwt

from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from dotenv import load_dotenv
from jwt import PyJWTError
from functools import wraps

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

def generate_pkce_verifier():
    return secrets.token_urlsafe(32)

def generate_pkce_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')

# ! token V2
def create_jwt_token(email: str, id_estado: int, rol_id: int, nombre: str, apellido: str):
    expiration = datetime.utcnow() + timedelta(hours=1)  # El token expira en 1 hora
    token = jwt.encode(
        {
            "email": email,
            "exp": expiration,
            "id_estado": id_estado,
            "rol_id": rol_id,
            "nombre": nombre,
            "apellido": apellido,
            "iat": datetime.utcnow()
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    return token

# ! validate V3

def validate(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get('request')
        if not request:
            raise HTTPException(status_code=400, detail="Request object not found")

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=403, detail="Authorization header missing")

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            email = payload.get("email")
            expired = payload.get("exp")
            id_estado = payload.get("id_estado")
            rol_id = payload.get("rol_id")
            nombre = payload.get("nombre")
            apellido = payload.get("apellido")

            if email is None or expired is None or id_estado is None:
                raise HTTPException(status_code=403, detail="Invalid token")

            if datetime.utcfromtimestamp(expired) < datetime.utcnow():
                raise HTTPException(status_code=403, detail="Expired token")

            if id_estado != 1:
                raise HTTPException(status_code=403, detail="Inactive user")

            # Inyectar los datos en el objeto request
            request.state.email = email
            request.state.rol_id = rol_id
            request.state.nombre = nombre
            request.state.apellido = apellido

        except PyJWTError:
            raise HTTPException(status_code=403, detail="Invalid token or expired token")

        return await func(*args, **kwargs)
    return wrapper
