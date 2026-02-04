import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Busca a URL que o Railway/Hostinger fornece. 
# Se você estiver testando no PC e não houver URL, ele usa um banco local (sqlite)
DATABASE_URL = os.getenv("DATABASE_URL")

# Pequeno ajuste técnico: O Railway às vezes entrega "postgres://", 
# mas as bibliotecas modernas do Python exigem "postgresql://"
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Cria a conexão oficial com o banco de dados
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Função para abrir e fechar a conexão com o banco em cada consulta
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CONFIGURAÇÕES CONSULTOC ---
app = FastAPI(title="Consultoc Intelligence API")

# Permitir que o Widget de qualquer site acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Substitua pelas suas chaves reais no painel da Hostinger (Variáveis de Ambiente)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_sua_chave_aqui")

# --- MOTOR DE CÁLCULO (IA SIMPLIFICADA) ---
class ConsultocAIEngine:
    def __init__(self):
        # Base de conhecimento (Área, Quartos, Padrão 1-5, Preço)
        data = [[50, 2, 2, 350000], [80, 3, 3, 600000], [120, 3, 5, 1200000], [40, 1, 1, 220000]]
        self.df = pd.DataFrame(data, columns=['area', 'quartos', 'padrao', 'preco'])
        self.model = LinearRegression()
        self.model.fit(self.df[['area', 'quartos', 'padrao']], self.df['preco'])

    def prever(self, area, quartos, padrao):
        valor = self.model.predict([[area, quartos, padrao]])
        return round(valor[0], 2)

engine = ConsultocAIEngine()

# --- GERADOR DE PDF CONSULTOC ---
class ConsultocPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 51, 102) # Azul Consultoc
        self.cell(0, 10, 'CONSULTOC - LAUDO DE AVALIAÇÃO', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Laudo gerado por Consultoc Inteligência Imobiliária em {datetime.now().strftime("%d/%m/%Y")}', 0, 0, 'C')

# --- MODELOS DE DADOS ---
class AvaliacaoInput(BaseModel):
    cep: str
    tipo: str
    area_util: float
    quartos: int
    padrao: int # 1 a 5

# --- ENDPOINTS (ROTAS) ---

@app.get("/")
def home():
    return {"message": "Consultoc API Online"}

@app.post("/v1/avaliacoes/processar")
async def processar_avaliacao(dados: AvaliacaoInput):
    try:
        # 1. Calcula o valor usando o motor IA
        valor_estimado = engine.prever(dados.area_util, dados.quartos, dados.padrao)
        
        # 2. Simula ID de avaliação
        avaliacao_id = f"CONS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "status": "success",
            "avaliacao_id": avaliacao_id,
            "valor_mercado": valor_estimado,
            "mensagem": "Avaliação processada com sucesso pela Consultoc."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/checkout/criar")
async def criar_checkout(avaliacao_id: str):
    try:
        # Cria link de pagamento no Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {'name': f'Laudo Consultoc {avaliacao_id}'},
                    'unit_amount': 4990, # R$ 49,90
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url="https://consultoc.com.br/sucesso",
            cancel_url="https://consultoc.com.br/cancelado",
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/laudo/pdf/{avaliacao_id}")
def gerar_pdf(avaliacao_id: str, valor: float, endereco: str):
    pdf = ConsultocPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"ID da Avaliação: {avaliacao_id}", 0, 1)
    pdf.cell(0, 10, f"Endereço: {endereco}", 0, 1)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"VALOR DE MERCADO ESTIMADO: R$ {valor:,.2f}", 1, 1, 'C')
    
    filename = f"laudo_{avaliacao_id}.pdf"
    pdf.output(filename)
    return {"message": f"PDF {filename} gerado com sucesso."}