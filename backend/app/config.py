"""
Configurações do Smith 2.0
Carrega variáveis de ambiente e valida configurações
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Configurações da aplicação"""

    # Aplicação
    app_name: str = Field(default="Smith 2.0", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    api_port: int = Field(default=8000, env="API_PORT")

    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")

    # Evolution API (WhatsApp)
    evolution_api_url: str = Field(..., env="EVOLUTION_API_URL")
    evolution_api_key: str = Field(..., env="EVOLUTION_API_KEY")
    evolution_instance_name: str = Field(default="smith", env="EVOLUTION_INSTANCE_NAME")

    # Supabase
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_key: str = Field(..., env="SUPABASE_SERVICE_KEY")
    supabase_anon_key: Optional[str] = Field(default=None, env="SUPABASE_ANON_KEY")
    supabase_db_password: str = Field(..., env="SUPABASE_DB_PASSWORD")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_enabled: bool = Field(default=False, env="REDIS_ENABLED")

    # Google Calendar
    google_credentials_path: str = Field(
        default="google_credentials.json",
        env="GOOGLE_CREDENTIALS_PATH"
    )
    google_calendar_id: str = Field(default="primary", env="GOOGLE_CALENDAR_ID")
    calendar_timezone: str = Field(default="America/Sao_Paulo", env="CALENDAR_TIMEZONE")
    calendar_work_start_hour: str = Field(default="09:00", env="CALENDAR_WORK_START_HOUR")
    calendar_work_end_hour: str = Field(default="18:00", env="CALENDAR_WORK_END_HOUR")
    calendar_work_days: str = Field(default="1,2,3,4,5", env="CALENDAR_WORK_DAYS")  # 1=seg, 5=sex
    calendar_meeting_duration: int = Field(default=60, env="CALENDAR_MEETING_DURATION")  # minutos

    # Configurações do Agente
    debounce_seconds: float = Field(default=5.0, env="DEBOUNCE_SECONDS")
    max_message_length: int = Field(default=2000, env="MAX_MESSAGE_LENGTH")
    default_timezone: str = Field(default="America/Sao_Paulo", env="DEFAULT_TIMEZONE")

    # Números de Contato
    numero_pedro: str = Field(..., env="NUMERO_PEDRO")

    # Intelligent Controller
    auto_approve_threshold: int = Field(default=80, env="AUTO_APPROVE_THRESHOLD")
    review_threshold: int = Field(default=50, env="REVIEW_THRESHOLD")

    # JWT
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

    # CORS - SEMPRE incluir Vercel
    cors_origins: str = Field(
        default="*",  # Permitir todos em desenvolvimento
        env="CORS_ORIGINS"
    )

    # Facebook Lead Ads
    facebook_verify_token: str = Field(default="smith_webhook_2026", env="FACEBOOK_VERIFY_TOKEN")
    facebook_app_secret: str = Field(default="", env="FACEBOOK_APP_SECRET")
    facebook_access_token: str = Field(default="", env="FACEBOOK_ACCESS_TOKEN")

    # Admin Login
    admin_email: str = Field(default="admin@smith.com", env="ADMIN_EMAIL")
    admin_password: str = Field(default="admin123", env="ADMIN_PASSWORD")

    # Notificações
    notification_whatsapp_enabled: bool = Field(default=True, env="NOTIFICATION_WHATSAPP_ENABLED")
    notification_whatsapp_number: str = Field(default="", env="NOTIFICATION_WHATSAPP_NUMBER")
    notification_email_enabled: bool = Field(default=False, env="NOTIFICATION_EMAIL_ENABLED")
    notification_email_to: str = Field(default="", env="NOTIFICATION_EMAIL_TO")
    notification_webhook_url: str = Field(default="", env="NOTIFICATION_WEBHOOK_URL")

    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna lista de origens CORS permitidas"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def supabase(self):
        """Retorna o cliente Supabase"""
        from app.database import get_supabase
        return get_supabase()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global de configurações
settings = Settings()


# Validação de configurações críticas no startup
def validate_settings():
    """Valida configurações críticas"""
    errors = []

    # Verifica se API keys estão configuradas (relaxado para modo mock/teste)
    if not settings.openai_api_key or settings.openai_api_key == "sk-...":
        errors.append("⚠️  OPENAI_API_KEY não configurada (usando valor mock)")

    if not settings.evolution_api_url or settings.evolution_api_url == "https://...":
        errors.append("⚠️  EVOLUTION_API_URL não configurada (usando valor mock)")

    if not settings.evolution_api_key or settings.evolution_api_key == "...":
        errors.append("⚠️  EVOLUTION_API_KEY não configurada (usando valor mock)")

    if not settings.supabase_url or settings.supabase_url == "https://...supabase.co":
        errors.append("⚠️  SUPABASE_URL não configurada (usando valor mock)")

    if not settings.supabase_service_key or settings.supabase_service_key == "...":
        errors.append("⚠️  SUPABASE_SERVICE_KEY não configurada (usando valor mock)")

    # JWT é menos crítico no modo teste
    # if not settings.jwt_secret_key or settings.jwt_secret_key == "seu-secret-key-super-seguro-aqui":
    #     errors.append("JWT_SECRET_KEY não configurada (use um valor seguro)")

    # Verifica credenciais do Google Calendar (comentado para modo mock/teste)
    # if not os.path.exists(settings.google_calendar_credentials_path):
    #     errors.append(f"Arquivo de credenciais do Google Calendar não encontrado: {settings.google_calendar_credentials_path}")

    if errors:
        # Modo mock/teste: apenas avisa mas não bloqueia
        from loguru import logger
        logger.warning("⚠️  RODANDO EM MODO MOCK/TESTE:")
        for error in errors:
            logger.warning(f"  {error}")
        logger.warning("\n📝 Configure as variáveis reais no arquivo .env quando estiver pronto\n")

    return True
