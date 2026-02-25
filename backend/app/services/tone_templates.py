"""
Templates fixos em 2 versões: formal e informal.
Usado pelo qualify_lead para espelhar o tom do lead.
"""

TEMPLATES = {
    "empresa_e_cargo": {
        "informal": "Opa, prazer {nome}! 👋\n\nMe fala — em qual empresa você está e o que você faz por lá?",
        "formal": "Olá, {nome}! Prazer em falar com você.\n\nPoderia me contar em qual empresa atua e qual é seu cargo?"
    },
    "contexto_operacional_completo": {
        "informal": "Show, {cargo} da {empresa}! 💪\n\nPra eu entender o tamanho da oportunidade aqui: qual é o faturamento mensal de vocês e quantas pessoas tem no time de atendimento/vendas?",
        "formal": "Entendido, {cargo} da {empresa}. Para dimensionar o potencial de impacto corretamente: qual seria a faixa de faturamento mensal e o tamanho da equipe de atendimento e vendas?"
    },
    "contexto_operacional_so_funcionarios": {
        "informal": "Entendido! E quantas pessoas você tem no time de vendas/atendimento?",
        "formal": "Entendido. Qual seria o tamanho da equipe de vendas e atendimento?"
    },
    "faturamento": {
        "informal": "Show! E o faturamento mensal da {empresa}, em que faixa tá hoje? Isso me ajuda a calcular o impacto real.",
        "formal": "Qual seria a faixa de faturamento mensal da {empresa}? Isso me permite dimensionar o potencial de retorno com precisão."
    },
    "decisor": {
        "informal": "Beleza! Você é quem decide sobre tecnologia e processos na {empresa}?",
        "formal": "Você é o responsável pelas decisões de tecnologia e processos na {empresa}?"
    },
    "dor_principal": {
        "informal": "Entendido! Com {funcionarios} pessoas na {empresa}, consigo imaginar o volume de trabalho.\n\nMe conta: qual é o maior problema que você tem hoje? Perda de leads? Atendimento lento? Processos que tomam tempo do time?",
        "formal": "Entendido. Com uma equipe desse tamanho na {empresa}, qual seria o principal desafio operacional? Perda de leads, atendimento desorganizado ou processos que sobrecarregam a equipe?"
    },
    "urgencia": {
        "informal": "Faz sentido, {nome}. Esse tipo de problema sangra lead bom todo dia que passa...\n\nIsso é urgente pra você resolver logo ou dá pra esperar alguns meses?",
        "formal": "Compreendo o cenário. Qual seria o prazo ideal para implementação de uma solução? É uma necessidade imediata ou pode ser planejada para os próximos meses?"
    }
}
