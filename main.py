from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# 1. Configuração da API
app = FastAPI(title="Consultoc Intelligence API")

# Permite que seu site/widget se conecte à API sem bloqueios
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Conexão com o Banco de Dados Railway (Servidor Switchyard)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Rota Principal de Status
@app.get("/")
def home():
    return {
        "status": "online",
        "plataforma": "Consultoc",
        "versao": "1.2-estavel"
    }

# 4. Rota de Teste de Banco (Versão sem erro de PostGIS)
@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as connection:
            # Consulta simples para checar se o banco está respondendo
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()
            return {
                "database": "Conectado com Sucesso",
                "versao": version[0],
                "status": "Pronto para salvar dados"
            }
    except Exception as e:
        return {"database": "Erro de Conexão", "detalhes": str(e)}

# 5. Rota para Receber Avaliações
@app.post("/avaliar")
async def salvar_avaliacao(dados: dict):
    # Aqui os dados do seu site serão processados e salvos
    return {"message": "Dados recebidos pela Consultoc!", "data": dados}
