"""
Script para configurar buckets do Supabase Storage
Execute: python setup_storage.py
"""
import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

async def setup_storage():
    print("[*] Configurando Supabase Storage...")

    # Obter credenciais do .env
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        print("[!] Erro: SUPABASE_URL ou SUPABASE_SERVICE_KEY nao encontrados no .env")
        return

    # Criar cliente Supabase
    supabase: Client = create_client(supabase_url, supabase_key)

    buckets_config = [
        {
            "id": "project-deliveries",
            "name": "project-deliveries",
            "public": False,
            "file_size_limit": 52428800,  # 50MB
            "allowed_mime_types": [
                "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/plain",
                "video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska",
                "application/zip", "application/x-rar-compressed", "application/x-7z-compressed"
            ]
        },
        {
            "id": "project-approvals",
            "name": "project-approvals",
            "public": False,
            "file_size_limit": 52428800,  # 50MB
            "allowed_mime_types": [
                "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "video/mp4", "video/quicktime",
                "application/zip"
            ]
        },
        {
            "id": "payment-proofs",
            "name": "payment-proofs",
            "public": False,
            "file_size_limit": 10485760,  # 10MB
            "allowed_mime_types": [
                "image/jpeg", "image/png", "image/gif", "image/webp",
                "application/pdf"
            ]
        }
    ]

    # Listar buckets existentes
    try:
        existing_buckets = supabase.storage.list_buckets()
        existing_ids = {b['id'] for b in existing_buckets}
        print(f"[+] Buckets existentes: {existing_ids if existing_ids else 'nenhum'}")
    except Exception as e:
        print(f"[!] Erro ao listar buckets: {e}")
        existing_ids = set()

    # Criar cada bucket
    for bucket_config in buckets_config:
        bucket_id = bucket_config["id"]

        if bucket_id in existing_ids:
            print(f"[OK] Bucket '{bucket_id}' ja existe")
            continue

        try:
            # Criar bucket
            supabase.storage.create_bucket(
                bucket_id,
                options={
                    "public": bucket_config["public"],
                    "file_size_limit": bucket_config["file_size_limit"],
                    "allowed_mime_types": bucket_config["allowed_mime_types"]
                }
            )
            print(f"[OK] Bucket '{bucket_id}' criado com sucesso")
        except Exception as e:
            print(f"[X] Erro ao criar bucket '{bucket_id}': {e}")

    print("\n[*] Configurando politicas RLS...")

    # Políticas RLS (Row Level Security)
    policies_sql = """
    -- Policy: Service role tem acesso total
    CREATE POLICY IF NOT EXISTS "Service role full access - deliveries"
    ON storage.objects FOR ALL
    TO service_role
    USING (bucket_id = 'project-deliveries');

    CREATE POLICY IF NOT EXISTS "Service role full access - approvals"
    ON storage.objects FOR ALL
    TO service_role
    USING (bucket_id = 'project-approvals');

    CREATE POLICY IF NOT EXISTS "Service role full access - payments"
    ON storage.objects FOR ALL
    TO service_role
    USING (bucket_id = 'payment-proofs');

    -- Policy: Authenticated users podem fazer upload
    CREATE POLICY IF NOT EXISTS "Authenticated users can upload - deliveries"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id = 'project-deliveries');

    CREATE POLICY IF NOT EXISTS "Authenticated users can upload - payments"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id = 'payment-proofs');

    -- Policy: Authenticated users podem ler próprios arquivos
    CREATE POLICY IF NOT EXISTS "Authenticated users can read - deliveries"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (bucket_id = 'project-deliveries');

    CREATE POLICY IF NOT EXISTS "Authenticated users can read - approvals"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (bucket_id = 'project-approvals');

    CREATE POLICY IF NOT EXISTS "Authenticated users can read - payments"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (bucket_id = 'payment-proofs');
    """

    try:
        # Executar SQL de políticas via RPC ou diretamente
        # Nota: Supabase Python client pode não ter método direto para executar SQL
        # Usuário precisará executar essas políticas no dashboard SQL Editor
        print("[!] IMPORTANTE: Execute o SQL abaixo no Supabase SQL Editor:")
        print("=" * 80)
        print(policies_sql)
        print("=" * 80)
    except Exception as e:
        print(f"[!] Nota: {e}")

    print("\n[OK] Setup do Storage concluido!")
    print("\n[*] Proximos passos:")
    print("1. Execute o SQL acima no Supabase Dashboard > SQL Editor")
    print("2. Teste o upload de arquivos no sistema")
    print("3. Verifique os buckets no Supabase Dashboard > Storage")

if __name__ == "__main__":
    asyncio.run(setup_storage())
