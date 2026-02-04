from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text, Column, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import stripe
from datetime import datetime

# 1. Configuração de Variáveis de Ambiente
DATABASE_URL = os.getenv("DATABASE_URL")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# 2. Configuração do Banco de Dados
engine = create_engine(DATABASE_URL)
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

# 3. Inicialização da API
app = FastAPI(title="Consultoc Intelligence API")

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
    return {"status": "online", "plataforma": "Consultoc", "versao": "1.5-pro"}

@app.get("/avaliacoes")
def listar_avaliacoes(db: Session = Depends(get_db)):
    return db.query(Avaliacao).order_by(Avaliacao.created_at.desc()).all()

@app.post("/avaliar")
async def salvar_avaliacao(dados: dict, db: Session = Depends(get_db)):
    try:
        nova_av = Avaliacao(
            id=str(datetime.timestamp(datetime.now())),
            endereco=dados.get("endereco"),
            area_util=float(dados.get("area")),
            valor_estimado=float(dados.get("area")) * 5500,
            status="Pendente"
        )
        db.add(nova_av)
        db.commit()
        return {"message": "Sucesso", "id": nova_av.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/criar-checkout")
async def criar_checkout(plano: str):
    precos = {"starter": 19900, "pro": 59900}
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
            success_url='https://api.consultoc.com.br/sucesso',
            cancel_url='https://api.consultoc.com.br/planos',
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/webhook-stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
