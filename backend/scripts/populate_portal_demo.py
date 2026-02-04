"""
Script para popular o Portal do Cliente com dados de demonstrao
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o diretrio raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from app.repository.client_portal_repository import get_client_portal_repository
from app.models.client_portal import (
    ClientCreate, ProjectCreate, StageCreate,
    DeliveryItemCreate, ApprovalItemCreate, ApprovalStatus,
    TimelineEventCreate, TimelineEventType,
    PaymentCreate, PaymentStatus
)


async def populate_demo_data():
    """Popular dados de demonstrao"""
    repo = get_client_portal_repository()

    print(">> Populando Portal do Cliente com dados de demonstracao...\n")

    # ============================================
    # 1. CRIAR CLIENTE
    # ============================================
    print("[1/5] Criando cliente de demonstracao...")
    client = await repo.create_client(ClientCreate(
        nome="Pedro Machado",
        email="pedro@automatex.com",
        telefone="61 8256-3956",
        empresa="Automatex",
        documento="12.345.678/0001-90",
        senha="123456"  # Senha simples para demo
    ))

    if not client:
        print("[ERRO] Erro ao criar cliente")
        return

    print(f"[OK] Cliente criado: {client.nome} ({client.email})")
    print(f"   Login: pedro@automatex.com")
    print(f"   Senha: 123456\n")

    # ============================================
    # 2. CRIAR PROJETO 1 - Site Institucional (Em Desenvolvimento)
    # ============================================
    print("[2/5] Criando Projeto 1: Site Institucional...")

    project1 = await repo.create_project(
        ProjectCreate(
            client_id=client.id,
            nome="Site Institucional Automatex",
            descricao="Desenvolvimento do novo site institucional da Automatex com design moderno e responsivo",
            tipo="Site Institucional",
            valor_total=8500.00,
            data_inicio=datetime.now() - timedelta(days=15),
            data_previsao=datetime.now() + timedelta(days=30)
        ),
        template="site_institucional"
    )

    if not project1:
        print("[ERRO] Erro ao criar projeto 1")
        return

    print(f"[OK] Projeto criado: {project1.nome}")
    print(f"   Link de acesso: http://localhost:3002/portal/projeto/{project1.access_token}")

    # Avanar para etapa "Desenvolvimento"
    stages1 = await repo.list_project_stages(project1.id)
    for i in range(3):  # Marcar 3 etapas como concludas (Briefing, Wireframe, Design)
        if i < len(stages1):
            await repo.update_stage(stages1[i].id, {"concluida": True, "data_conclusao": datetime.now() - timedelta(days=10-i*3)})

    # Avanar progresso
    await repo.update_project(project1.id, {"status": "em_desenvolvimento", "etapa_atual": 3, "progresso": 50})

    # Adicionar entregas pendentes
    print("    Adicionando entregas pendentes...")
    delivery1 = await repo.create_delivery_item(DeliveryItemCreate(
        project_id=project1.id,
        nome="Textos das pginas (Home, Sobre, Servios)",
        descricao="Envie os textos finais que sero usados no site",
        obrigatorio=True
    ))

    delivery2 = await repo.create_delivery_item(DeliveryItemCreate(
        project_id=project1.id,
        nome="Fotos da equipe em alta resoluo",
        descricao="Fotos profissionais da equipe para a pgina 'Sobre'",
        obrigatorio=False
    ))

    # Adicionar aprovao aguardando
    print("   [OK] Adicionando aprovaes pendentes...")
    approval1 = await repo.create_approval_item(ApprovalItemCreate(
        project_id=project1.id,
        titulo="Design do Site - Verso 2",
        descricao="Ajustes solicitados na primeira verso foram aplicados. Por favor, revise e aprove.",
        tipo="link",
        link_externo="https://www.figma.com/design-site-automatex-v2"
    ))

    # Adicionar eventos na timeline
    print("    Adicionando eventos na timeline...")
    await repo.add_timeline_event(TimelineEventCreate(
        project_id=project1.id,
        tipo=TimelineEventType.ETAPA_AVANCADA,
        titulo="Design aprovado!",
        descricao="O design do site foi aprovado e avanamos para desenvolvimento",
        is_client_action=False
    ))

    await repo.add_timeline_event(TimelineEventCreate(
        project_id=project1.id,
        tipo=TimelineEventType.MATERIAL_SOLICITADO,
        titulo="Materiais solicitados",
        descricao="Precisamos dos textos e fotos para continuar",
        is_client_action=False
    ))

    # Adicionar pagamentos
    print("    Adicionando pagamentos...")
    payment1 = await repo.create_payment(PaymentCreate(
        project_id=project1.id,
        descricao="Entrada - 50%",
        valor=4250.00,
        data_vencimento=datetime.now() - timedelta(days=15)
    ))
    await repo.update_payment(payment1.id, {"status": PaymentStatus.PAGO, "data_pagamento": datetime.now() - timedelta(days=14)})

    payment2 = await repo.create_payment(PaymentCreate(
        project_id=project1.id,
        descricao="Final - 50%",
        valor=4250.00,
        data_vencimento=datetime.now() + timedelta(days=30)
    ))

    print("[OK] Projeto 1 configurado!\n")

    # ============================================
    # 3. CRIAR PROJETO 2 - Identidade Visual (Aguardando Aprovao)
    # ============================================
    print("[2/5] Criando Projeto 2: Identidade Visual...")

    project2 = await repo.create_project(
        ProjectCreate(
            client_id=client.id,
            nome="Identidade Visual - Nova Marca",
            descricao="Criao completa da identidade visual: logo, paleta de cores, tipografia e aplicaes",
            tipo="Identidade Visual",
            valor_total=5500.00,
            data_inicio=datetime.now() - timedelta(days=45),
            data_previsao=datetime.now() + timedelta(days=7)
        ),
        template="identidade_visual"
    )

    print(f"[OK] Projeto criado: {project2.nome}")

    # Avanar para etapa "Refinamento"
    stages2 = await repo.list_project_stages(project2.id)
    for i in range(4):  # Marcar 4 etapas como concludas
        if i < len(stages2):
            await repo.update_stage(stages2[i].id, {"concluida": True, "data_conclusao": datetime.now() - timedelta(days=40-i*10)})

    await repo.update_project(project2.id, {"status": "aprovacao", "etapa_atual": 4, "progresso": 80})

    # Adicionar aprovao aguardando
    print("   [OK] Adicionando aprovao aguardando...")
    approval2 = await repo.create_approval_item(ApprovalItemCreate(
        project_id=project2.id,
        titulo="Logo Final - Conceito Escolhido",
        descricao="Verso final do logo aps todos os refinamentos",
        tipo="arquivo",
        arquivo_url="https://exemplo.com/logo-final.png"
    ))

    approval3 = await repo.create_approval_item(ApprovalItemCreate(
        project_id=project2.id,
        titulo="Manual de Marca Completo",
        descricao="PDF com todas as aplicaes e diretrizes de uso",
        tipo="arquivo",
        arquivo_url="https://exemplo.com/manual-marca.pdf"
    ))

    # Timeline
    await repo.add_timeline_event(TimelineEventCreate(
        project_id=project2.id,
        tipo=TimelineEventType.APROVACAO_SOLICITADA,
        titulo="Logo e Manual prontos para aprovao",
        descricao="Por favor, revise os arquivos finais",
        is_client_action=False
    ))

    # Pagamento
    payment3 = await repo.create_payment(PaymentCreate(
        project_id=project2.id,
        descricao="Pagamento nico",
        valor=5500.00,
        data_vencimento=datetime.now() + timedelta(days=7)
    ))

    print("[OK] Projeto 2 configurado!\n")

    # ============================================
    # 4. CRIAR PROJETO 3 - Sistema Web (Briefing)
    # ============================================
    print("[2/5] Criando Projeto 3: Sistema Web...")

    project3 = await repo.create_project(
        ProjectCreate(
            client_id=client.id,
            nome="Sistema de Gesto de Clientes",
            descricao="Desenvolvimento de sistema web para gesto de leads e clientes",
            tipo="Sistema Web",
            valor_total=28000.00,
            data_inicio=datetime.now() - timedelta(days=5),
            data_previsao=datetime.now() + timedelta(days=90)
        ),
        template="sistema_web"
    )

    print(f"[OK] Projeto criado: {project3.nome}")

    # Manter na primeira etapa
    await repo.update_project(project3.id, {"status": "briefing", "progresso": 10})

    # Entregas pendentes
    await repo.create_delivery_item(DeliveryItemCreate(
        project_id=project3.id,
        nome="Documento de Requisitos",
        descricao="Documento detalhado com todas as funcionalidades desejadas",
        obrigatorio=True
    ))

    await repo.create_delivery_item(DeliveryItemCreate(
        project_id=project3.id,
        nome="Fluxos de Processo",
        descricao="Diagrama ou descrio dos processos do sistema",
        obrigatorio=True
    ))

    # Timeline
    await repo.add_timeline_event(TimelineEventCreate(
        project_id=project3.id,
        tipo=TimelineEventType.PROJETO_CRIADO,
        titulo="Projeto iniciado",
        descricao="Bem-vindo ao seu novo projeto!",
        is_client_action=False
    ))

    await repo.add_timeline_event(TimelineEventCreate(
        project_id=project3.id,
        tipo=TimelineEventType.MATERIAL_SOLICITADO,
        titulo="Envie os requisitos do sistema",
        descricao="Precisamos entender todas as funcionalidades que voc precisa",
        is_client_action=False
    ))

    # Pagamentos parcelados
    for i in range(4):
        await repo.create_payment(PaymentCreate(
            project_id=project3.id,
            descricao=f"Parcela {i+1}/4",
            valor=7000.00,
            data_vencimento=datetime.now() + timedelta(days=30*i)
        ))

    print("[OK] Projeto 3 configurado!\n")

    # ============================================
    # 5. CRIAR PROJETO 4 - Concludo
    # ============================================
    print("[2/5] Criando Projeto 4: Landing Page (Concludo)...")

    project4 = await repo.create_project(
        ProjectCreate(
            client_id=client.id,
            nome="Landing Page Campanha Black Friday",
            descricao="Pgina de captura de leads para campanha promocional",
            tipo="Landing Page",
            valor_total=2800.00,
            data_inicio=datetime.now() - timedelta(days=60),
            data_previsao=datetime.now() - timedelta(days=45)
        )
    )

    print(f"[OK] Projeto criado: {project4.nome}")

    # Marcar todas etapas como concludas
    stages4 = await repo.list_project_stages(project4.id)
    for i, stage in enumerate(stages4):
        await repo.update_stage(stage.id, {"concluida": True, "data_conclusao": datetime.now() - timedelta(days=50-i*5)})

    await repo.update_project(project4.id, {
        "status": "concluido",
        "progresso": 100,
        "concluido_em": datetime.now() - timedelta(days=45)
    })

    # Timeline de concluso
    await repo.add_timeline_event(TimelineEventCreate(
        project_id=project4.id,
        tipo=TimelineEventType.PROJETO_CONCLUIDO,
        titulo="Projeto concludo com sucesso! ",
        descricao="A landing page foi entregue e est no ar",
        is_client_action=False
    ))

    # Pagamento pago
    payment4 = await repo.create_payment(PaymentCreate(
        project_id=project4.id,
        descricao="Pagamento nico",
        valor=2800.00,
        data_vencimento=datetime.now() - timedelta(days=50)
    ))
    await repo.update_payment(payment4.id, {"status": PaymentStatus.PAGO, "data_pagamento": datetime.now() - timedelta(days=48)})

    print("[OK] Projeto 4 configurado!\n")

    # ============================================
    # RESUMO
    # ============================================
    print("=" * 60)
    print("[OK] DADOS DE DEMONSTRAO CRIADOS COM SUCESSO!")
    print("=" * 60)
    print()
    print(" CLIENTE:")
    print(f"   Nome: {client.nome}")
    print(f"   Email: {client.email}")
    print(f"   Senha: 123456")
    print()
    print("[2/5] PROJETOS CRIADOS:")
    print(f"   1. {project1.nome} - Em Desenvolvimento (50%)")
    print(f"   2. {project2.nome} - Aguardando Aprovao (80%)")
    print(f"   3. {project3.nome} - Briefing (10%)")
    print(f"   4. {project4.nome} - Concludo [OK]")
    print()
    print(" ACESSO AO PORTAL:")
    print(f"   URL: http://localhost:3002/portal/login")
    print(f"   Email: {client.email}")
    print(f"   Senha: 123456")
    print()
    print(" LINKS DIRETOS (sem login):")
    print(f"   Projeto 1: http://localhost:3002/portal/projeto/{project1.access_token}")
    print(f"   Projeto 2: http://localhost:3002/portal/projeto/{project2.access_token}")
    print(f"   Projeto 3: http://localhost:3002/portal/projeto/{project3.access_token}")
    print(f"   Projeto 4: http://localhost:3002/portal/projeto/{project4.access_token}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(populate_demo_data())
