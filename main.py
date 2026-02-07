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

# 2. Configuração do Banco de Dados (PostgreSQL 17)
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

# Habilita CORS robusto para evitar erros de conexão no navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependência do Banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Funções Auxiliares
def enviar_email_boas_vindas(email_destino):
    print(f"📧 Alerta Igrtech: E-mail de boas-vindas para {email_destino}")

def notificar_novo_lead(endereco, area):
    print(f"🚀 NOVO LEAD CONSULTOC: Imóvel em {endereco} ({area}m²)")

# --- ROTAS ---

@app.get("/")
def home():
    return {"status": "online", "plataforma": "Consultoc", "versao": "1.5-pro"}

@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()
            return {"database": "Conectado", "versao": version[0]}
    except Exception as e:
        return {"database": "Erro", "detalhes": str(e)}

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
        
        # Notificação interna de Lead
        notificar_novo_lead(nova_av.endereco, nova_av.area_util)
        
        return {"message": "Sucesso", "id": nova_av.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/avaliacoes")
def listar_avaliacoes(db: Session = Depends(get_db)):
    return db.query(Avaliacao).all()

@app.post("/webhook-stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email_cliente = session.get("customer_details", {}).get("email")
        enviar_email_boas_vindas(email_cliente)

    return {"status": "success"}

