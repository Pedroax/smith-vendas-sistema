# 📦 Sistema de Buffer de Mensagens (Message Debouncer)

## 📋 Visão Geral

Sistema inteligente que **agrupa mensagens** enviadas em sequência rápida pelo mesmo usuário, processando apenas quando o usuário **para de enviar** por X segundos. Isso evita múltiplas respostas da IA e melhora a experiência do usuário.

---

## 🎯 Problema que Resolve

### Sem Buffer:
```
Lead: "Oi"                    → Paula: "Olá! Como posso ajudar?"
Lead: "quero botox"           → Paula: "Certo, sobre botox..."
Lead: "quanto custa"          → Paula: "Sobre o preço..."
Lead: "e pode parcelar?"      → Paula: "Sim, pode parcelar..."
```
**Resultado**: 4 mensagens separadas, confuso e poluído

### Com Buffer:
```
Lead: "Oi"
Lead: "quero botox"
Lead: "quanto custa"
Lead: "e pode parcelar?"
(aguarda 5 segundos de silêncio)
Paula recebe: "Oi\nquero botox\nquanto custa\ne pode parcelar?"
Paula: "Olá! Sobre o botox e preços, temos várias opções..."
```
**Resultado**: 1 resposta completa e contextualizada

---

## 🏗️ Arquitetura

### 1. Classe Principal: `MessageDebouncer`

**Localização**: `utils/debouncer.py`

```python
class MessageDebouncer:
    """
    Sistema de debouncing inteligente para mensagens do WhatsApp.

    Agrupa mensagens enviadas em sequência rápida pelo mesmo usuário,
    processando apenas quando o usuário para de enviar por X segundos.
    """

    def __init__(self, wait_seconds: float = 5.0):
        """
        Args:
            wait_seconds: Segundos de espera após última mensagem antes de processar
        """
        self.wait_seconds = wait_seconds
        self.timers: Dict[str, asyncio.Task] = {}        # Timer para cada usuário
        self.message_buffer: Dict[str, list] = {}        # Buffer de mensagens por usuário
        self.locks: Dict[str, asyncio.Lock] = {}         # Lock para thread-safety
```

### 2. Estruturas de Dados

#### Buffer de Mensagens
```python
self.message_buffer = {
    "5521999999999": [
        {
            "message": "Oi",
            "timestamp": datetime(2025, 1, 1, 10, 0, 0)
        },
        {
            "message": "quero botox",
            "timestamp": datetime(2025, 1, 1, 10, 0, 2)
        },
        {
            "message": "quanto custa",
            "timestamp": datetime(2025, 1, 1, 10, 0, 4)
        }
    ]
}
```

#### Timers Ativos
```python
self.timers = {
    "5521999999999": <asyncio.Task object at 0x...>
}
```

#### Locks (Thread-Safety)
```python
self.locks = {
    "5521999999999": <asyncio.Lock object at 0x...>
}
```

---

## 🔄 Fluxo de Funcionamento

### Diagrama de Sequência

```
┌─────────┐                 ┌──────────────┐                ┌──────────┐
│  Lead   │                 │  Debouncer   │                │  Paula   │
└────┬────┘                 └──────┬───────┘                └────┬─────┘
     │                             │                             │
     │  1. "Oi"                    │                             │
     ├────────────────────────────>│                             │
     │                             │ Buffer: ["Oi"]              │
     │                             │ Timer: 5s                   │
     │                             │                             │
     │  2. "quero botox"           │                             │
     ├────────────────────────────>│                             │
     │                             │ Buffer: ["Oi", "quero..."]  │
     │                             │ Timer REINICIADO: 5s        │
     │                             │                             │
     │  3. "quanto custa"          │                             │
     ├────────────────────────────>│                             │
     │                             │ Buffer: [..., "quanto..."]  │
     │                             │ Timer REINICIADO: 5s        │
     │                             │                             │
     │  (para de enviar)           │                             │
     │                             │                             │
     │         ... 5 segundos ...  │                             │
     │                             │                             │
     │                             │  4. Combina mensagens       │
     │                             │  "Oi\nquero botox\nquanto   │
     │                             │   custa"                    │
     │                             │                             │
     │                             │  5. Chama callback          │
     │                             ├────────────────────────────>│
     │                             │                             │
     │                             │         6. Processa         │
     │                             │                             │
     │  7. Resposta única          │                             │
     │<────────────────────────────┴─────────────────────────────┤
     │                                                           │
```

---

## 💻 Implementação Passo a Passo

### Passo 1: Criar a Classe MessageDebouncer

**Arquivo**: `utils/debouncer.py`

```python
import asyncio
from typing import Dict, Callable, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MessageDebouncer:
    """
    Sistema de debouncing inteligente para mensagens do WhatsApp.
    """

    def __init__(self, wait_seconds: float = 5.0):
        """
        Args:
            wait_seconds: Segundos de espera após última mensagem antes de processar
        """
        self.wait_seconds = wait_seconds
        self.timers: Dict[str, asyncio.Task] = {}
        self.message_buffer: Dict[str, list] = {}
        self.locks: Dict[str, asyncio.Lock] = {}

    async def add_message(
        self,
        phone: str,
        message: str,
        callback: Callable[[str, str], Any]
    ) -> None:
        """
        Adiciona mensagem ao buffer e gerencia debouncing.

        Args:
            phone: Telefone do usuário
            message: Mensagem recebida
            callback: Função async a ser chamada quando processar (recebe phone, combined_message)
        """
        # 1. Cria lock se não existir (garante thread-safety)
        if phone not in self.locks:
            self.locks[phone] = asyncio.Lock()

        async with self.locks[phone]:
            # 2. Adiciona mensagem ao buffer
            if phone not in self.message_buffer:
                self.message_buffer[phone] = []

            self.message_buffer[phone].append({
                "message": message,
                "timestamp": datetime.now()
            })

            logger.info(
                f"📩 Mensagem adicionada ao buffer [{phone}]: '{message}' "
                f"(total: {len(self.message_buffer[phone])} msgs)"
            )

            # 3. Cancela timer anterior se existir
            if phone in self.timers and not self.timers[phone].done():
                self.timers[phone].cancel()
                logger.info(f"⏱️  Timer anterior cancelado para {phone}")

            # 4. Cria novo timer (reinicia contagem)
            self.timers[phone] = asyncio.create_task(
                self._process_after_delay(phone, callback)
            )

    async def _process_after_delay(
        self,
        phone: str,
        callback: Callable[[str, str], Any]
    ) -> None:
        """
        Aguarda delay e processa mensagens agrupadas.

        Args:
            phone: Telefone do usuário
            callback: Função a ser chamada
        """
        try:
            # 1. Aguarda o tempo de debounce
            logger.info(f"⏳ Aguardando {self.wait_seconds}s de silêncio para {phone}...")
            await asyncio.sleep(self.wait_seconds)

            # 2. Pega todas as mensagens do buffer
            async with self.locks[phone]:
                messages = self.message_buffer.get(phone, [])

                if not messages:
                    logger.warning(f"⚠️  Buffer vazio para {phone}")
                    return

                # 3. Combina todas as mensagens com quebra de linha
                combined_message = "\n".join([msg["message"] for msg in messages])

                logger.info(
                    f"✅ Processando {len(messages)} mensagem(ns) agrupada(s) de {phone}:\n"
                    f"   '{combined_message[:100]}...'"
                )

                # 4. Limpa buffer
                self.message_buffer[phone] = []

            # 5. Processa mensagem combinada
            await callback(phone, combined_message)

        except asyncio.CancelledError:
            logger.info(f"❌ Timer cancelado para {phone} (nova mensagem chegou)")
            # Não faz nada, novo timer foi criado
        except Exception as e:
            logger.error(f"💥 Erro ao processar mensagens de {phone}: {str(e)}", exc_info=True)

    def get_buffer_size(self, phone: str) -> int:
        """Retorna quantidade de mensagens no buffer de um usuário"""
        return len(self.message_buffer.get(phone, []))

    def clear_buffer(self, phone: str) -> None:
        """Limpa buffer de um usuário"""
        if phone in self.message_buffer:
            del self.message_buffer[phone]
        if phone in self.timers:
            if not self.timers[phone].done():
                self.timers[phone].cancel()
            del self.timers[phone]
        logger.info(f"🗑️  Buffer limpo para {phone}")
```

---

### Passo 2: Integrar no Sistema Principal

**Arquivo**: `main.py` (ou seu arquivo de webhook)

```python
from utils.debouncer import MessageDebouncer

# ============================================================================
# VARIÁVEIS GLOBAIS
# ============================================================================

debouncer: Optional[MessageDebouncer] = None


@app.on_event("startup")
async def startup():
    """Inicializa componentes"""
    global debouncer

    # Inicializa debouncer com 5 segundos de espera
    debouncer = MessageDebouncer(wait_seconds=5.0)

    logger.success("✅ Sistema iniciado com debouncer!")


@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook que recebe mensagens do WhatsApp
    """
    try:
        # 1. Recebe payload do webhook
        payload = await request.json()

        # 2. Extrai dados importantes
        phone = payload['message']['sender']  # Telefone do lead
        message_text = payload['message']['text']  # Texto da mensagem
        push_name = payload['chat']['name']  # Nome do lead

        # 3. LOG: Mensagem recebida
        logger.info(f"📨 Mensagem de {phone}: '{message_text}'")

        # 4. ADICIONA AO DEBOUNCER (não processa imediatamente!)
        await debouncer.add_message(
            phone=phone,
            message=message_text,
            callback=lambda p, m: process_message(p, m, push_name)
        )

        # 5. Retorna sucesso imediatamente (não espera processar)
        return JSONResponse({"status": "queued"})

    except Exception as e:
        logger.error(f"💥 Erro no webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_message(phone: str, combined_message: str, push_name: str):
    """
    Função chamada pelo debouncer após agrupar mensagens.

    Args:
        phone: Telefone do lead
        combined_message: Mensagens combinadas separadas por \n
        push_name: Nome do lead
    """
    try:
        logger.info(f"🤖 Processando mensagem combinada de {phone}")
        logger.debug(f"📝 Mensagem: {combined_message}")

        # 1. Busca ou cria sessão do lead
        session = await session_manager.get_or_create_session(phone)

        # 2. Processa com a IA
        response = await paula_agent.chat(
            message=combined_message,
            state=session,
            phone=phone,
            push_name=push_name
        )

        # 3. Envia resposta via WhatsApp
        await whatsapp_api.send_text(phone, response)

        # 4. Salva no banco de dados
        await salvar_mensagem(
            conversa_id=session.get("conversa_id"),
            remetente="usuario",
            conteudo=combined_message
        )

        await salvar_mensagem(
            conversa_id=session.get("conversa_id"),
            remetente="assistente",
            conteudo=response
        )

        logger.success(f"✅ Resposta enviada para {phone}")

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}")
```

---

### Passo 3: Adicionar Comando de Reset

```python
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    # ... código anterior ...

    # COMANDO ESPECIAL: /reset ou /delete
    if message_text.strip().lower() in ['/reset', '/delete', '/limpar']:
        logger.warning(f"🔄 Comando /delete recebido de {phone}")

        # IMPORTANTE: Limpa buffer ANTES de resetar
        debouncer.clear_buffer(phone)

        # Deleta sessão, conversa, etc
        await session_manager.delete_session(phone)

        await whatsapp_api.send_text(
            phone,
            "✅ Memória resetada com sucesso! Vamos começar do zero."
        )

        return JSONResponse({"status": "reset_complete"})

    # Adiciona ao debouncer normalmente
    await debouncer.add_message(...)
```

---

## ⚙️ Configuração

### Tempo de Espera (wait_seconds)

```python
# Ajustar tempo de espera
debouncer = MessageDebouncer(wait_seconds=5.0)  # 5 segundos (padrão)
debouncer = MessageDebouncer(wait_seconds=3.0)  # 3 segundos (mais rápido)
debouncer = MessageDebouncer(wait_seconds=10.0) # 10 segundos (mais lento)
```

**Recomendações**:
- **3-5 segundos**: Usuários digitam rápido
- **5-7 segundos**: Usuários médios (recomendado)
- **7-10 segundos**: Usuários lentos ou com mensagens longas

### Via Variável de Ambiente

```python
# config.py
class Settings(BaseSettings):
    debounce_seconds: float = 5.0  # Configurável via .env

# main.py
from config import settings

debouncer = MessageDebouncer(wait_seconds=settings.debounce_seconds)
```

```bash
# .env
DEBOUNCE_SECONDS=5.0
```

---

## 🧪 Como Testar

### Teste Manual

1. **Envie múltiplas mensagens rápidas**:
```
Você: "Oi"
Você: "quero botox"
Você: "quanto custa"
(aguarde 5 segundos)
```

2. **Verifique os logs**:
```
📩 Mensagem adicionada ao buffer [5521999999999]: 'Oi' (total: 1 msgs)
⏱️  Timer anterior cancelado para 5521999999999
⏳ Aguardando 5s de silêncio para 5521999999999...

📩 Mensagem adicionada ao buffer [5521999999999]: 'quero botox' (total: 2 msgs)
⏱️  Timer anterior cancelado para 5521999999999
❌ Timer cancelado para 5521999999999 (nova mensagem chegou)
⏳ Aguardando 5s de silêncio para 5521999999999...

📩 Mensagem adicionada ao buffer [5521999999999]: 'quanto custa' (total: 3 msgs)
⏱️  Timer anterior cancelado para 5521999999999
❌ Timer cancelado para 5521999999999 (nova mensagem chegou)
⏳ Aguardando 5s de silêncio para 5521999999999...

✅ Processando 3 mensagem(ns) agrupada(s) de 5521999999999:
   'Oi
    quero botox
    quanto custa'
```

3. **Resultado esperado**: 1 única resposta após 5 segundos

### Teste de Múltiplos Usuários

```python
# Envie mensagens de 2 usuários diferentes simultaneamente
# Cada um deve ter seu próprio buffer independente
```

---

## 🐛 Troubleshooting

### Problema 1: Mensagens não são agrupadas

**Causa**: Tempo de espera muito curto

**Solução**: Aumente `wait_seconds`:
```python
debouncer = MessageDebouncer(wait_seconds=7.0)
```

### Problema 2: Resposta demora muito

**Causa**: Tempo de espera muito longo

**Solução**: Diminua `wait_seconds`:
```python
debouncer = MessageDebouncer(wait_seconds=3.0)
```

### Problema 3: Buffer não limpa após /reset

**Causa**: Esqueceu de chamar `clear_buffer`

**Solução**: Sempre limpe o buffer ao resetar:
```python
debouncer.clear_buffer(phone)
await session_manager.delete_session(phone)
```

### Problema 4: Múltiplas respostas ainda aparecem

**Causa**: Buffer não está sendo usado no webhook

**Solução**: Certifique-se de usar `debouncer.add_message()` no webhook

---

## 📊 Métricas e Monitoramento

### Verificar tamanho do buffer

```python
# Quantas mensagens estão pendentes para um usuário
buffer_size = debouncer.get_buffer_size("5521999999999")
print(f"Mensagens no buffer: {buffer_size}")
```

### Dashboard de Monitoramento

```python
@app.get("/admin/debouncer/status")
async def debouncer_status():
    """Retorna status do debouncer"""
    return {
        "active_buffers": len(debouncer.message_buffer),
        "active_timers": len(debouncer.timers),
        "buffers": {
            phone: len(messages)
            for phone, messages in debouncer.message_buffer.items()
        }
    }
```

---

## 🚀 Melhorias Futuras

### 1. Timeout Máximo
Evitar que mensagens fiquem no buffer indefinidamente:

```python
class MessageDebouncer:
    def __init__(self, wait_seconds: float = 5.0, max_wait: float = 30.0):
        self.wait_seconds = wait_seconds
        self.max_wait = max_wait  # Timeout máximo
        # ...
```

### 2. Limite de Mensagens
Processar automaticamente após X mensagens:

```python
async def add_message(self, phone: str, message: str, callback):
    # ...

    # Se buffer atingiu 10 mensagens, processa imediatamente
    if len(self.message_buffer[phone]) >= 10:
        await self._process_now(phone, callback)
```

### 3. Prioridade de Usuários
VIPs têm tempo de espera menor:

```python
async def add_message(self, phone: str, message: str, callback, priority: str = "normal"):
    wait_time = self.wait_seconds

    if priority == "vip":
        wait_time = 2.0  # VIPs: 2 segundos
    elif priority == "urgent":
        wait_time = 1.0  # Urgente: 1 segundo

    # ...
```

---

## ✅ Checklist de Implementação

- [ ] Criar arquivo `utils/debouncer.py` com a classe `MessageDebouncer`
- [ ] Importar e inicializar no `main.py` (ou arquivo principal)
- [ ] Integrar no webhook: `debouncer.add_message()`
- [ ] Implementar `process_message()` callback
- [ ] Adicionar `clear_buffer()` no comando /reset
- [ ] Configurar `wait_seconds` adequado (5.0 recomendado)
- [ ] Testar com múltiplas mensagens rápidas
- [ ] Testar com múltiplos usuários simultaneamente
- [ ] Adicionar logs para debug
- [ ] Monitorar em produção

---

## 📚 Referências

- **AsyncIO Tasks**: https://docs.python.org/3/library/asyncio-task.html
- **AsyncIO Locks**: https://docs.python.org/3/library/asyncio-sync.html
- **Debouncing Pattern**: https://css-tricks.com/debouncing-throttling-explained-examples/

---

## 💡 Resumo para Claude

Para implementar este sistema em outro agente de IA:

1. **Copie** o arquivo `utils/debouncer.py` completo
2. **Importe** no seu webhook: `from utils.debouncer import MessageDebouncer`
3. **Inicialize** na startup: `debouncer = MessageDebouncer(wait_seconds=5.0)`
4. **Use no webhook**: Em vez de processar direto, chame:
   ```python
   await debouncer.add_message(
       phone=phone,
       message=message_text,
       callback=lambda p, m: your_process_function(p, m, extra_params)
   )
   ```
5. **Limpe buffer** ao resetar: `debouncer.clear_buffer(phone)`

**Pronto!** O sistema vai automaticamente agrupar mensagens e processar após 5 segundos de silêncio.
