
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import date

class SolicitudInstructor(BaseModel):
    Id_Solicitud: int
    Id_Especialidad: int
    primer_Nombre: str
    segundo_Nombre: Optional[str] = None
    primer_Apellido: str
    segundo_Apellido: Optional[str] = None
    mail: str
    Fecha_Solicitud: date
    Estado: str
    Descripción: Optional[str] = None
    ImagenUrl: Optional[str] = None

    class Config:
        json_encoders = {
            date: lambda v: v.strftime("%Y-%m-%d")
        }
        

class Solicitud(BaseModel):
    Id_Solicitud: int
    email: Optional[str] = None
    
class Inscripcion(BaseModel):
    Id_Especialidad: int
    primer_Nombre: str
    segundo_Nombre: Optional[str] = None
    primer_Apellido: str
    segundo_Apellido: Optional[str] = None
    mail: str
    Descripción: Optional[str] = None
    ImagenUrl: Optional[str] = None