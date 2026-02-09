"""
Repository para gerenciar faturas (Invoices)
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from loguru import logger
from supabase import Client

from app.database import get_supabase
from app.models.invoice import (
    Invoice,
    InvoiceCreate,
    InvoiceStatus,
    InvoiceUpdate,
    InvoiceStats
)


class InvoiceRepository:
    """Repository para operações com faturas"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_invoice(self, data: InvoiceCreate) -> Invoice:
        """Cria uma nova fatura"""
        logger.info(f"Criando fatura para projeto {data.project_id}")

        # Calcular valor final
        valor_final = data.valor - data.desconto

        # Gerar número da fatura (INV-YYYY-XXX)
        ano_atual = datetime.now().year

        # Buscar última fatura do ano
        result = self.supabase.table("invoices")\
            .select("numero_fatura")\
            .like("numero_fatura", f"INV-{ano_atual}-%")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        if result.data:
            ultimo_numero = int(result.data[0]["numero_fatura"].split("-")[-1])
            proximo_numero = ultimo_numero + 1
        else:
            proximo_numero = 1

        numero_fatura = f"INV-{ano_atual}-{proximo_numero:03d}"

        # Preparar dados
        invoice_data = {
            "project_id": data.project_id,
            "numero_fatura": numero_fatura,
            "descricao": data.descricao,
            "valor": float(data.valor),
            "desconto": float(data.desconto),
            "valor_final": float(valor_final),
            "data_emissao": data.data_emissao.isoformat() if data.data_emissao else date.today().isoformat(),
            "data_vencimento": data.data_vencimento.isoformat(),
            "metodo_pagamento": data.metodo_pagamento.value if data.metodo_pagamento else None,
            "notas_admin": data.notas_admin,
            "status": InvoiceStatus.PENDENTE.value
        }

        # Inserir no banco
        result = self.supabase.table("invoices").insert(invoice_data).execute()

        if not result.data:
            raise Exception("Erro ao criar fatura")

        logger.success(f"Fatura {numero_fatura} criada com sucesso")
        return await self.get_invoice_by_id(UUID(result.data[0]["id"]))

    async def get_invoice_by_id(self, invoice_id: UUID) -> Optional[Invoice]:
        """Busca uma fatura por ID (com joins de project e client)"""
        result = self.supabase.table("invoices")\
            .select("""
                *,
                projects (
                    nome,
                    leads (nome)
                )
            """)\
            .eq("id", str(invoice_id))\
            .single()\
            .execute()

        if not result.data:
            return None

        # Flatten data
        invoice_data = result.data
        if invoice_data.get("projects"):
            invoice_data["project_nome"] = invoice_data["projects"]["nome"]
            if invoice_data["projects"].get("leads"):
                invoice_data["client_nome"] = invoice_data["projects"]["leads"]["nome"]
            del invoice_data["projects"]

        return Invoice(**invoice_data)

    async def list_invoices(
        self,
        project_id: Optional[int] = None,
        status: Optional[InvoiceStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Invoice]:
        """Lista faturas com filtros opcionais"""
        query = self.supabase.table("invoices")\
            .select("""
                *,
                projects (
                    nome,
                    leads (nome)
                )
            """)

        if project_id:
            query = query.eq("project_id", project_id)

        if status:
            query = query.eq("status", status.value)

        result = query.order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        invoices = []
        for invoice_data in result.data:
            # Flatten data
            if invoice_data.get("projects"):
                invoice_data["project_nome"] = invoice_data["projects"]["nome"]
                if invoice_data["projects"].get("leads"):
                    invoice_data["client_nome"] = invoice_data["projects"]["leads"]["nome"]
                del invoice_data["projects"]

            invoices.append(Invoice(**invoice_data))

        return invoices

    async def update_invoice(
        self,
        invoice_id: UUID,
        data: InvoiceUpdate
    ) -> Invoice:
        """Atualiza uma fatura"""
        logger.info(f"Atualizando fatura {invoice_id}")

        update_data = data.model_dump(exclude_unset=True)

        # Se valor ou desconto mudou, recalcular valor_final
        if "valor" in update_data or "desconto" in update_data:
            invoice = await self.get_invoice_by_id(invoice_id)
            if not invoice:
                raise ValueError("Fatura não encontrada")

            novo_valor = Decimal(str(update_data.get("valor", invoice.valor)))
            novo_desconto = Decimal(str(update_data.get("desconto", invoice.desconto)))
            update_data["valor_final"] = float(novo_valor - novo_desconto)

        # Converter enums para valores
        if "status" in update_data and isinstance(update_data["status"], InvoiceStatus):
            update_data["status"] = update_data["status"].value

        if "metodo_pagamento" in update_data and update_data["metodo_pagamento"]:
            update_data["metodo_pagamento"] = update_data["metodo_pagamento"].value

        # Converter Decimal para float
        for key in ["valor", "desconto"]:
            if key in update_data:
                update_data[key] = float(update_data[key])

        # Converter date para string
        for key in ["data_vencimento"]:
            if key in update_data and update_data[key]:
                update_data[key] = update_data[key].isoformat()

        result = self.supabase.table("invoices")\
            .update(update_data)\
            .eq("id", str(invoice_id))\
            .execute()

        if not result.data:
            raise Exception("Erro ao atualizar fatura")

        logger.success(f"Fatura {invoice_id} atualizada")
        return await self.get_invoice_by_id(invoice_id)

    async def upload_comprovante(
        self,
        invoice_id: UUID,
        comprovante_url: str
    ) -> Invoice:
        """Cliente faz upload do comprovante de pagamento"""
        logger.info(f"Upload de comprovante para fatura {invoice_id}")

        update_data = {
            "comprovante_url": comprovante_url,
            "comprovante_enviado_em": datetime.now().isoformat(),
            "status": InvoiceStatus.AGUARDANDO_CONF.value
        }

        result = self.supabase.table("invoices")\
            .update(update_data)\
            .eq("id", str(invoice_id))\
            .execute()

        if not result.data:
            raise Exception("Erro ao fazer upload do comprovante")

        logger.success(f"Comprovante enviado para fatura {invoice_id}")
        return await self.get_invoice_by_id(invoice_id)

    async def confirmar_pagamento(
        self,
        invoice_id: UUID,
        admin_id: UUID,
        data_pagamento: date,
        notas_admin: Optional[str] = None
    ) -> Invoice:
        """Admin confirma o pagamento"""
        logger.info(f"Confirmando pagamento da fatura {invoice_id}")

        update_data = {
            "status": InvoiceStatus.PAGO.value,
            "data_pagamento": data_pagamento.isoformat(),
            "confirmado_por": str(admin_id),
            "confirmado_em": datetime.now().isoformat()
        }

        if notas_admin:
            update_data["notas_admin"] = notas_admin

        result = self.supabase.table("invoices")\
            .update(update_data)\
            .eq("id", str(invoice_id))\
            .execute()

        if not result.data:
            raise Exception("Erro ao confirmar pagamento")

        logger.success(f"Pagamento confirmado para fatura {invoice_id}")
        return await self.get_invoice_by_id(invoice_id)

    async def upload_nota_fiscal(
        self,
        invoice_id: UUID,
        nota_fiscal_url: str
    ) -> Invoice:
        """Admin faz upload da nota fiscal"""
        logger.info(f"Upload de NF para fatura {invoice_id}")

        result = self.supabase.table("invoices")\
            .update({"nota_fiscal_url": nota_fiscal_url})\
            .eq("id", str(invoice_id))\
            .execute()

        if not result.data:
            raise Exception("Erro ao fazer upload da nota fiscal")

        logger.success(f"Nota fiscal enviada para fatura {invoice_id}")
        return await self.get_invoice_by_id(invoice_id)

    async def get_stats(self) -> InvoiceStats:
        """Retorna estatísticas gerais de faturas"""
        # Buscar todas as faturas
        result = self.supabase.table("invoices")\
            .select("*")\
            .execute()

        faturas = result.data

        total_pago = Decimal("0")
        total_pendente = Decimal("0")
        total_atrasado = Decimal("0")

        qtd_pago = 0
        qtd_pendente = 0
        qtd_atrasado = 0
        qtd_aguardando = 0

        for f in faturas:
            valor = Decimal(str(f["valor_final"]))

            if f["status"] == InvoiceStatus.PAGO.value:
                total_pago += valor
                qtd_pago += 1
            elif f["status"] == InvoiceStatus.PENDENTE.value:
                total_pendente += valor
                qtd_pendente += 1
            elif f["status"] == InvoiceStatus.ATRASADO.value:
                total_atrasado += valor
                qtd_atrasado += 1
            elif f["status"] == InvoiceStatus.AGUARDANDO_CONF.value:
                qtd_aguardando += 1

        # Buscar próximos vencimentos (próximos 30 dias)
        proximos = self.supabase.table("invoices")\
            .select("""
                *,
                projects (
                    nome,
                    leads (nome)
                )
            """)\
            .in_("status", [InvoiceStatus.PENDENTE.value, InvoiceStatus.AGUARDANDO_CONF.value])\
            .gte("data_vencimento", date.today().isoformat())\
            .order("data_vencimento")\
            .limit(5)\
            .execute()

        proximos_vencimentos = []
        for invoice_data in proximos.data:
            if invoice_data.get("projects"):
                invoice_data["project_nome"] = invoice_data["projects"]["nome"]
                if invoice_data["projects"].get("leads"):
                    invoice_data["client_nome"] = invoice_data["projects"]["leads"]["nome"]
                del invoice_data["projects"]
            proximos_vencimentos.append(Invoice(**invoice_data))

        return InvoiceStats(
            total_faturado=total_pago + total_pendente + total_atrasado,
            total_pago=total_pago,
            total_pendente=total_pendente,
            total_atrasado=total_atrasado,
            quantidade_pago=qtd_pago,
            quantidade_pendente=qtd_pendente,
            quantidade_atrasado=qtd_atrasado,
            quantidade_aguardando_conf=qtd_aguardando,
            proximos_vencimentos=proximos_vencimentos
        )

    async def delete_invoice(self, invoice_id: UUID) -> bool:
        """Deleta uma fatura (soft delete - marca como cancelado)"""
        logger.info(f"Deletando fatura {invoice_id}")

        result = self.supabase.table("invoices")\
            .update({"status": InvoiceStatus.CANCELADO.value})\
            .eq("id", str(invoice_id))\
            .execute()

        return bool(result.data)


def get_invoice_repository() -> InvoiceRepository:
    """Retorna instância do repository"""
    return InvoiceRepository(get_supabase())
