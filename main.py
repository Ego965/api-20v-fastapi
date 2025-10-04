from fastapi import FastAPI, Depends, HTTPException, Path, Query, Response, Cookie, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional

# Importar funciones y modelos refactorizados
from database import get_db
from post import (
    PostCreate,
    PostResponse,
    create_post,
    get_all_posts,
    get_post_by_id,
    update_post,
    delete_post,
    search_posts_by_title
)

app = FastAPI(
    title="Blog API con FastAPI y MongoDB",
    description="API RESTful para manejar posts de un blog."
)

# CORS Middleware (se mantiene)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Endpoints ---

@app.get("/", tags=["Root"])
def read_root():
    """Endpoint de prueba de funcionamiento."""
    return {"message": "Bienvenido a la API del Blog con FastAPI"}


@app.post("/posts", response_model=PostResponse, status_code=201, tags=["Posts"])
def create_one_post(post: PostCreate, db=Depends(get_db)):
    """Crea un nuevo post. Solo acepta datos JSON."""
    try:
        new_post_data = create_post(db, post)
        return new_post_data
    except Exception as e:
        # Manejo genérico de error de base de datos
        raise HTTPException(status_code=500, detail=f"Error al crear el post: {e}")


@app.get("/posts", response_model=List[PostResponse], tags=["Posts"])
def get_all_posts_api(db=Depends(get_db)):
    """Obtiene la lista de todos los posts."""
    try:
        return get_all_posts(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los posts: {e}")


@app.get("/posts/search", response_model=List[PostResponse], tags=["Posts"])
def search_posts_api(
    titulo: str = Query(..., min_length=1, title="Título a buscar"),
    db=Depends(get_db)
):
    """Busca posts cuyo título coincida (parcialmente, sin importar mayúsculas) con el texto proporcionado."""
    try:
        return search_posts_by_title(db, titulo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda: {e}")


@app.get("/posts/{post_id}", response_model=PostResponse, tags=["Posts"])
def get_one_post_api(
    post_id: str = Path(
        ...,
        title="ID del post",
        min_length=24,
        max_length=24,
        regex="^[0-9a-fA-F]{24}$",
        description="Debe ser un ObjectId de 24 caracteres hexadecimales."
    ),
    db=Depends(get_db)
):
    """Obtiene un post específico usando su ID."""
    try:
        post = get_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post no encontrado")
        return post
    except Exception as e:
        # Se atrapan errores internos (ej. de DB)
        raise HTTPException(status_code=500, detail=f"Error al obtener el post: {e}")


@app.patch("/posts/{post_id}", response_model=PostResponse, tags=["Posts"])
def update_one_post_api(
    post_id: str = Path(..., regex="^[0-9a-fA-F]{24}$"),
    post_data: PostCreate = Depends(), # Usa el modelo PostCreate para validar los datos
    db=Depends(get_db)
):
    """Actualiza un post existente usando su ID."""
    try:
        updated_post = update_post(db, post_id, post_data)
        if not updated_post:
            raise HTTPException(status_code=404, detail="Post no encontrado o ID inválido")
        return updated_post
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el post: {e}")


@app.delete("/posts/{post_id}", status_code=204, tags=["Posts"])
def delete_one_post_api(
    post_id: str = Path(..., regex="^[0-9a-fA-F]{24}$"),
    db=Depends(get_db)
):
    """Elimina un post usando su ID. Retorna 204 No Content si es exitoso."""
    try:
        if not delete_post(db, post_id):
            raise HTTPException(status_code=404, detail="Post no encontrado o ID inválido")
        # El status 204 no devuelve cuerpo (retorna Response vacío por defecto)
        return Response(status_code=204)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el post: {e}")


# --- Puntos Extra y Endpoints de Prueba ---

@app.get("/secure/posts", response_model=List[PostResponse], tags=["Auth & Cookies"])
def obtener_posts_secure_api(
    authorization: str = Header(
        ..., 
        alias="Authorization", 
        description="Token en formato 'Bearer secreto123'"
    ),
    db=Depends(get_db)
):
    """Ejemplo de endpoint seguro usando token de autenticación en el header."""
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=400,
                detail="Formato de token inválido. Use 'Bearer <token>'"
            )
        
        token = authorization[7:]

        if token != "secreto123":
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
            
        return get_all_posts(db)
        
    except HTTPException:
        # Re-lanza la HTTPException si la generamos aquí (400, 401)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de servidor: {e}")


@app.get("/set-cookie", tags=["Auth & Cookies"])
def set_cookie_api(response: Response):
    """Guarda un ID de usuario en la cookie del navegador."""
    response.set_cookie(
        key="user_id", 
        value="987654", 
        httponly=True,  # No accesible por JavaScript
        max_age=3600    # Expira en 1 hora
    )
    return {"message": "Cookie 'user_id' creada!"}


@app.get("/get-cookie", tags=["Auth & Cookies"])
def get_cookie_api(user_id: str | None = Cookie(None)):
    """Obtiene el valor de la cookie 'user_id'."""
    if user_id is None:
        return {"value": "No se encontró la cookie 'user_id'"}
    return { "value": user_id }


@app.get("/del-cookie", tags=["Auth & Cookies"])
def clear_cookie_api(response: Response):
    """Elimina la cookie 'user_id'."""
    response.delete_cookie("user_id")
    return {"message": "Cookie 'user_id' eliminada"}