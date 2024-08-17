from dotenv import load_dotenv
import os
import pyodbc
import logging
import json
from datetime import datetime, date
from fastapi import  HTTPException


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

driver = os.getenv('SQL_DRIVER')
server = os.getenv('SQL_SERVER')
database = os.getenv('SQL_DATABASE')
username = os.getenv('SQL_USERNAME')
password = os.getenv('SQL_PASSWORD')


connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"

import pyodbc

async def get_db_connection():
    try:
        logger.info(f"Intentando conectar a la base de datos con la cadena de conexión: {connection_string}")
        conn = pyodbc.connect(connection_string)
        logger.info("Conexión exitosa a la base de datos.")
        return conn
    except pyodbc.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise Exception(f"Database connection error: {str(e)}")



def datetime_handler(x):
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    if x is None:
        return None
    raise TypeError(f"Object of type {type(x)} is not JSON serializable")
        
 
async def fetch_query_as_json(query, params=None, output_params=None, commit=False):
    try:
        conn = await get_db_connection()
        cursor = conn.cursor()
        
        logger.debug(f"Ejecutando query: {query}")
        logger.debug(f"Parámetros: {params}")

        cursor.execute(query, params or [])

        results = []
        columns = []

        # Leer todos los conjuntos de resultados
        while True:
            if cursor.description:
                # Obtener columnas y resultados
                columns = [column[0] for column in cursor.description]
                results.extend([
                    {
                        k: (v.isoformat() if isinstance(v, (datetime, date)) else v) 
                        for k, v in zip(columns, row)
                    }
                    for row in cursor.fetchall()
                ])
            if not cursor.nextset():
                break

        if commit:
            conn.commit()

        # Si hay resultados, retornar JSON
        if results:
            return json.dumps(results, default=datetime_handler)
        else:
            return json.dumps([])

    except pyodbc.Error as e:
        logger.error(f"Error ejecutando el query: {str(e)}")
        raise Exception(f"Error ejecutando el query: {str(e)}")
    
    finally:
        cursor.close()
        conn.close()

       






