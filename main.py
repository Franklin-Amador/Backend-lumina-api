from fastapi import FastAPI, Request, APIRouter, HTTPException

from models.Userlogin import UserRegister, UserLogin, MailSend
from models.Prueba import Prueba
from utils.database import fetch_query_as_json
import json
from typing import List, Dict, Union

from models.Instructores import SolicitudInstructor, Solicitud, Inscripcion

from controllers.firebase import register_user_firebase, login_user_firebase
from controllers.instructores import get_instructores_info, get_SolicitudesInstructor, post_Instructores, rechazar_Solicitud, get_especialidades, get_categorias, create_solicitud
from utils.security import validate
from utils.sendmail import password_reset_email, welcome_email, rejection_email

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración del middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP
    allow_headers=["*"],  # Permite todos los encabezados
)

@app.get("/")
async def hello():
    return {
        "Hello": "World"
        , "version": "0.1.70"
    }

@app.post("/register")
async def register(user: UserRegister):
    return await register_user_firebase(user)


@app.post("/login/custom")
async def login_custom(user: UserLogin):
    return await login_user_firebase(user)


@app.get("/user")
@validate
async def user(request: Request):
    return {
        "email": request.state.email
    }
 
 
@app.get("/instructores", response_model=List[Dict[str, Union[str, int]]])
@validate
async def get_instructores(request: Request):
    return await get_instructores_info()


@app.get("/solicitudes/instructor", response_model=List[SolicitudInstructor])
@validate
async def get_solicitudes_instructor(request: Request):
    return await get_SolicitudesInstructor()

@app.post("/solicitud")
# @validate
async def instapp(inst: Solicitud):
    return await post_Instructores(inst)
    
    
@app.put("/solicitud/rechazo")
# @validate
async def instrej(inst: Solicitud):
   return await rechazar_Solicitud(inst)

@app.post("/inscripcion")
async def inscripcion(inscripcion: Inscripcion):
    return await create_solicitud(inscripcion)

@app.get("/especialidades")
async def especialidades():
    return await get_especialidades()

@app.get("/categorias")
async def categorias():
    return await get_categorias()

# Endpoint para solicitar el restablecimiento de contraseña
@app.post("/r/password")
async def reset_password(request: MailSend):
    result = await password_reset_email(request.email)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/bienvenida")
async def bienvenida(request: MailSend):
    result = await welcome_email(request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/correorechazo")
async def send_rejection_email(mail: MailSend):
    result = await rejection_email(mail.email)
    if result["success"]:
        return {"message": result["message"]}
    else:
        raise HTTPException(status_code=500, detail=result["message"])


@app.post("/prueba")
async def create_prueba(prueba: Prueba):
    query = f"INSERT INTO lum.create_user (username ,name , email, active) VALUES ('{prueba.username}', '{prueba.name}', '{prueba.email}', {prueba.active})"
    try:
        result = await fetch_query_as_json(query)
        return json.loads(result)[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)