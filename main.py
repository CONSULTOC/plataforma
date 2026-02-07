from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
import os
import stripe
import uuid
from datetime import datetime
from typing import List

# 1. Configuração de Variáveis de Ambiente
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./consultoc.db")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# 2. Configuração do Banco de Dados
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    id = Column(String, primary_key=True, index=True)
    endereco = Column(Text, nullable=False)
    area_util = Column(Float, nullable=False)
    valor_estimado = Column(Float)
    status = Column(String, default="Pendente")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# 3. Modelos de Validação (Pydantic)
class AvaliacaoCreate(BaseModel):
    endereco: str = Field(..., min_length=5)
    area: float = Field(..., gt=0)

# 4. Inicialização da API
app = FastAPI(title="Consultoc Intelligence API", version="1.5.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS ---

@app.get("/")
def home():
    return {"status": "online", "plataforma": "Consultoc", "versao": "1.5.1-pro"}

@app.post("/avaliar")
async def salvar_avaliacao(dados: AvaliacaoCreate, db: Session = Depends(get_db)):
    try:
        # Lógica de negócio: R$ 5.500 por m² (Exemplo base Consultoc)
        valor_calculado = dados.area * 5500
        
        nova_av = Avaliacao(
            id=str(uuid.uuid4()),
            endereco=dados.endereco,
            area_util=dados.area,
            valor_estimado=valor_calculado,
            status="Pendente"
        )
        db.add(nova_av)
        db.commit()
        db.refresh(nova_av)
        return {"message": "Sucesso", "id": nova_av.id, "valor_estimado": valor_calculado}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao processar avaliação: {str(e)}")

@app.post("/criar-checkout")
async def criar_checkout(plano: str):
    precos = {"starter": 19900, "pro": 59900} # Em centavos (BRL)
    if plano not in precos:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
        
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {'name': f'Assinatura Consultoc - {plano.capitalize()}'},
                    'unit_amount': precos[plano],
                    'recurring': {'interval': 'month'},
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://app.consultoc.com.br/sucesso?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://app.consultoc.com.br/planos',
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
 

