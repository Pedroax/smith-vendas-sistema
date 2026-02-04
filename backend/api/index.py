"""
Vercel entry point - FastAPI direto (sem Mangum)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create app
app = FastAPI(title="Smith 2.0 Backend", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
try:
    from app.api.leads import router as leads_router
    app.include_router(leads_router, prefix="/api/leads", tags=["leads"])
    print("✅ Leads router carregado com sucesso")
except ImportError as e:
    print(f"⚠️ Aviso: Não foi possível importar leads router: {e}")
    print("📝 Usando rotas mock temporárias")

    # Rotas mock temporárias enquanto Supabase não está configurado
    @app.get("/api/leads")
    async def mock_get_leads():
        return []

    @app.get("/api/leads/stats/summary")
    async def mock_get_stats():
        return {
            "total_leads": 0,
            "por_status": {},
            "por_origem": {},
            "por_temperatura": {},
            "score_medio": 0,
            "valor_total_pipeline": 0,
            "taxa_qualificacao": 0,
            "taxa_conversao": 0
        }

@app.get("/")
def root():
    return {
        "name": "Smith 2.0",
        "version": "2.0.0",
        "status": "online",
        "message": "Backend funcionando na Vercel!",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# Webhook do Facebook - direto aqui para evitar problemas de imports
from fastapi import Query, Request, HTTPException
from fastapi.responses import PlainTextResponse

@app.get("/webhook/facebook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """Verificação do webhook do Facebook"""
    print(f"🔍 Verificação webhook - mode: {mode}, token: {token}")

    # Token configurado no Facebook
    verify_token = "smith_webhook_2026"

    if mode == "subscribe" and token == verify_token:
        print("✅ Webhook verificado!")
        return PlainTextResponse(content=challenge, status_code=200)

    print("❌ Token inválido")
    raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook/facebook")
async def receive_facebook_lead(request: Request):
    """
    Recebe leads do Facebook Lead Ads
    Processa, qualifica e insere no CRM automaticamente
    """
    try:
        # Parse JSON
        data = await request.json()
        print(f"📨 Webhook Facebook recebido: {data}")

        # Importar lógica de processamento
        try:
            from app.api.webhook_facebook import _process_facebook_lead

            # Processar cada entrada
            if "entry" not in data:
                return {"status": "ok", "message": "No entries to process"}

            for entry in data["entry"]:
                if "changes" not in entry:
                    continue

                for change in entry["changes"]:
                    if change.get("field") != "leadgen":
                        continue

                    # Extrair dados do lead
                    lead_data = change.get("value", {})
                    lead_id_fb = lead_data.get("leadgen_id")
                    form_id = lead_data.get("form_id")
                    page_id = lead_data.get("page_id")

                    print(f"📋 Processando lead FB: {lead_id_fb}")

                    # Processar lead com toda a automação
                    await _process_facebook_lead(lead_id_fb, form_id, page_id, lead_data)

            return {"status": "ok", "message": "Leads processados"}

        except ImportError as e:
            print(f"⚠️ Erro ao importar processamento: {e}")
            print(f"📝 Lead salvo para processamento manual: {data}")
            return {"status": "ok", "message": "Lead recebido (processamento offline)"}

    except Exception as e:
        print(f"❌ Erro ao processar webhook Facebook: {e}")
        # Retorna 200 mesmo com erro para não fazer Facebook retentar infinitamente
        return {"status": "error", "message": str(e)}
