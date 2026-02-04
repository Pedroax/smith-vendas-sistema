"""
Serviço para pesquisar e analisar websites de leads
Usa WebFetch e Exa AI para coletar informações e gerar insights
"""
from typing import Dict, Optional, List
from loguru import logger
import re
from urllib.parse import urlparse
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from app.config import settings


class WebsiteResearchService:
    """Pesquisa e analisa websites de leads para personalizar atendimento"""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    def extract_url(self, message: str) -> Optional[str]:
        """
        Extrai URL de uma mensagem

        Args:
            message: Texto da mensagem

        Returns:
            URL encontrada ou None
        """
        # Regex para URLs
        url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+(?:/[^\s]*)?)'
        match = re.search(url_pattern, message.lower())

        if match:
            url = match.group(0)
            # Adicionar https:// se não tiver protocolo
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            return url

        return None

    def normalize_url(self, url: str) -> str:
        """
        Normaliza URL para formato padrão

        Args:
            url: URL bruta

        Returns:
            URL normalizada
        """
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        return url

    def extract_company_name(self, url: str) -> str:
        """
        Extrai nome da empresa da URL

        Args:
            url: URL do site

        Returns:
            Nome da empresa
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            # Remove www. e extensão
            domain = domain.replace('www.', '')
            domain = domain.split('.')[0]
            return domain.capitalize()
        except Exception as e:
            logger.error(f"Erro ao extrair nome da empresa: {e}")
            return "Empresa"

    async def fetch_website_content(self, url: str) -> Optional[str]:
        """
        Faz fetch do conteúdo do website

        Args:
            url: URL do site

        Returns:
            Texto extraído do site ou None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.warning(f"Site retornou status {response.status}")
                        return None

                    html = await response.text()

                    # Usar BeautifulSoup para extrair texto
                    soup = BeautifulSoup(html, 'html.parser')

                    # Remover scripts e styles
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Pegar texto
                    text = soup.get_text()

                    # Limpar espaços em branco
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)

                    # Limitar tamanho (primeiros 3000 caracteres para análise)
                    text = text[:3000]

                    return text

        except asyncio.TimeoutError:
            logger.warning(f"Timeout ao acessar {url}")
            return None
        except Exception as e:
            logger.error(f"Erro ao fazer fetch do site: {e}")
            return None

    async def analyze_with_gpt(self, company_name: str, website_content: str) -> Dict[str, any]:
        """
        Analisa conteúdo do site com GPT e gera insights

        Args:
            company_name: Nome da empresa
            website_content: Conteúdo do site

        Returns:
            {
                "summary": str,
                "insights": List[str]
            }
        """
        try:
            prompt = f"""Você é um assistente de vendas analisando o site de um lead.

EMPRESA: {company_name}

CONTEÚDO DO SITE:
{website_content}

Analise o site e gere:
1. Um resumo curto (1 frase) do que a empresa faz
2. Um insight interessante para usar na conversa de vendas (conectar com problema/dor que a empresa deve ter)

IMPORTANTE:
- Seja natural e conversacional
- Foque em entender o negócio deles
- Identifique possíveis dores/desafios que eles têm
- Seja breve e direto

Responda APENAS em formato JSON:
{{
    "summary": "Uma frase sobre o que a empresa faz",
    "insight": "Um insight para usar na conversa (ex: 'Vi que trabalham com X. Muitos clientes nossos nesse segmento tinham desafio de Y')"
}}"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            return {
                "summary": result.get("summary", ""),
                "insights": [result.get("insight", "")]
            }

        except Exception as e:
            logger.error(f"Erro ao analisar com GPT: {e}")
            return {
                "summary": "",
                "insights": []
            }

    async def research_website(self, url: str) -> Dict[str, any]:
        """
        Pesquisa e analisa um website

        Args:
            url: URL do site para pesquisar

        Returns:
            Dicionário com informações pesquisadas:
            {
                "success": bool,
                "url": str,
                "company_name": str,
                "summary": str,
                "insights": List[str],
                "error": Optional[str]
            }
        """
        try:
            url = self.normalize_url(url)
            company_name = self.extract_company_name(url)

            logger.info(f"🔍 Pesquisando website: {url}")

            # 1. Fazer fetch do conteúdo
            content = await self.fetch_website_content(url)

            if not content:
                logger.warning("Não conseguiu extrair conteúdo do site")
                return {
                    "success": False,
                    "url": url,
                    "company_name": company_name,
                    "summary": "",
                    "insights": [],
                    "error": "Não foi possível acessar o site"
                }

            # 2. Analisar com GPT
            analysis = await self.analyze_with_gpt(company_name, content)

            result = {
                "success": True,
                "url": url,
                "company_name": company_name,
                "summary": analysis["summary"],
                "insights": analysis["insights"],
                "error": None
            }

            logger.info(f"✅ Website pesquisado: {company_name}")
            return result

        except Exception as e:
            logger.error(f"❌ Erro ao pesquisar website: {e}")
            return {
                "success": False,
                "url": url if 'url' in locals() else "",
                "company_name": company_name if 'company_name' in locals() else "Empresa",
                "summary": "",
                "insights": [],
                "error": str(e)
            }

    def format_research_message(self, research: Dict[str, any]) -> str:
        """
        Formata resultado da pesquisa em mensagem natural

        Args:
            research: Resultado da pesquisa

        Returns:
            Mensagem formatada
        """
        if not research["success"]:
            return f"Dei uma olhada no site mas não consegui acessar agora. Sem problemas! Me conta, o que a {research['company_name']} faz?"

        company = research["company_name"]
        summary = research.get("summary", "")
        insights = research.get("insights", [])

        # Construir mensagem
        parts = [f"Visitei o site da {company}! 👀"]

        if summary:
            parts.append(summary)

        if insights:
            parts.append(insights[0])  # Usar primeiro insight

        return "\n\n".join(parts)


# Instância global
website_research_service = WebsiteResearchService()
