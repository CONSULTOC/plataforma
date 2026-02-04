from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Configuração do Banco
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo da Tabela de Avaliações
class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    id = Column(String, primary_key=True, index=True)
    endereco = Column(Text)
    area = Column(Float)
    valor_estimado = Column(Float)
    latitude = Column(Float) # Substitui o PostGIS por número
    longitude = Column(Float) # Substitui o PostGIS por número
    created_at = Column(DateTime, default=datetime.utcnow)

# Criar tabelas automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Consultoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "online", "banco": "conectado", "versão": "1.2-estável"}

@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as conn:
            return {"database": "Conectado com Sucesso", "versao": "Postgres 17"}
    except Exception as e:
        return {"database": "Erro", "detalhes": str(e)}
