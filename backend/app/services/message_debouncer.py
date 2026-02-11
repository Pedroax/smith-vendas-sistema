"""
Message Debouncer - Buffer de Mensagens WhatsApp
Agrupa mensagens enviadas rapidamente pelo mesmo usuário
"""
import asyncio
from typing import Dict, Callable, List
from datetime import datetime
from loguru import logger


class MessageDebouncer:
    """
    Buffer de mensagens com processamento em background

    Aguarda X segundos após última mensagem antes de processar.
    Evita processar cada mensagem individual quando usuário
    está digitando várias mensagens em sequência.

    Exemplo:
        Usuário envia:
        - "Oi" (00:00:00.0)
        - "Quero fazer um site" (00:00:01.5)
        - "Para minha empresa" (00:00:02.3)

        Sistema processa uma única vez (00:00:04.8):
        "Oi\nQuero fazer um site\nPara minha empresa"
    """

    def __init__(self, wait_seconds: float = 2.5):
        """
        Inicializa debouncer

        Args:
            wait_seconds: Tempo de espera após última mensagem (padrão: 2.5s)
        """
        self.wait_seconds = wait_seconds
        self.timers: Dict[str, asyncio.Task] = {}
        self.message_buffer: Dict[str, List[dict]] = {}
        self.locks: Dict[str, asyncio.Lock] = {}

        logger.info(f"🔄 MessageDebouncer inicializado (wait={wait_seconds}s)")

    async def add_message(
        self,
        phone: str,
        message: str,
        callback: Callable,
        **callback_kwargs
    ):
        """
        Adiciona mensagem ao buffer e inicia/reseta timer

        Esta função não aguarda processamento - retorna imediatamente.
        O processamento acontece em background após wait_seconds.

        Args:
            phone: Telefone do usuário (identificador único)
            message: Conteúdo da mensagem
            callback: Função async a ser chamada com mensagens combinadas
            **callback_kwargs: Argumentos adicionais para o callback
        """
        # Criar lock se não existir (thread-safety)
        if phone not in self.locks:
            self.locks[phone] = asyncio.Lock()

        async with self.locks[phone]:
            # Adicionar mensagem ao buffer
            if phone not in self.message_buffer:
                self.message_buffer[phone] = []

            self.message_buffer[phone].append({
                "content": message,
                "timestamp": datetime.now()
            })

            msg_count = len(self.message_buffer[phone])
            logger.info(
                f"📝 Buffer [{phone[:12]}...]: "
                f"{msg_count} mensagem{'s' if msg_count > 1 else ''} "
                f"(última: '{message[:30]}...')"
            )

            # Cancelar timer anterior se existir
            if phone in self.timers and not self.timers[phone].done():
                self.timers[phone].cancel()
                logger.debug(f"⏱️  Timer resetado para {phone[:12]}...")

            # Criar novo timer (background task)
            self.timers[phone] = asyncio.create_task(
                self._process_after_delay(phone, callback, callback_kwargs)
            )

    async def _process_after_delay(
        self,
        phone: str,
        callback: Callable,
        callback_kwargs: dict
    ):
        """
        Aguarda X segundos e processa mensagens acumuladas

        Se nova mensagem chegar durante a espera, este timer
        será cancelado e um novo será iniciado.

        Args:
            phone: Telefone do usuário
            callback: Função a ser chamada
            callback_kwargs: Argumentos para callback
        """
        try:
            # Aguardar período de silêncio
            await asyncio.sleep(self.wait_seconds)

            async with self.locks[phone]:
                # Extrair mensagens do buffer
                messages = self.message_buffer.pop(phone, [])

                if not messages:
                    logger.warning(f"⚠️  Buffer vazio para {phone[:12]}... (já processado?)")
                    return

                # Combinar mensagens com quebra de linha
                combined_message = "\n".join([msg["content"] for msg in messages])

                first_timestamp = messages[0]["timestamp"]
                last_timestamp = messages[-1]["timestamp"]
                duration = (last_timestamp - first_timestamp).total_seconds()

                logger.info(
                    f"🔄 Processando buffer [{phone[:12]}...]: "
                    f"{len(messages)} mensagens em {duration:.1f}s"
                )
                logger.debug(f"📨 Mensagem combinada: '{combined_message[:100]}...'")

                # Chamar callback com mensagem combinada (background)
                await callback(phone, combined_message, **callback_kwargs)

                logger.success(f"✅ Buffer processado para {phone[:12]}...")

        except asyncio.CancelledError:
            logger.debug(f"⏹️  Timer cancelado para {phone[:12]}... (nova mensagem recebida)")
            # Não fazer nada - nova mensagem criará novo timer

        except Exception as e:
            logger.error(
                f"❌ Erro ao processar buffer para {phone[:12]}...: {e}",
                exc_info=True
            )
            # Limpar buffer em caso de erro para não travar
            self.message_buffer.pop(phone, None)
            self.timers.pop(phone, None)

    def get_stats(self) -> dict:
        """
        Retorna estatísticas do debouncer

        Returns:
            Dict com stats: active_timers, pending_messages, phones_waiting
        """
        active_timers = sum(
            1 for task in self.timers.values()
            if not task.done()
        )

        pending_messages = sum(
            len(msgs) for msgs in self.message_buffer.values()
        )

        return {
            "active_timers": active_timers,
            "pending_messages": pending_messages,
            "phones_waiting": list(self.message_buffer.keys())
        }


# Instância global do debouncer
_message_debouncer: MessageDebouncer = None


def get_message_debouncer(wait_seconds: float = 2.5) -> MessageDebouncer:
    """
    Retorna instância global do MessageDebouncer

    Args:
        wait_seconds: Tempo de espera (usado apenas na primeira chamada)

    Returns:
        Instância singleton do debouncer
    """
    global _message_debouncer
    if _message_debouncer is None:
        _message_debouncer = MessageDebouncer(wait_seconds=wait_seconds)
    return _message_debouncer
