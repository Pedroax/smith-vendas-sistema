"""
Smith 2.0 - API Principal
FastAPI application com integração WhatsApp e LangGraph
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings, validate_settings

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle da aplicação"""
    # Startup
    logger.info("🚀 Iniciando Smith 2.0...")

    try:
        # Validar configurações
        validate_settings()
        logger.success("✅ Configurações validadas")
    except ValueError as e:
        logger.error(f"❌ Erro nas configurações: {e}")
        raise

    # Inicializar Supabase
    from app.database import init_supabase
    try:
        init_supabase()
        logger.success("✅ Supabase conectado")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Supabase: {e}")
        # Não bloquear startup em modo desenvolvimento
        if not settings.debug:
            raise

    logger.info("✅ Conexões inicializadas")

    # TODO: Carregar agente LangGraph
    logger.info("✅ Agente Smith carregado")

    logger.success(f"🎯 Smith 2.0 rodando em http://localhost:{settings.api_port}")
    logger.info(f"📚 Documentação: http://localhost:{settings.api_port}/docs")

    yield

    # Shutdown
    logger.info("👋 Encerrando Smith 2.0...")
    # TODO: Fechar conexões


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Agente de Vendas Inteligente com IA",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware para confiar em proxy headers (Railway, Heroku, etc)
# CRITICAL: Deve vir ANTES do CORS para funcionar corretamente
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# Em produção, forçar HTTPS e confiar nos headers do proxy
if not settings.debug:
    # Confiar nos headers X-Forwarded-Proto, X-Forwarded-For do Railway
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Railway gerencia isso
    )

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Middleware personalizado para garantir que redirects usem HTTPS em produção
@app.middleware("http")
async def force_https_redirects(request: Request, call_next):
    """
    Força redirects a usarem HTTPS quando X-Forwarded-Proto é https
    Resolve problema de Mixed Content no Railway/Vercel
    """
    response = await call_next(request)

    # Se é um redirect E a requisição original era HTTPS
    if (
        response.status_code in [301, 302, 303, 307, 308] and
        request.headers.get("x-forwarded-proto") == "https"
    ):
        location = response.headers.get("location", "")
        # Se o redirect for para HTTP, trocar para HTTPS
        if location.startswith("http://"):
            response.headers["location"] = location.replace("http://", "https://", 1)
            logger.info(f"🔒 Redirect corrigido: {location} → {response.headers['location']}")

    return response


# ========================================
# ROTAS DE HEALTH CHECK
# ========================================

@app.get("/")
async def root():
    """Rota raiz"""
    return {
        "name": settings.app_name,
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "2.0.0"
    }


# ========================================
# ROTAS DA API
# ========================================

from app.api import leads, webhook, analytics, projects, webhook_facebook, test_qualification, webhook_evolution, webhook_uazapi, client_portal, interactions, appointments, notifications, search, tasks, admin_auth, invoices, milestones, webhook_form

# Incluir routers
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(webhook_facebook.router, prefix="/webhook", tags=["Facebook"])
app.include_router(webhook_evolution.router, tags=["Evolution"])  # Webhook WhatsApp (DEPRECATED)
app.include_router(webhook_uazapi.router, prefix="/webhook", tags=["UAZAPI"])  # Webhook WhatsApp (NOVO)
app.include_router(webhook_form.router, prefix="/webhook", tags=["Form LP"])  # Formulário Landing Page
app.include_router(test_qualification.router, prefix="/api", tags=["Testing"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(client_portal.router, tags=["Portal do Cliente"])
app.include_router(interactions.router, tags=["Interactions"])
app.include_router(appointments.router, tags=["Appointments"])
app.include_router(notifications.router, tags=["Notifications"])
app.include_router(search.router, tags=["Search"])
app.include_router(tasks.router, tags=["Tasks"])
app.include_router(admin_auth.router, tags=["Admin Auth"])
app.include_router(invoices.router, tags=["Invoices"])
app.include_router(milestones.router, tags=["Milestones"])

# Teste direto
@app.get("/api/test-analytics")
async def test_analytics():
    """Endpoint de teste para verificar se está funcionando"""
    return {"status": "ok", "message": "Analytics router funcionando!"}


# ========================================
# WEBSOCKET
# ========================================

from app.websocket import manager

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para atualizações em tempo real"""
    await manager.connect(websocket)
    try:
        # Manter conexão aberta e aguardar mensagens
        while True:
            # Receber mensagem do cliente (heartbeat ou comando)
            data = await websocket.receive_text()
            logger.debug(f"Mensagem WebSocket recebida: {data}")

            # Echo de heartbeat
            if data == "ping":
                await manager.send_personal_message("pong", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Cliente WebSocket desconectado")
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")
        manager.disconnect(websocket)


# Seed mock data desabilitado - usando dados reais do Supabase
# @app.on_event("startup")
# async def startup_event():
#     """Popula banco com dados de exemplo"""
#     leads.seed_mock_leads()
#     logger.info("✅ Dados de exemplo carregados")


# ========================================
# ERROR HANDLERS
# ========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções"""
    logger.error(f"❌ Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )


# ========================================
# EXECUÇÃO
# ========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
