"""
API endpoints para Faturas (Invoices)
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.invoice import (
    Invoice,
    InvoiceConfirmarPagamento,
    InvoiceCreate,
    InvoiceStats,
    InvoiceStatus,
    InvoiceUpdate,
    InvoiceUploadComprovante,
)
from app.repository.invoice_repository import get_invoice_repository

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


@router.post("/", response_model=Invoice, status_code=201)
async def create_invoice(data: InvoiceCreate):
    """
    Cria uma nova fatura (ADMIN ONLY)

    - Gera número de fatura automaticamente
    - Calcula valor final com desconto
    - Status inicial: pendente
    """
    try:
        repo = get_invoice_repository()
        invoice = await repo.create_invoice(data)
        return invoice
    except Exception as e:
        logger.error(f"Erro ao criar fatura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[Invoice])
async def list_invoices(
    project_id: Optional[int] = Query(None, description="Filtrar por projeto"),
    status: Optional[InvoiceStatus] = Query(None, description="Filtrar por status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Lista faturas com filtros opcionais

    - Se project_id fornecido: retorna apenas do projeto (cliente vê só dele)
    - Se status fornecido: filtra por status
    - Admin vê todas, cliente vê só as dele
    """
    try:
        repo = get_invoice_repository()
        invoices = await repo.list_invoices(
            project_id=project_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return invoices
    except Exception as e:
        logger.error(f"Erro ao listar faturas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=InvoiceStats)
async def get_stats():
    """
    Retorna estatísticas de faturas (ADMIN ONLY)

    - Total faturado, pendente, atrasado, pago
    - Quantidades por status
    - Próximos vencimentos
    """
    try:
        repo = get_invoice_repository()
        stats = await repo.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: UUID):
    """Busca uma fatura por ID"""
    try:
        repo = get_invoice_repository()
        invoice = await repo.get_invoice_by_id(invoice_id)

        if not invoice:
            raise HTTPException(status_code=404, detail="Fatura não encontrada")

        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar fatura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: UUID, data: InvoiceUpdate):
    """
    Atualiza uma fatura (ADMIN ONLY)

    - Pode atualizar valores, datas, status
    - Recalcula valor_final automaticamente
    """
    try:
        repo = get_invoice_repository()

        # Verificar se existe
        existing = await repo.get_invoice_by_id(invoice_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Fatura não encontrada")

        invoice = await repo.update_invoice(invoice_id, data)
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar fatura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{invoice_id}/upload-comprovante", response_model=Invoice)
async def upload_comprovante(invoice_id: UUID, data: InvoiceUploadComprovante):
    """
    Cliente faz upload do comprovante de pagamento

    - Atualiza comprovante_url
    - Muda status para 'aguardando_conf'
    - Registra timestamp do envio
    """
    try:
        repo = get_invoice_repository()

        # Verificar se existe
        existing = await repo.get_invoice_by_id(invoice_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Fatura não encontrada")

        # Não pode enviar comprovante se já estiver paga ou cancelada
        if existing.status in [InvoiceStatus.PAGO, InvoiceStatus.CANCELADO]:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível enviar comprovante. Status atual: {existing.status.value}"
            )

        invoice = await repo.upload_comprovante(invoice_id, data.comprovante_url)
        logger.info(f"Comprovante enviado para fatura {invoice_id}")
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer upload do comprovante: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{invoice_id}/confirmar-pagamento", response_model=Invoice)
async def confirmar_pagamento(invoice_id: UUID, data: InvoiceConfirmarPagamento):
    """
    Admin confirma o pagamento da fatura

    - Muda status para 'pago'
    - Registra data de pagamento
    - Registra quem confirmou
    """
    try:
        repo = get_invoice_repository()

        # Verificar se existe
        existing = await repo.get_invoice_by_id(invoice_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Fatura não encontrada")

        # TODO: Pegar admin_id da sessão/auth
        # Por enquanto, usar UUID dummy
        admin_id = UUID("00000000-0000-0000-0000-000000000000")

        invoice = await repo.confirmar_pagamento(
            invoice_id=invoice_id,
            admin_id=admin_id,
            data_pagamento=data.data_pagamento,
            notas_admin=data.notas_admin
        )

        logger.success(f"Pagamento confirmado para fatura {invoice_id}")
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao confirmar pagamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{invoice_id}/upload-nota-fiscal", response_model=Invoice)
async def upload_nota_fiscal(invoice_id: UUID, nota_fiscal_url: str):
    """
    Admin faz upload da nota fiscal

    - Armazena URL da NF
    - Cliente poderá baixar
    """
    try:
        repo = get_invoice_repository()

        # Verificar se existe
        existing = await repo.get_invoice_by_id(invoice_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Fatura não encontrada")

        invoice = await repo.upload_nota_fiscal(invoice_id, nota_fiscal_url)
        logger.info(f"Nota fiscal enviada para fatura {invoice_id}")
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer upload da nota fiscal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: UUID):
    """
    Deleta (cancela) uma fatura (ADMIN ONLY)

    - Soft delete: marca como cancelado
    """
    try:
        repo = get_invoice_repository()

        # Verificar se existe
        existing = await repo.get_invoice_by_id(invoice_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Fatura não encontrada")

        success = await repo.delete_invoice(invoice_id)

        if not success:
            raise HTTPException(status_code=500, detail="Erro ao deletar fatura")

        logger.warning(f"Fatura {invoice_id} cancelada")
        return {"success": True, "message": "Fatura cancelada com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar fatura: {e}")
        raise HTTPException(status_code=500, detail=str(e))
