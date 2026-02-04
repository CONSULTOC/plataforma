from fastapi import FastAPI, HTTPException, Depends
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

# 2. Configuração do Banco de Dados (Estável PostgreSQL 17)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de Dados para Avaliações (Sincronizado com o Dashboard)
class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    id = Column(String, primary_key=True, index=True)
    endereco = Column(Text, nullable=False)
    area_util = Column(Float, nullable=False)
    valor_estimado = Column(Float)
    status = Column(String, default="Pendente")
    created_at = Column(DateTime, default=datetime.utcnow)

# Criação das tabelas no Railway
Base.metadata.create_all(bind=engine)

# 3. Inicialização da API
app = FastAPI(title="Consultoc Intelligence API")

# Habilita CORS para sua Landing Page e Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# --- ROTAS DE STATUS E TESTE ---

@app.get("/")
def home():
    return {"status": "online", "plataforma": "Consultoc", "versao": "1.5-pro"}

@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()
            return {
                "database": "Conectado com Sucesso",
                "versao": version[0],
                "status": "Pronto para salvar dados"
            }
    except Exception as e:
        return {"database": "Erro", "detalhes": str(e)}

# --- ROTAS DE NEGÓCIO (AVALIAÇÃO) ---

@app.post("/avaliar")
async def salvar_avaliacao(dados: dict, db: Session = Depends(get_db)):
    try:
        nova_av = Avaliacao(
            id=str(datetime.timestamp(datetime.now())),
            endereco=dados.get("endereco"),
            area_util=float(dados.get("area")),
            valor_estimado=float(dados.get("area")) * 5500, # Lógica simplificada de mercado
            status="Pendente"
        )
        db.add(nova_av)
        db.commit()
        return {"message": "Avaliação registrada com sucesso!", "id": nova_av.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/avaliacoes")
def listar_avaliacoes(db: Session = Depends(get_db)):
    # Rota que alimenta o Dashboard Administrativo
    return db.query(Avaliacao).order_by(Avaliacao.created_at.desc()).all()

# --- ROTAS DE PAGAMENTO (STRIPE) ---

@app.post("/criar-checkout")
async def criar_checkout(plano: str):
    # Preços definidos conforme os planos da Landing Page
    precos = {
        "starter": 19900,  # R$ 199,00
        "pro": 59900       # R$ 599,00
    }
    
    if plano not in precos:
        raise HTTPException(status_code=400, detail="Plano inválido")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {'name': f'Assinatura Consultoc API - {plano.capitalize()}'},
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
        from fastapi import Request

@app.post("/webhook-stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET") # Adicione esta chave no seu .env

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Payload inválido")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Assinatura inválida")

    # Lógica quando o pagamento é confirmado
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Aqui você pode salvar no PostgreSQL que o cliente está 'Ativo'
        print(f"Pagamento aprovado para: {session.customer_email}")

    return {"status": "success"}
    # Adicione esta função ao final do seu main.py
def enviar_email_boas_vindas(email_destino):
    # Aqui você integraria com SendGrid ou Gmail API
    # Por enquanto, deixaremos o log para você verificar na VPS
    print(f"📧 E-mail de boas-vindas enviado para: {email_destino}")

# Atualize o seu Webhook para chamar a função
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
        
        # 1. Libera o acesso no seu PostgreSQL 17
        # 2. Dispara o e-mail automático
        enviar_email_boas_vindas(email_cliente)

    return {"status": "success"}


