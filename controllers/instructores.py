
import json
import logging
from firebase_admin import auth as firebase_auth
import logging
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel

from utils.database import fetch_query_as_json, get_db_connection
from utils.sendmail import welcome_email, rejection_email, solicitud_mail
from models.Instructores import Solicitud, Inscripcion
import json
import random


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#  * funcion para obtener la informacion de los instructores
async def get_instructores_info():
    try:
        query = "EXEC ObtenerInformacionInstructores"
        logger.info(f"Ejecutando query: {query}")
        
        # Llama a fetch_query_as_json para obtener los resultados
        result_json = await fetch_query_as_json(query)
        
        # Si no se obtuvieron resultados, devuelve una lista vacía
        if not result_json:
            return []
        
        # Convierte el JSON a una lista de diccionarios
        results = json.loads(result_json)
        
        # Convierte los valores a cadenas
        for result in results:
            result["Cantidad_Cursos"] = str(result["Cantidad_Cursos"])
            result["Promedio_Score"] = str(result["Promedio_Score"])
            result["Cantidad_Inscripciones"] = str(result["Cantidad_Inscripciones"])
        
        return results
    
    except Exception as e:
        logger.error(f"Error al obtener la información de instructores: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener la información de instructores: {e}")

# * funcion para obtener las solicitudes de instructor 
async def get_SolicitudesInstructor():
    query = "EXEC lum.sp_GetSolicitudesPendientesOrdenadas"
    logger.info(f"Ejecutando query: {query}")
    
    try:
        # Obtener los resultados de la consulta como JSON
        result_json = await fetch_query_as_json(query)
        
        # Manejar el caso en que no se obtuvieron resultados
        if not result_json:
            logger.warning("No se obtuvieron resultados de la consulta.")
            return []
        
        # Convertir el JSON a una lista de diccionarios
        results = json.loads(result_json)

        # Procesar las fechas en los resultados
        for result in results:
            fecha_solicitud = result.get('Fecha_Solicitud')
            if fecha_solicitud:
                try:
                    # Convertir la cadena de fecha a objeto datetime y luego a ISO format (solo fecha)
                    fecha_dt = datetime.fromisoformat(fecha_solicitud.rstrip('Z')).date()
                    result['Fecha_Solicitud'] = fecha_dt.isoformat()
                except ValueError as e:
                    logger.error(f"Error al procesar la fecha: {e}")
                    result['Fecha_Solicitud'] = None
        
        return results
    
    except Exception as e:
        logger.error(f"Error en get_SolicitudesInstructor: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener las solicitudes de instructor: {e}")


# ?funcion para registrar un instructor, se le envia un correo con su contraseña
async def post_Instructores(inst: Solicitud):
    query = """
    DECLARE @Resultado NVARCHAR(MAX), @CorreoInstructor NVARCHAR(100);
    EXEC lum.ProcesarSolicitud @Id_Solicitud = ?, @Resultado = @Resultado OUTPUT, @CorreoInstructor = @CorreoInstructor OUTPUT;
    SELECT @Resultado AS Resultado, @CorreoInstructor AS CorreoInstructor;
    """
    
    try:
        # Llama a fetch_query_as_json para obtener los resultados y realizar commit
        result_json = await fetch_query_as_json(
            query,
            params=(inst.Id_Solicitud,),
            commit=True
        )
        
        # Convierte el JSON a una lista de diccionarios
        results = json.loads(result_json)
        
        if not isinstance(results, list) or len(results) == 0:
            raise HTTPException(status_code=500, detail="No se recibieron resultados del procedimiento almacenado")

        result_dict = results[0] if results else {}
        resultado = result_dict.get('Resultado')
        emaild = result_dict.get('CorreoInstructor')

        if resultado != 'Éxito':
            raise HTTPException(status_code=500, detail=f"Error en el procedimiento almacenado: {resultado}")

        if not emaild:
            raise HTTPException(status_code=404, detail="No se encontró el correo para el instructor")

        # Generar un número aleatorio de 4 dígitos y convertirlo en una cadena
        random_number = "Fr4n" + str(random.randint(1000, 9999))
        
        # Crear usuario en Firebase Authentication
        user_record = firebase_auth.create_user(
            email=emaild,
            password=random_number # Usar una contraseña por defecto
        )
        
        # Enviar correo de bienvenida
        await welcome_email(emaild, random_number)
        
        return {
            "success": True,
            "message": "Instructor registrado exitosamente",
            "user_id": user_record.uid
        }
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar al instructor: {str(e)}")


# ?funcion para rechazar una solicitud, se envia un correo al solicitante
async def rechazar_Solicitud(inst: Solicitud):  
    try:
        conn = await get_db_connection()
        cursor = conn.cursor()
        try:
            # Asegúrate de que inst.Id_Solicitud se pasa como una tupla
            cursor.execute(
                "EXEC lum.RechazarSolicitud @Id_Solicitud = ?",
                (inst.Id_Solicitud,)
            )
            conn.commit()
            
            await rejection_email(inst.email)
            return {
                "success": True,
                "message":  "Solicitud rechazada exitosamente"
            }
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail="aqui"+str(e))
        finally:
            cursor.close()
            conn.close()    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {e}")

    
# ?funcion para obtener la informacion de las especialidades
async def get_especialidades():
    query = "SELECT * FROM lum.Especialidades"
    try:
        result = await fetch_query_as_json(query)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ?funcion para obtener la informacion de las categorias
async def get_categorias():
    query = "SELECT * FROM lum.Categorias"
    try:
        result = await fetch_query_as_json(query)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ?funcion para inscribir un instructor
async def create_solicitud(solicitud: Solicitud):
    query = """
        INSERT INTO lum.Solicitudes
        (Id_Especialidad, primer_Nombre, segundo_Nombre, primer_Apellido, segundo_Apellido, mail, Descripción, ImagenUrl)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        solicitud.Id_Especialidad,
        solicitud.primer_Nombre,
        solicitud.segundo_Nombre,
        solicitud.primer_Apellido,
        solicitud.segundo_Apellido,
        solicitud.mail,
        solicitud.Descripción,
        solicitud.ImagenUrl
    )
    try:
        await solicitud_mail(solicitud.mail)
        # Ejecutar la consulta de inserción
        await fetch_query_as_json(query, params, commit=True)
        return {
            "message": "Solicitud enviada exitosamente",
            "success": True
        }
       
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="No se pudo enviar la solicitud: " + str(e))
   