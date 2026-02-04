"""
Script para criar notificações de teste
Execute: python test_notifications.py
"""

import requests
import json

API_URL = "http://localhost:8000"

notifications = [
    {
        "tipo": "lead_quente",
        "prioridade": "high",
        "titulo": "Lead Quente sem Contato!",
        "mensagem": "O lead 'João Silva' está marcado como quente mas não tem interação há 3 dias.",
        "link": "/crm",
    },
    {
        "tipo": "agendamento",
        "prioridade": "urgent",
        "titulo": "Reunião em 30 minutos",
        "mensagem": "Você tem uma reunião agendada com 'Maria Santos' em 30 minutos.",
        "link": "/agendamentos",
    },
    {
        "tipo": "novo_lead",
        "prioridade": "medium",
        "titulo": "Novo Lead Capturado",
        "mensagem": "Um novo lead 'Pedro Costa' entrou pelo formulário do site.",
        "link": "/crm",
    },
    {
        "tipo": "proposta_vencendo",
        "prioridade": "high",
        "titulo": "Proposta Expirando em 2 dias",
        "mensagem": "A proposta enviada para 'Tech Solutions' vence em 2 dias.",
        "link": "/pipeline",
    },
    {
        "tipo": "lead_parado",
        "prioridade": "medium",
        "titulo": "Lead Parado há 5 dias",
        "mensagem": "O lead 'Ana Oliveira' está no estágio 'Negociação' há 5 dias sem movimentação.",
        "link": "/crm",
    },
    {
        "tipo": "follow_up",
        "prioridade": "medium",
        "titulo": "Follow-up Agendado",
        "mensagem": "Fazer follow-up com 'Carlos Mendes' sobre proposta enviada.",
        "link": "/conversas",
    },
    {
        "tipo": "sistema",
        "prioridade": "low",
        "titulo": "Sistema Atualizado",
        "mensagem": "O Smith 2.0 foi atualizado com novas funcionalidades: Notificações e Busca Global!",
        "link": "/dashboard",
    },
]

print("Criando notificacoes de teste...\n")

for i, notif in enumerate(notifications, 1):
    try:
        response = requests.post(f"{API_URL}/api/notifications", json=notif)

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] {i}. Criada: {notif['titulo']}")
            print(f"   Prioridade: {notif['prioridade']} | Tipo: {notif['tipo']}")
        else:
            print(f"[ERRO] {i}. Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERRO] {i}. Erro na requisicao: {e}")
    print()

print("\nNotificacoes de teste criadas!")
print("\nProximos passos:")
print("1. Acesse o frontend: http://localhost:3000")
print("2. Veja o sino no header com contador de notificacoes")
print("3. Clique no sino para ver o dropdown")
print("4. Acesse /notificacoes para ver a pagina completa")
