import os
from dotenv import load_dotenv
import yagmail
from firebase_admin import auth as firebase_auth
from fastapi import FastAPI
from models.Userlogin import MailSend

# Cargar variables de entorno
load_dotenv()

# Configurar FastAPI
app = FastAPI()

# Configurar variables de entorno
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# * Función para enviar el correo de restablecimiento
async def password_reset_email(email: MailSend):
    try:
        # Verificar si el usuario existe
        try:
            user = firebase_auth.get_user_by_email(email)
            print(f"Usuario encontrado: {user.uid}")
        except firebase_auth.AuthError as auth_error:
            print(f"Error al buscar usuario: {auth_error}")
            return {"success": False, "message": "Usuario no encontrado"}

        # Generar el enlace de restablecimiento
        print(f"Generando enlace de restablecimiento para: {email}")
        reset_link = firebase_auth.generate_password_reset_link(email)
        
        if not reset_link:
            raise ValueError("No se pudo generar el enlace de restablecimiento de contraseña.")
        
        print(f"Enlace generado con éxito: {reset_link[:20]}...")  # Imprime solo los primeros 20 caracteres por seguridad

        # Configurar yagmail
        yag = yagmail.SMTP(EMAIL_USERNAME, EMAIL_PASSWORD)

        # Enviar el correo
        subject = "Restablecer tu contraseña"
        contents = f"Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_link}"
        
        yag.send(to=email, subject=subject, contents=contents)
        
        print("Correo enviado con éxito")
        return {"success": True, "message": "Correo de restablecimiento enviado"}

    except firebase_auth.AuthError as auth_error:
        print(f"Error de autenticación de Firebase: {auth_error}")
        return {"success": False, "message": f"Error de Firebase: {str(auth_error)}"}
    except ValueError as ve:
        print(f"Error de valor: {ve}")
        return {"success": False, "message": str(ve)}
    except Exception as e:
        print(f"Error inesperado: {e}")
        return {"success": False, "message": f"Error inesperado: {str(e)}"}

# * Función para enviar el correo de bienvenida 
async def welcome_email(email: str, password: str):
    try:
        # Configurar yagmail
        yag = yagmail.SMTP(EMAIL_USERNAME, EMAIL_PASSWORD)

        # Enviar el correo
        subject = "Bienvenido a nuestra plataforma Lumina"
        contents = f"Has sido aprobado, recuerda cambiar tu contraseña. Tu contraseña es: {password}"
                
        yag.send(to=email, subject=subject, contents=contents)
                
        print("Correo de bienvenida enviado con éxito")
        return {"success": True, "message": "Correo de bienvenida enviado"}

    except Exception as e:
        print(f"Error al enviar el correo de bienvenida: {e}")
        return {"success": False, "message": f"Error al enviar el correo de bienvenida: {str(e)}"}
    
# * Función para enviar el correo de rechazo
async def rejection_email(email: str):
    try:
        # Configurar yagmail
        yag = yagmail.SMTP(EMAIL_USERNAME, EMAIL_PASSWORD)

        # Enviar el correo
        subject = "Rechazo de solicitud"
        contents = f"Tu solicitud ha sido rechazada por la administración de Lumina. Si tienes alguna duda, por favor contáctanos."
                    
        yag.send(to=email, subject=subject, contents=contents)
                    
        print("Correo de rechazo enviado con éxito")
        return {"success": True, "message": "Correo de rechazo enviado"}

    except Exception as e:
        print(f"Error al enviar el correo de rechazo: {e}")
        return {"success": False, "message": f"Error al enviar el correo de rechazo: {str(e)}"}
    
# * Función para enviar el correo de solicitud
async def solicitud_mail(email: MailSend):
    try:
        # Configurar yagmail
        yag = yagmail.SMTP(EMAIL_USERNAME, EMAIL_PASSWORD)

        # Enviar el correo
        subject = "Solicitud de registro"
        contents = f"Tu solicitud ha sido enviada con éxito. Pronto recibirás una respuesta de la administración de Lumina."
                    
        yag.send(to=email, subject=subject, contents=contents)
                    
        print("Correo de solicitud enviado con éxito")
        return {"success": True, "message": "Correo de solicitud enviado"}

    except Exception as e:
        print(f"Error al enviar el correo de solicitud: {e}")
        return {"success": False, "message": f"Error al enviar el correo de solicitud: {str(e)}"}