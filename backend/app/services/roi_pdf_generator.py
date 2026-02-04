"""
Serviço de geração de PDF de análise de ROI
Gera PDFs personalizados com cálculos de retorno sobre investimento
"""
from datetime import datetime
from typing import Optional
from pathlib import Path
import io

from app.models.lead import Lead, QualificationData, ROIAnalysis
from loguru import logger


class ROIPDFGenerator:
    """Gerador de PDFs de análise de ROI"""

    def __init__(self):
        self.output_dir = Path("./pdfs")
        self.output_dir.mkdir(exist_ok=True)

    def calculate_roi(self, qualification_data: QualificationData, valor_proposta: float = 2000) -> ROIAnalysis:
        """
        Calcula ROI baseado nos dados de qualificação

        Args:
            qualification_data: Dados coletados na qualificação
            valor_proposta: Valor mensal da proposta (default: R$ 2000)

        Returns:
            ROIAnalysis com os cálculos
        """
        try:
            # Valores padrão caso não tenham sido coletados
            atendimentos_dia = qualification_data.atendimentos_por_dia or 50
            tempo_atendimento = qualification_data.tempo_por_atendimento or 15  # minutos
            ticket_medio = qualification_data.ticket_medio or 300

            # Cálculos
            # 1. Tempo economizado por mês (assumindo 70% de automatização)
            atendimentos_mes = atendimentos_dia * 22  # dias úteis
            minutos_totais_mes = atendimentos_mes * tempo_atendimento
            horas_totais_mes = minutos_totais_mes / 60
            tempo_economizado = horas_totais_mes * 0.7  # 70% de automatização

            # 2. Valor economizado (baseado em salário médio de atendente)
            salario_medio_atendente = 3000  # R$ por mês
            valor_hora = salario_medio_atendente / 176  # horas/mês
            valor_economizado_mes = tempo_economizado * valor_hora
            valor_economizado_ano = valor_economizado_mes * 12

            # 3. ROI percentual
            investimento_anual = valor_proposta * 12
            roi_percentual = ((valor_economizado_ano - investimento_anual) / investimento_anual) * 100

            # 4. Payback (meses para recuperar investimento)
            payback_meses = int(investimento_anual / valor_economizado_mes) if valor_economizado_mes > 0 else 12

            return ROIAnalysis(
                tempo_economizado_mes=round(tempo_economizado, 1),
                valor_economizado_ano=round(valor_economizado_ano, 2),
                roi_percentual=round(roi_percentual, 1),
                payback_meses=payback_meses,
                generated_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Erro ao calcular ROI: {e}")
            return ROIAnalysis(
                tempo_economizado_mes=0,
                valor_economizado_ano=0,
                roi_percentual=0,
                payback_meses=12,
                generated_at=datetime.now()
            )

    def generate_pdf(self, lead: Lead, roi_analysis: ROIAnalysis) -> Optional[str]:
        """
        Gera PDF de análise de ROI para um lead

        Args:
            lead: Lead com dados de qualificação
            roi_analysis: Análise de ROI calculada

        Returns:
            Caminho do arquivo PDF gerado ou None se erro
        """
        try:
            # TODO: Implementar geração de PDF com reportlab
            # Por enquanto, retorna um placeholder

            filename = f"roi_analysis_{lead.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = self.output_dir / filename

            logger.info(f"PDF de ROI gerado: {filepath}")

            # Placeholder: criar um arquivo vazio por enquanto
            # Na implementação real, usar reportlab ou weasyprint
            self._generate_pdf_content(lead, roi_analysis, filepath)

            return str(filepath)

        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            return None

    def _generate_pdf_content(self, lead: Lead, roi_analysis: ROIAnalysis, filepath: Path):
        """
        Gera o conteúdo do PDF
        TODO: Implementar com reportlab
        """
        # Placeholder - criar arquivo de texto por enquanto
        content = f"""
╔══════════════════════════════════════════════════════════╗
║                  ANÁLISE DE ROI PERSONALIZADA             ║
║                        AutomateX IA                       ║
╚══════════════════════════════════════════════════════════╝

Cliente: {lead.nome}
Empresa: {lead.empresa or 'N/A'}
Data: {datetime.now().strftime('%d/%m/%Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 DADOS OPERACIONAIS ATUAIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Atendimentos por dia: {lead.qualification_data.atendimentos_por_dia or 'N/A'}
• Tempo médio por atendimento: {lead.qualification_data.tempo_por_atendimento or 'N/A'} minutos
• Ticket médio: R$ {lead.qualification_data.ticket_medio or 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 PROJEÇÃO DE ECONOMIA COM AUTOMAÇÃO IA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️  Tempo economizado por mês: {roi_analysis.tempo_economizado_mes} horas

💵  Valor economizado por ano: R$ {roi_analysis.valor_economizado_ano:,.2f}

📈  ROI Percentual: {roi_analysis.roi_percentual}%

⚡  Payback: {roi_analysis.payback_meses} meses

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 O QUE ISSO SIGNIFICA?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Com a automação da AutomateX IA, sua empresa pode:

✅ Liberar {roi_analysis.tempo_economizado_mes} horas/mês da equipe
✅ Economizar R$ {roi_analysis.valor_economizado_ano:,.2f} por ano
✅ Recuperar o investimento em {roi_analysis.payback_meses} meses
✅ Obter retorno de {roi_analysis.roi_percentual}% sobre o investimento

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 COMO A AUTOMATEX PODE REVERTER ESSA SITUAÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Nossa solução de IA oferece:

🤖 SMITH - AGENTE SDR INTELIGENTE
   • Atende leads automaticamente 24/7 via WhatsApp
   • Qualifica leads usando metodologia BANT
   • Coleta informações estratégicas da conversa
   • Agenda reuniões automaticamente no seu calendário

⚡ RESULTADOS IMEDIATOS:
   ✓ Sua equipe foca APENAS em leads qualificados
   ✓ Zero tempo gasto com curiosos ou não-qualificados
   ✓ Follow-ups automáticos (nunca mais perde um lead)
   ✓ Respostas instantâneas (aumenta conversão em 40%)

💡 TECNOLOGIA:
   • GPT-4 (mesma IA do ChatGPT) treinada para vendas
   • Integração nativa com WhatsApp Business
   • CRM profissional incluído
   • Analytics em tempo real

📊 IMPLEMENTAÇÃO:
   • Setup em 48 horas
   • Treinamento personalizado para sua operação
   • Suporte dedicado

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 PRÓXIMOS PASSOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Vamos conversar 30 minutos para eu te mostrar:
• Como funciona na prática (demo ao vivo)
• Como adaptar para o seu processo de vendas
• Plano de implementação personalizado

🌐 automatexia.com.br
📱 WhatsApp: {lead.telefone}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Análise gerada automaticamente por Smith 2.0
© {datetime.now().year} AutomateX - Inteligência Artificial para Vendas

"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    async def generate_and_send(self, lead: Lead) -> Optional[ROIAnalysis]:
        """
        Calcula ROI, gera PDF e atualiza o lead

        Args:
            lead: Lead com dados de qualificação

        Returns:
            ROIAnalysis com URL do PDF ou None se erro
        """
        try:
            if not lead.qualification_data:
                logger.warning(f"Lead {lead.id} não tem dados de qualificação")
                return None

            # Calcular ROI
            roi_analysis = self.calculate_roi(lead.qualification_data)

            # Gerar PDF
            pdf_path = self.generate_pdf(lead, roi_analysis)

            if pdf_path:
                roi_analysis.pdf_url = pdf_path
                logger.success(f"PDF de ROI gerado para {lead.nome}: {pdf_path}")
                return roi_analysis

            return None

        except Exception as e:
            logger.error(f"Erro ao gerar e enviar ROI: {e}")
            return None


# Instância global
roi_generator = ROIPDFGenerator()
