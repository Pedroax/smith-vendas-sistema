"""
Configuração e inicialização do cliente Supabase e SQLAlchemy
"""
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
from loguru import logger


# Cliente Supabase global
supabase: Client = None

# SQLAlchemy para conversas (acesso direto ao PostgreSQL)
# Construir URL de conexão a partir das configurações
from urllib.parse import quote_plus

db_password = quote_plus(settings.supabase_db_password)
project_id = settings.supabase_url.replace('https://', '').replace('http://', '').split('.')[0]

# Connection string para Supabase PostgreSQL - Direct Connection
# Formato: postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres
DATABASE_URL = f"postgresql+psycopg2://postgres:{db_password}@db.{project_id}.supabase.co:5432/postgres"

# Engine SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "connect_timeout": 10,
        "sslmode": "require"
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_supabase() -> Client:
    """
    Inicializa o cliente Supabase

    Returns:
        Cliente Supabase configurado
    """
    global supabase

    if supabase is not None:
        return supabase

    try:
        # Criar cliente usando service_role key para acesso completo
        supabase = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key
        )

        logger.info(f"✅ Supabase conectado: {settings.supabase_url}")

        return supabase

    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao Supabase: {e}")
        raise


def get_supabase() -> Client:
    """
    Retorna o cliente Supabase (inicializa se necessário)

    Returns:
        Cliente Supabase
    """
    if supabase is None:
        return init_supabase()

    return supabase


def get_db():
    """
    Dependency para obter sessão do banco de dados

    Yields:
        Session do SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
