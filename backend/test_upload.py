"""
Script para testar upload de arquivos
"""
import os
import io
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def test_upload():
    print("[*] Testando upload no Supabase Storage...")

    # Criar cliente
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    supabase = create_client(supabase_url, supabase_key)

    # Criar diferentes tipos de arquivo de teste
    # Imagem PNG mínima (1x1 transparente)
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
        0x42, 0x60, 0x82
    ])

    # Testar upload em cada bucket com tipo correto
    buckets = [
        ("project-deliveries", "test-project-123/test-item-456/test.txt", b"Teste", "text/plain"),
        ("project-approvals", "test-project-123/test-approval-789/test.png", png_bytes, "image/png"),
        ("payment-proofs", "test-project-123/test-payment-999/test.png", png_bytes, "image/png")
    ]

    for bucket_id, file_path, content, mime_type in buckets:
        try:
            print(f"\n[*] Testando bucket: {bucket_id}")

            # Upload
            result = supabase.storage.from_(bucket_id).upload(
                file_path,
                content,
                file_options={"content-type": mime_type}
            )

            print(f"[OK] Upload bem-sucedido: {file_path}")

            # Gerar URL assinada
            signed_url = supabase.storage.from_(bucket_id).create_signed_url(
                file_path,
                expires_in=3600  # 1 hora
            )

            print(f"[OK] URL assinada gerada: {signed_url['signedURL'][:80]}...")

            # Deletar arquivo de teste
            supabase.storage.from_(bucket_id).remove([file_path])
            print(f"[OK] Arquivo de teste removido")

        except Exception as e:
            print(f"[X] Erro no bucket {bucket_id}: {e}")

    print("\n[OK] Teste de upload concluido!")

if __name__ == "__main__":
    test_upload()
