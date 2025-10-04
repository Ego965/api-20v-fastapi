## 📄 Proyecto FastAPI (API REST)

```markdown
# 🚀 API RESTful: FastAPI, Pydantic y MongoDB

Esta aplicación es una API RESTful de alto rendimiento construida con **FastAPI** y **Uvicorn**. La arquitectura está modularizada en tres capas (`main.py`, `post.py`, `database.py`) para una mejor separación de responsabilidades. Utiliza **MongoDB** para la persistencia.

---

## ⚙️ Configuración y Dependencias

### 1. Clonar y Preparar Entorno

```bash
# 1. Clonar el repositorio
git clone <URL_DE_TU_REPOSITORIO_FASTAPI>
cd <nombre-de-tu-repo-fastapi>

# 2. Crear y activar el entorno virtual
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# 3. Instalar dependencias (incluyendo pymongo y uvicorn)
pip install -r requirements.txt

# Hacer los ajustes requeridos sobre el uso de mongodb u otra base de datos local o en la nube.

#IMPORTANTE, FORMA DE EJECUCION:
# Usar el estándar uvicorn <modulo>:<app_object>
uvicorn main:app --reload
