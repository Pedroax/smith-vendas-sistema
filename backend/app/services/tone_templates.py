"""
Templates fixos em 2 versões: formal e informal.
Usado pelo qualify_lead para espelhar o tom do lead.
"""

TEMPLATES = {
    "empresa_e_cargo": {
        "informal": "Opa, prazer {nome}! 👋\n\nMe conta, qual é sua empresa e o que você faz lá?",
        "formal": "Olá, {nome}! Prazer em falar com você.\n\nPoderia me informar o nome de sua empresa e qual é o seu cargo?"
    },
    "contexto_operacional_completo": {
        "informal": "Bacana! Pra eu entender melhor o cenário: quantas pessoas vocês têm na equipe de vendas e qual o faturamento mensal aproximado?",
        "formal": "Entendido! Para melhor compreender o contexto, poderia informar o tamanho da equipe comercial e a faixa de faturamento mensal?"
    },
    "contexto_operacional_so_funcionarios": {
        "informal": "Entendi! E quantas pessoas você tem na equipe de vendas/atendimento?",
        "formal": "Entendido! Qual seria o tamanho da equipe de vendas e atendimento?"
    },
    "faturamento": {
        "informal": "Show! E qual o faturamento mensal de vocês? Isso vai me ajudar a calcular o impacto real que consigo gerar.",
        "formal": "Qual seria a faixa de faturamento mensal da empresa? Isso me permitirá calcular o impacto potencial."
    },
    "decisor": {
        "informal": "Beleza! Você é quem decide sobre tecnologia e processos na {empresa}?",
        "formal": "Você é o responsável pelas decisões de tecnologia e processos na {empresa}?"
    },
    "dor_principal": {
        "informal": "Perfeito! Me conta: qual o principal problema que vocês enfrentam hoje? É perda de leads? Atendimento desorganizado? Processos manuais?",
        "formal": "Qual seria o principal desafio que a empresa enfrenta atualmente? Perda de leads, atendimento desorganizado ou processos manuais?"
    },
    "urgencia": {
        "informal": "Entendi! E quanto ao timing: isso é urgente pra vocês ou dá pra deixar pros próximos meses?",
        "formal": "Qual seria o prazo estimado para implementação de uma solução? É uma necessidade imediata ou pode ser planejada para os próximos meses?"
    }
}
