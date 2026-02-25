"""
Serviço de pesquisa de empresas para o SDR Smith.
Usa website_research_service para scraping + Gemini 2.0 Flash para gerar insights.
Roda em background sem bloquear o fluxo principal.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
from loguru import logger

from app.config import settings
from app.services.website_research_service import WebsiteResearchService


class EmpresaResearchService:
    """
    Pesquisa informações sobre a empresa do lead.
    Usa scraping do site + Gemini 2.0 Flash para gerar 1 insight de vendas.
    Cache em memória com TTL de 24h.
    """

    def __init__(self):
        self.website_research = WebsiteResearchService()
        # Cache: {lead_id: {"insight": str, "timestamp": datetime, "empresa": str}}
        self._cache: Dict[str, dict] = {}
        self._gemini_model = None

    def _init_gemini(self):
        """Inicializa Gemini lazily - apenas se GEMINI_API_KEY estiver configurada"""
        if self._gemini_model:
            return self._gemini_model

        if not settings.gemini_api_key:
            logger.debug("GEMINI_API_KEY não configurada - pesquisa de empresa desabilitada")
            return None

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self._gemini_model = genai.GenerativeModel(settings.gemini_model)
            logger.info(f"Gemini {settings.gemini_model} inicializado para pesquisa de empresas")
            return self._gemini_model
        except ImportError:
            logger.warning("google-generativeai não instalado. Execute: pip install google-generativeai")
            return None
        except Exception as e:
            logger.error(f"Erro ao inicializar Gemini: {e}")
            return None

    def detect_trigger(self, lead, message: str):
        """
        Detecta se deve rodar pesquisa de empresa.

        Triggers:
        - Mensagem contém URL
        - Lead tem empresa preenchida mas ainda não foi pesquisado

        Retorna: (deve_pesquisar, url_ou_none)
        """
        # Se já tem insight em cache recente (< 24h), não pesquisar de novo
        cached = self._cache.get(str(lead.id))
        if cached:
            age = datetime.now() - cached["timestamp"]
            if age < timedelta(hours=24):
                return False, None

        # Verificar se mensagem tem URL
        url = self.website_research.extract_url(message)
        if url:
            logger.info(f"🔗 URL detectada na mensagem: {url}")
            return True, url

        # Se lead tem empresa mas nunca foi pesquisado - não faz nada ainda
        # (só pesquisamos quando temos URL ou site explícito)
        return False, None

    def _generate_insight_with_gemini(
        self,
        company_name: str,
        website_content: str
    ) -> Optional[str]:
        """
        Usa Gemini 2.0 Flash para gerar 1 insight de vendas baseado no site da empresa.
        """
        model = self._init_gemini()
        if not model:
            return None

        try:
            prompt = f"""Você é um assistente de vendas da AutomateX, empresa que vende automação de atendimento e vendas via WhatsApp/IA.

EMPRESA: {company_name}

CONTEÚDO DO SITE:
{website_content[:2000]}

Analise o site e gere APENAS 1 frase de insight para usar naturalmente em conversa de vendas pelo WhatsApp.

REGRAS:
- Máximo 2 linhas
- Tom conversacional, não formal
- Conectar o que a empresa faz com o problema que a AutomateX resolve (atendimento lento, perda de leads, processos manuais)
- Não inventar dados que não estão no site
- Começar com "Vi que" ou "Percebi que"

EXEMPLOS:
- "Vi que a {company_name} atende clientes B2B — empresas assim costumam perder leads por demora no primeiro contato."
- "Percebi que vocês têm várias linhas de produto — isso deve gerar muito volume de dúvidas repetidas no atendimento."
- "Vi que a {company_name} está crescendo bastante — times em expansão geralmente sofrem com atendimento desorganizado."

Responda APENAS com a frase, sem explicações."""

            response = model.generate_content(prompt)
            insight = response.text.strip()

            if insight and len(insight) > 10:
                logger.info(f"Gemini gerou insight: {insight[:80]}...")
                return insight

        except Exception as e:
            logger.error(f"Erro ao gerar insight com Gemini: {e}")

        return None

    async def research_empresa(
        self,
        lead,
        url: Optional[str] = None
    ) -> Optional[str]:
        """
        Pesquisa empresa e retorna 1 insight de vendas.

        Fluxo:
        1. Scraping do site com website_research_service
        2. Gemini analisa e gera insight
        3. Fallback: usa insight do GPT do website_research_service
        """
        if not url:
            return None

        try:
            empresa_nome = lead.empresa or self.website_research.extract_company_name(url)

            logger.info(f"Pesquisando empresa {empresa_nome} em {url}")

            # 1. Scraping do site
            content = await self.website_research.fetch_website_content(url)

            if not content:
                logger.warning(f"Não foi possível acessar {url}")
                return None

            # 2. Tentar com Gemini primeiro
            insight = None
            gemini_model = self._init_gemini()

            if gemini_model:
                # Gemini é síncrono, rodar em thread para não bloquear
                insight = await asyncio.to_thread(
                    self._generate_insight_with_gemini,
                    empresa_nome,
                    content
                )

            # 3. Fallback: usar análise GPT do website_research_service
            if not insight:
                logger.info("Fallback: usando análise GPT do website_research_service")
                analysis = await self.website_research.analyze_with_gpt(empresa_nome, content)
                if analysis and analysis.get("insights"):
                    insight = analysis["insights"][0]

            return insight

        except Exception as e:
            logger.error(f"Erro ao pesquisar empresa: {e}")
            return None

    def _generate_plano_personalizado(
        self,
        company_name: str,
        lead_nome: str,
        website_content: str
    ) -> Optional[str]:
        """
        Usa Gemini para gerar análise completa e personalizada baseada no site.
        Chamado quando o lead pergunta 'como você me ajudaria?' e manda o site.
        """
        model = self._init_gemini()
        if not model:
            return None

        try:
            prompt = f"""Você é Smith, consultor da AutomateX que vende automação de atendimento e vendas via IA.
Você acabou de analisar o site da empresa de {lead_nome}.

EMPRESA: {company_name}

CONTEÚDO DO SITE:
{website_content[:3000]}

Gere uma resposta para WhatsApp que mostre que você REALMENTE analisou o site e entende o negócio deles.

A mensagem deve:
1. Mencionar 2-3 detalhes ESPECÍFICOS que você encontrou no site (produtos, serviços, segmento, público)
2. Identificar onde há oportunidade clara de automação/IA no atendimento deles (baseado no que você viu)
3. Ser específico sobre o que a AutomateX faria na prática para essa empresa
4. Terminar com convite para call de 30min

REGRAS:
- Máximo 6-7 linhas
- WhatsApp casual mas profissional
- NUNCA use as palavras "chatbot", "robô" ou "bot" — use "IA de atendimento" ou "agente inteligente"
- Mencione detalhes REAIS do site — não invente
- Seja específico, não genérico
- Tom de consultor que entende o negócio deles, não de vendedor

Responda APENAS com a mensagem, sem explicações."""

            response = model.generate_content(prompt)
            plano = response.text.strip()

            if plano and len(plano) > 50:
                logger.success(f"Plano personalizado gerado para {company_name}: {plano[:80]}...")
                return plano

        except Exception as e:
            logger.error(f"Erro ao gerar plano personalizado com Gemini: {e}")

        return None

    async def _generate_plano_com_openai(
        self,
        company_name: str,
        lead_nome: str,
        website_content: str
    ) -> Optional[str]:
        """
        Fallback usando OpenAI GPT-4o para gerar plano personalizado.
        Sempre disponível quando Gemini não estiver configurado.
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage
            from app.config import settings

            llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0.3,
                api_key=settings.openai_api_key,
                request_timeout=20
            )

            prompt = f"""Você é Smith, consultor da AutomateX que vende automação de atendimento e vendas via IA.
Você acabou de analisar o site da empresa de {lead_nome}.

EMPRESA: {company_name}

CONTEÚDO DO SITE:
{website_content[:3000]}

Gere uma mensagem para WhatsApp que mostre que você REALMENTE analisou o site e entende o negócio deles.

A mensagem deve:
1. Mencionar 2-3 detalhes ESPECÍFICOS encontrados no site (produtos, serviços, segmento, público-alvo)
2. Identificar onde há oportunidade de automação/IA no atendimento deles baseado no que você viu
3. Ser específico sobre o que a AutomateX faria na prática para essa empresa
4. Terminar com convite para call de 30min

REGRAS:
- Máximo 6-7 linhas
- WhatsApp casual mas profissional
- NUNCA use "chatbot", "robô" ou "bot" — use "IA de atendimento" ou "agente inteligente"
- Mencione detalhes REAIS do site — não invente nada
- Tom de consultor que entende o negócio, não de vendedor

Responda APENAS com a mensagem, sem explicações."""

            response = await llm.ainvoke([SystemMessage(content=prompt)])
            result = response.content.strip()

            if result and len(result) > 50:
                logger.success(f"Plano gerado com OpenAI para {company_name}: {result[:80]}...")
                return result

        except Exception as e:
            logger.error(f"Erro ao gerar plano com OpenAI: {e}")

        return None

    async def _generate_plano_sem_site(
        self,
        company_name: str,
        lead_nome: str,
        url: str
    ) -> Optional[str]:
        """
        Gera análise quando o site não pôde ser acessado.
        Usa apenas o nome da empresa e URL para inferir o segmento.
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage

            llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0.4,
                api_key=settings.openai_api_key,
                request_timeout=20
            )

            prompt = f"""Você é Smith, consultor da AutomateX que vende automação de atendimento e vendas via IA.

EMPRESA: {company_name}
URL: {url}

Você não conseguiu acessar o site, mas pelo nome da empresa e URL consegue inferir o segmento.

Gere uma mensagem de WhatsApp que:
1. Mostre que você pesquisou a empresa (mesmo sem acesso ao site)
2. Faça uma pergunta inteligente sobre o negócio deles baseada no que o nome/URL sugere
3. Conecte com uma oportunidade de automação no atendimento
4. Convide para call de 30min

REGRAS:
- Máximo 5-6 linhas
- WhatsApp casual mas profissional
- NUNCA use "chatbot", "robô" ou "bot" — use "IA de atendimento" ou "agente inteligente"
- NÃO invente dados específicos que você não sabe
- Seja honesto mas curioso: "Pesquisei sobre a {company_name}..."
- Tom de consultor interessado, não de vendedor

Responda APENAS com a mensagem."""

            response = await llm.ainvoke([SystemMessage(content=prompt)])
            result = response.content.strip()

            if result and len(result) > 30:
                logger.info(f"Plano gerado sem acesso ao site para {company_name}")
                return result

        except Exception as e:
            logger.error(f"Erro ao gerar plano sem site: {e}")

        return None

    async def research_empresa_com_plano(
        self,
        lead,
        url: str
    ) -> Optional[str]:
        """
        Pesquisa completa e síncrona do site da empresa.
        Retorna análise personalizada para usar como resposta imediata.
        Tenta Gemini primeiro, fallback para OpenAI (sempre disponível).
        """
        try:
            empresa_nome = lead.empresa or self.website_research.extract_company_name(url)
            lead_nome = lead.nome.split()[0] if lead.nome else (lead.nome or "você")

            logger.info(f"🔍 Analisando site completo: {url} para {empresa_nome}")

            content = await self.website_research.fetch_website_content(url)
            if not content:
                logger.warning(f"Não foi possível acessar {url} — usando análise baseada no domínio")
                plano = await self._generate_plano_sem_site(empresa_nome, lead_nome, url)
                if plano:
                    self._cache[str(lead.id)] = {
                        "insight": plano[:120],
                        "full_analysis": plano,
                        "timestamp": datetime.now(),
                        "empresa": empresa_nome
                    }
                return plano

            logger.info(f"✅ Site acessado ({len(content)} chars) — gerando análise personalizada")

            plano = None

            # 1. Tentar Gemini (se disponível)
            gemini_model = self._init_gemini()
            if gemini_model:
                plano = await asyncio.to_thread(
                    self._generate_plano_personalizado,
                    empresa_nome,
                    lead_nome,
                    content
                )

            # 2. Fallback para OpenAI (sempre disponível)
            if not plano:
                logger.info("Usando OpenAI para gerar plano personalizado")
                plano = await self._generate_plano_com_openai(empresa_nome, lead_nome, content)

            if plano:
                self._cache[str(lead.id)] = {
                    "insight": plano[:120],
                    "full_analysis": plano,
                    "timestamp": datetime.now(),
                    "empresa": empresa_nome
                }
                return plano

            logger.warning("Não foi possível gerar análise personalizada")
            return None

        except Exception as e:
            logger.error(f"Erro na análise completa da empresa: {e}")
            return None

    def get_cached_insight(self, lead_id) -> Optional[str]:
        """Retorna insight do cache se existir e for recente (< 24h)"""
        cached = self._cache.get(str(lead_id))
        if not cached:
            return None

        age = datetime.now() - cached["timestamp"]
        if age > timedelta(hours=24):
            del self._cache[str(lead_id)]
            return None

        return cached.get("insight")

    async def run_background_research(self, lead, message: str):
        """
        Entry point para rodar em background.
        Detecta trigger, pesquisa empresa, salva no cache.
        Não bloqueia o fluxo principal.
        """
        try:
            deve_pesquisar, url = self.detect_trigger(lead, message)

            if not deve_pesquisar:
                return

            insight = await self.research_empresa(lead, url=url)

            if insight:
                self._cache[str(lead.id)] = {
                    "insight": insight,
                    "timestamp": datetime.now(),
                    "empresa": lead.empresa or ""
                }
                logger.success(f"Insight salvo para lead {lead.id}: {insight[:60]}...")

        except Exception as e:
            logger.error(f"Erro na pesquisa background de empresa: {e}")


# Instância global (singleton)
empresa_research_service = EmpresaResearchService()
