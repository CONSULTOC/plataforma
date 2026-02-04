from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# 1. Configuração do App
app = FastAPI(title="Consultoc Intelligence API")

# Permitir que o Widget acesse a API de qualquer domínio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Conexão com o Banco de Dados Railway
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável DATABASE_URL não foi encontrada no arquivo .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Rota de Verificação (Health Check)
@app.get("/")
def home():
    return {
        "status": "online",
        "plataforma": "Consultoc",
        "message": "API de Avaliação Imobiliária Pronta"
    }

# 4. Rota para Testar a Conexão com o Banco
@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT postgis_full_version();"))
            version = result.fetchone()
            return {"database": "Connected", "postgis": version[0]}
    except Exception as e:
        return {"database": "Error", "details": str(e)}

# 5. Exemplo de Rota para Receber Dados do Widget
@app.post("/avaliar")
async def avaliar_imovel(dados: dict):
    # Aqui entrará a lógica da IA para processar os dados
    # e salvar no banco de dados do Railway
    return {
        "message": "Dados recebidos com sucesso pela Consultoc",
        "recebido": dados
    }

if __name__ == "__main__":
    import uvicorn
    # Porta 8000 interna que o Docker mapeia para a porta 80 externa
    uvicorn.run(app, host="0.0.0.0", port=8000)
