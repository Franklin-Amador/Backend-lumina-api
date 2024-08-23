import os
import requests
import json
import logging
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException



import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from utils.database import fetch_query_as_json, get_db_connection
from utils.security import create_jwt_token
from models.Userlogin import UserRegister, UserLogin


print(os.getcwd())


# class UserLoginF(BaseModel):
#     email: str
#     password: str

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Obtener la API Key de Firebase
api_key = os.getenv("FIREBASE_API_KEY")


# Inicializar la app de Firebase Admin
cred = credentials.Certificate("secrets/admin-firebasesdk.json")
firebase_admin.initialize_app(cred)


# ! Cambiar contraseña de firebase pendiente
async def change_password(user: UserRegister):
    try:
        user = firebase_auth.update_user(
            email=user.email,
            password=user.password
        )
        return {
            "mesaage": "Contraseña actualizada exitosamente"
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al cambiar contraseña: {e}"
        )

# ? Registrar usuario con Firebase Authentication ya funcionando
async def register_user_firebase(user: UserRegister):
    try:
        # Crear usuario en Firebase Authentication
        user_record = firebase_auth.create_user(
            email=user.email,
            password=user.password
        )

        conn = await get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "EXEC  insert_into_create_user @username = ?, @name = ?, @email = ?",
                user.name,
                user.name,
                user.email
            )
            conn.commit()
            return {
                "success": True,
                "message": "Usuario registrado exitosamente"
            }
        except Exception as e:
            firebase_auth.delete_user(user_record.uid)
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al registrar usuario: {e}"
        )


# ? Autenticar usuario con Firebase Authentication ya funcionando 
     
async def login_user_firebase(user: UserLogin):
    try:
        # Autenticar usuario con Firebase Authentication usando la API REST
        logger.info(f"Iniciando proceso de login para el usuario: {user.email}")
        
        api_key = os.getenv("FIREBASE_API_KEY")
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {
            "email": user.email,
            "password": user.password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        response_data = response.json()

        if "error" in response_data:
            raise HTTPException(
                status_code=400,
                detail=f"Error al autenticar usuario: {response_data['error']['message']}"
            )

        # Consulta para obtener Id_Estado, Id_Rol, primer_Nombre y primer_Apellido del usuario
        query = f"""
        SELECT u.Id_Estado, u.Id_Rol, u.primer_Nombre, u.primer_Apellido
        FROM lum.Usuarios u
        WHERE u.mail = '{user.email}'
        """

        logger.info("Ejecutando consulta de información del usuario")
        result_json = await fetch_query_as_json(query)
        result_dict = json.loads(result_json)

        if result_dict and result_dict[0].get("Id_Estado") == 1:
            # Información adicional a incluir en el token
            user_info = {
                "email": user.email,
                "id_estado": result_dict[0].get("Id_Estado"),  
                "rol_id": result_dict[0].get("Id_Rol"),
                "nombre": result_dict[0].get("primer_Nombre"),
                "apellido": result_dict[0].get("primer_Apellido")
            }

            return {
                "message": "Usuario autenticado exitosamente",
                "idToken": create_jwt_token(**user_info),
                "user": user_info
            }
        else:
            raise HTTPException(
                status_code=401,
                detail="Usuario no autorizado o estado inactivo"
            )
            
    except Exception as e:
        
        logger.error(f"Error en el proceso de login")
        raise HTTPException(
            status_code=400,
            detail=f"Error al autenticar usuario"
        )


# * funcion de forgot password en desarrollo

async def send_password_reset_email(email: str):
    try:
        # Genera el enlace para el restablecimiento de contraseña
        reset_link = firebase_auth.generate_password_reset_link(email)
        
        # Aquí Firebase envía el correo usando la plantilla configurada
        print(f"Enlace de restablecimiento de contraseña: {reset_link}")
        
        return {"success": True, "message": f"Correo de restablecimiento enviado {reset_link}"}
    
    except Exception as e:
        print(f"Error al enviar el correo de restablecimiento de contraseña: {e}")
        return {"success": False, "message": str(e)}
    
    

