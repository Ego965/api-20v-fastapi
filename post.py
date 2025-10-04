from pydantic import BaseModel, Field, BeforeValidator
from pymongo.database import Database
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any, Optional, Annotated

PydanticObjectId = Annotated[str, BeforeValidator(str)]
# --- Modelos de Datos ---

# 1. Modelo de respuesta (para asegurar que 'id' es un string en la salida)
class PostResponse(BaseModel):
    # Usamos PydanticObjectId para permitir que el campo acepte ObjectId 
    # y lo convierta a string
    id: PydanticObjectId = Field(..., alias="_id") 
    title: str
    content: str
    created: datetime

    class Config:
        # Permite que Pydantic lea la salida de MongoDB con el campo "_id"
        populate_by_name = True
        # Este es el nuevo ajuste para Pydantic V2/V3
        arbitrary_types_allowed = True 
        # Ya no necesitamos json_encoders para ObjectId gracias a PydanticObjectId
        json_schema_extra = {
            "example": {
                "id": "60d5ec49f13e5a5a9c0f9a2c",
                "title": "Mi Primer Post",
                "content": "Este es el contenido de mi post.",
                "created": "2025-01-01T12:00:00"
            }
        }

# 2. Modelo base para la creación y edición (lo que el usuario envía)
class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=50, description="Título del post.")
    content: str = Field(..., min_length=1, max_length=500, description="Contenido del post.")


# --- Funciones CRUD (Capa de Negocio) ---

POST_COLLECTION = "post"

def create_post(db: Database, post_data: PostCreate) -> PostResponse: # Cambiar el tipo de retorno a PostResponse
    """Crea un nuevo post en la base de datos."""
    new_post = {
        "title": post_data.title,
        "content": post_data.content,
        "created": datetime.now()
    }
    result = db[POST_COLLECTION].insert_one(new_post)
    
    created_post = db[POST_COLLECTION].find_one({"_id": result.inserted_id})
    
    # USO CLAVE: Validar y serializar el post creado con Pydantic V2/V3
    return PostResponse.model_validate(created_post)


def get_all_posts(db: Database) -> List[PostResponse]:
    """Obtiene todos los posts de la base de datos."""
    posts_data = list(db[POST_COLLECTION].find())
    
    # El método 'model_validate' de Pydantic V2 es ideal aquí
    # Pasamos una lista de diccionarios, y Pydantic valida y serializa cada uno.
    return [PostResponse.model_validate(post) for post in posts_data]


def get_post_by_id(db: Database, post_id: str) -> Optional[PostResponse]:
    """Obtiene un solo post por su ID de MongoDB (string de 24 caracteres)."""
    if not ObjectId.is_valid(post_id):
        return None 
        
    post_data = db[POST_COLLECTION].find_one({"_id": ObjectId(post_id)})
    
    if post_data:
        # Usar model_validate para la validación
        return PostResponse.model_validate(post_data)
    return None


def update_post(db: Database, post_id: str, post_data: PostCreate) -> Optional[PostResponse]:
    """Actualiza un post existente."""
    if not ObjectId.is_valid(post_id):
        return None

    updated_data = {
        "title": post_data.title,
        "content": post_data.content
    }
    
    result = db[POST_COLLECTION].update_one(
        {"_id": ObjectId(post_id)}, 
        {"$set": updated_data}
    )
    
    if result.matched_count == 0:
        return None
        
    return get_post_by_id(db, post_id)


def delete_post(db: Database, post_id: str) -> bool:
    """Elimina un post por su ID."""
    if not ObjectId.is_valid(post_id):
        return False
        
    result = db[POST_COLLECTION].delete_one({"_id": ObjectId(post_id)})
    
    # Retorna True si se eliminó exactamente 1 documento
    return result.deleted_count == 1
    
    
# En post.py
def search_posts_by_title(db: Database, title_query: str) -> List[PostResponse]:
    """Busca posts por una expresión regular en el título."""
    filtro = {"title": {"$regex": title_query, "$options": "i"}}

    posts_data = list(db[POST_COLLECTION].find(filtro))
    
    # USO CLAVE: Aplicar la validación y serialización a cada post en la lista
    return [PostResponse.model_validate(post) for post in posts_data]