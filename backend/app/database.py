"""
Conexão com o PostgreSQL (Railway)

- `get_supabase()` devolve um PostgresClient com a mesma API do supabase-py usada
  nos repositories (o nome foi mantido para não mexer em todos os call sites).
- `SessionLocal`/`get_db` continuam servindo os repositories que usam SQLAlchemy.
- `init_db()` valida a conexão e aplica as migrations `migrations/railway_*.sql`.
"""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

from app.config import settings
from app.pg_client import PostgresClient


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _normalize_database_url(url: str) -> str:
    """
    Força o driver psycopg2 (o PostgresClient depende dele).
    A Railway entrega postgresql:// e, a partir do SQLAlchemy 2.1,
    esse esquema passou a usar o psycopg 3 por padrão.
    """
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


engine = create_engine(
    _normalize_database_url(settings.database_url),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 10},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

_client: PostgresClient = None


def get_supabase() -> PostgresClient:
    """Retorna o cliente Postgres global (API compatível com supabase-py)"""
    global _client
    if _client is None:
        _client = PostgresClient(engine)
    return _client


def run_migrations():
    """
    Aplica, em ordem, os arquivos migrations/railway_*.sql ainda não aplicados.
    Cada arquivo roda numa transação e fica registrado em schema_migrations.
    """
    connection = engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " filename TEXT PRIMARY KEY,"
            " applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
        )
        connection.commit()

        cursor.execute("SELECT filename FROM schema_migrations")
        applied = {row[0] for row in cursor.fetchall()}

        for path in sorted(MIGRATIONS_DIR.glob("railway_*.sql")):
            if path.name in applied:
                continue

            logger.info(f"🗄️  Aplicando migration {path.name}...")
            try:
                cursor.execute(path.read_text(encoding="utf-8"))
                cursor.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
                )
                connection.commit()
                logger.success(f"✅ Migration {path.name} aplicada")
            except Exception:
                connection.rollback()
                logger.error(f"❌ Falha ao aplicar migration {path.name}")
                raise

        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"🗄️  Tabelas no banco: {', '.join(tables)}")
    finally:
        connection.close()


def init_db() -> PostgresClient:
    """Valida a conexão, aplica migrations e devolve o cliente"""
    run_migrations()
    logger.info("✅ PostgreSQL conectado")
    return get_supabase()


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
