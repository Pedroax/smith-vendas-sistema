"""
Modelos Pydantic para Faturas (Invoices)
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


class InvoiceStatus(str, Enum):
    """Status possíveis de uma fatura"""
    PENDENTE = "pendente"
    AGUARDANDO_CONF = "aguardando_conf"
    PAGO = "pago"
    ATRASADO = "atrasado"
    CANCELADO = "cancelado"


class MetodoPagamento(str, Enum):
    """Métodos de pagamento aceitos"""
    PIX = "pix"
    TRANSFERENCIA = "transferencia"
    BOLETO = "boleto"
    CARTAO = "cartao"
    DINHEIRO = "dinheiro"
    OUTRO = "outro"


class InvoiceBase(BaseModel):
    """Modelo base de fatura"""
    project_id: UUID
    descricao: str = Field(..., min_length=1, max_length=500)
    valor: Decimal = Field(..., gt=0, decimal_places=2)
    desconto: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    data_vencimento: date
    metodo_pagamento: Optional[MetodoPagamento] = None


class InvoiceCreate(InvoiceBase):
    """Modelo para criação de fatura (usado pelo admin)"""
    data_emissao: Optional[date] = None  # Se não fornecido, usa data atual
    notas_admin: Optional[str] = None


class InvoiceUpdate(BaseModel):
    """Modelo para atualização de fatura"""
    descricao: Optional[str] = Field(None, min_length=1, max_length=500)
    valor: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    desconto: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    data_vencimento: Optional[date] = None
    metodo_pagamento: Optional[MetodoPagamento] = None
    status: Optional[InvoiceStatus] = None
    notas_admin: Optional[str] = None


class InvoiceUploadComprovante(BaseModel):
    """Modelo para upload de comprovante pelo cliente"""
    comprovante_url: str = Field(..., min_length=1)


class InvoiceConfirmarPagamento(BaseModel):
    """Modelo para confirmação de pagamento pelo admin"""
    data_pagamento: date
    notas_admin: Optional[str] = None


class Invoice(InvoiceBase):
    """Modelo completo de fatura (retornado pela API)"""
    id: UUID
    numero_fatura: str
    valor_final: Decimal
    data_emissao: date
    data_pagamento: Optional[date] = None
    status: InvoiceStatus

    # URLs de documentos
    nota_fiscal_url: Optional[str] = None
    comprovante_url: Optional[str] = None
    comprovante_enviado_em: Optional[datetime] = None

    # Confirmação admin
    confirmado_por: Optional[UUID] = None
    confirmado_em: Optional[datetime] = None
    notas_admin: Optional[str] = None

    # Metadata
    created_at: datetime
    updated_at: datetime

    # Informações do projeto (join)
    project_nome: Optional[str] = None
    client_nome: Optional[str] = None

    @computed_field
    @property
    def esta_atrasado(self) -> bool:
        """Verifica se a fatura está atrasada"""
        if self.status in [InvoiceStatus.PAGO, InvoiceStatus.CANCELADO]:
            return False
        return self.data_vencimento < date.today()

    @computed_field
    @property
    def dias_ate_vencimento(self) -> int:
        """Dias até o vencimento (negativo se atrasado)"""
        delta = self.data_vencimento - date.today()
        return delta.days

    class Config:
        from_attributes = True


class InvoiceStats(BaseModel):
    """Estatísticas de faturas (para dashboard admin)"""
    total_faturado: Decimal
    total_pendente: Decimal
    total_atrasado: Decimal
    total_pago: Decimal

    quantidade_pendente: int
    quantidade_atrasado: int
    quantidade_pago: int
    quantidade_aguardando_conf: int

    proximos_vencimentos: list[Invoice] = Field(default_factory=list)
