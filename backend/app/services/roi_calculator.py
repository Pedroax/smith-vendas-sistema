"""
Calculadora de ROI para o SDR Smith.
Zero LLM - cálculo puro em Python.
Usado para personalizar a oferta de agendamento com números reais do lead.
"""

from typing import Optional


def calcular_roi(qualification_data) -> dict:
    """
    Calcula ROI estimado baseado nos dados coletados do lead.

    Caminhos:
    1. Com funcionários: economia baseada em horas economizadas
    2. Com faturamento: economia baseada em percentual do faturamento
    3. Fallback: sem número (mensagem genérica)

    Retorna dict com valores calculados e mensagem pronta.
    """
    if not qualification_data:
        return {
            "tem_numero": False,
            "funcionarios": None,
            "economia_mensal": None,
            "economia_anual": None,
            "mensagem_roi": None
        }

    funcionarios = qualification_data.funcionarios_atendimento
    faturamento_anual = qualification_data.faturamento_anual

    # Caminho 1: tem funcionários → calcular por horas economizadas
    if funcionarios and funcionarios > 0:
        # 4h por semana * 4.3 semanas/mês = 17.2h/mês por pessoa
        # Salário médio R$3.000 / 176h = ~R$17/h
        # 70% das tarefas manuais são automatizáveis
        horas_economizadas_mes = funcionarios * 4 * 4.3
        custo_hora = 3000 / 176
        economia_mensal = round(horas_economizadas_mes * custo_hora * 0.7, -2)  # arredonda p/ centena
        economia_anual = economia_mensal * 12

        return {
            "tem_numero": True,
            "funcionarios": funcionarios,
            "economia_mensal": economia_mensal,
            "economia_anual": economia_anual,
            "mensagem_roi": None  # será montada no formatar_mensagem_roi
        }

    # Caminho 2: tem faturamento → calcular por percentual recuperado
    if faturamento_anual and faturamento_anual > 0:
        faturamento_mensal = faturamento_anual / 12
        # 8% de recuperação média (leads perdidos por lentidão de atendimento)
        economia_mensal = round(faturamento_mensal * 0.08, -2)  # arredonda p/ centena
        economia_anual = economia_mensal * 12

        return {
            "tem_numero": True,
            "funcionarios": None,
            "economia_mensal": economia_mensal,
            "economia_anual": economia_anual,
            "mensagem_roi": None
        }

    # Fallback: sem dados suficientes
    return {
        "tem_numero": False,
        "funcionarios": None,
        "economia_mensal": None,
        "economia_anual": None,
        "mensagem_roi": None
    }


def formatar_mensagem_roi(resultado: dict, lead_nome: str, empresa_nome: str = None) -> str:
    """
    Gera mensagem de oferta de agendamento com ROI personalizado.
    """
    nome = lead_nome.split()[0] if lead_nome else lead_nome
    empresa = empresa_nome or "vocês"

    if not resultado.get("tem_numero"):
        # Fallback genérico sem número
        return (
            f"Perfeito, {nome}! 🎯\n\n"
            f"Pelo que você me contou, tenho certeza que consigo gerar resultado real pra {empresa}.\n\n"
            f"Vale uma call de 30min pra eu te mostrar como funciona na prática?"
        )

    economia_mensal = resultado.get("economia_mensal", 0)
    funcionarios = resultado.get("funcionarios")

    # Formatar valor monetário
    if economia_mensal >= 1000:
        valor_fmt = f"R${economia_mensal:,.0f}".replace(",", ".")
    else:
        valor_fmt = f"R${economia_mensal:.0f}"

    if funcionarios:
        return (
            f"Rodei os números aqui, {nome} 🧮\n\n"
            f"Com {funcionarios} pessoas no time automatizando tarefas repetitivas, "
            f"a estimativa é de ~{valor_fmt}/mês em horas recuperadas — "
            f"só isso já paga o investimento em 1-2 meses.\n\n"
            f"Vale uma call de 30min pra eu mostrar como implementar isso na {empresa}?"
        )
    else:
        return (
            f"Rodei os números aqui, {nome} 🧮\n\n"
            f"Com o faturamento de vocês, só recuperando os leads que se perdem "
            f"por atendimento lento, estamos falando de ~{valor_fmt}/mês.\n\n"
            f"Vale uma call de 30min pra eu mostrar como isso funciona na {empresa}?"
        )
