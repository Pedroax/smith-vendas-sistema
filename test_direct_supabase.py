"""
Cria notificações direto no Supabase (não precisa do backend)
"""
import os
from supabase import create_client
from datetime import datetime
from uuid import uuid4

# Pegar as credenciais do .env
supabase_url = os.getenv("SUPABASE_URL", "https://byseoksffurotygitfvy.supabase.co")
supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ5c2Vva3NmZnVyb3R5Z2l0ZnZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU4MzU0MTksImV4cCI6MjA1MTQxMTQxOX0.YfTkmZYMp0RdAVAx01ZkUhqLrv0HxJDz7XUcLI4MgQQ")

supabase = create_client(supabase_url, supabase_key)

notifications = [
    {
        "id": str(uuid4()),
        "tipo": "lead_quente",
        "prioridade": "high",
        "titulo": "Lead Quente sem Contato!",
        "mensagem": "O lead 'Joao Silva' esta marcado como quente mas nao tem interacao ha 3 dias.",
        "link": "/crm",
        "lida": False,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid4()),
        "tipo": "agendamento",
        "prioridade": "urgent",
        "titulo": "Reuniao em 30 minutos",
        "mensagem": "Voce tem uma reuniao agendada com 'Maria Santos' em 30 minutos.",
        "link": "/agendamentos",
        "lida": False,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid4()),
        "tipo": "novo_lead",
        "prioridade": "medium",
        "titulo": "Novo Lead Capturado",
        "mensagem": "Um novo lead 'Pedro Costa' entrou pelo formulario do site.",
        "link": "/crm",
        "lida": False,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid4()),
        "tipo": "proposta_vencendo",
        "prioridade": "high",
        "titulo": "Proposta Expirando em 2 dias",
        "mensagem": "A proposta enviada para 'Tech Solutions' vence em 2 dias.",
        "link": "/pipeline",
        "lida": False,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid4()),
        "tipo": "lead_parado",
        "prioridade": "medium",
        "titulo": "Lead Parado ha 5 dias",
        "mensagem": "O lead 'Ana Oliveira' esta no estagio 'Negociacao' ha 5 dias sem movimentacao.",
        "link": "/crm",
        "lida": False,
        "created_at": datetime.utcnow().isoformat()
    },
]

print("Criando notificacoes direto no Supabase...\n")

for i, notif in enumerate(notifications, 1):
    try:
        result = supabase.table("notifications").insert(notif).execute()
        print(f"[OK] {i}. Criada: {notif['titulo']}")
    except Exception as e:
        print(f"[ERRO] {i}. {e}")

print("\nNotificacoes criadas com sucesso!")
print("\nProximos passos:")
print("1. Acesse o frontend: http://localhost:3004")
print("2. Veja o sino no header com contador (5)")
print("3. Clique no sino para ver o dropdown")
print("4. Acesse /notificacoes para ver a pagina completa")
