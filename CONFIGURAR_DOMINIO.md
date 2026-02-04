# Configurar Domínio Próprio - Smith 2.0

## 🌐 Arquitetura Recomendada

Supondo seu domínio: **automatex.com.br**

```
admin.automatex.com.br   → Admin Portal (Vercel)
portal.automatex.com.br  → Cliente Portal (Vercel)
api.automatex.com.br     → Backend API (Railway)
```

---

## 📋 PASSO 1: Configurar DNS no Registro.br

1. Acesse: https://registro.br
2. Faça login
3. Vá em **"Meus domínios"**
4. Clique no seu domínio
5. Vá em **"DNS"** → **"Modo Avançado"**

### Adicione os seguintes registros:

```dns
Tipo    Nome      Valor                                               TTL
------  --------  ------------------------------------------------    -----
CNAME   admin     cname.vercel-dns.com.                              3600
CNAME   portal    cname.vercel-dns.com.                              3600
CNAME   api       smith-vendas-sistema-production.up.railway.app.    3600
```

**⚠️ IMPORTANTE**:
- Coloque o **ponto (.)** no final de cada valor!
- Substitua `smith-vendas-sistema-production.up.railway.app` pela URL real do Railway

**Tempo de Propagação**: 5 minutos a 48 horas (geralmente ~30 minutos)

---

## 🎨 PASSO 2: Configurar Domínios na Vercel

### 2.1 Adicionar admin.automatex.com.br

1. Vá no projeto Vercel
2. **"Settings"** → **"Domains"**
3. Clique em **"Add"**
4. Digite: `admin.automatex.com.br`
5. Clique em **"Add"**

Vercel vai mostrar instruções de DNS (você já configurou no Passo 1).

### 2.2 Adicionar portal.automatex.com.br

Repita o processo:
1. Clique em **"Add"** novamente
2. Digite: `portal.automatex.com.br`
3. Clique em **"Add"**

### 2.3 Configurar Domínio Principal (Opcional)

Se quiser que `automatex.com.br` (sem subdomínio) redirecione:

1. Adicione `automatex.com.br` como domínio
2. Configure no DNS do Registro.br:
   ```dns
   Tipo   Nome    Valor                  TTL
   ----   ----    --------------------   -----
   A      @       76.76.21.21           3600
   ```

3. Configure redirect na Vercel:
   - `automatex.com.br` → `portal.automatex.com.br`

---

## 🚂 PASSO 3: Configurar Domínio no Railway

### 3.1 Adicionar Custom Domain

1. Vá no projeto Railway
2. Clique em **"Settings"**
3. Vá em **"Networking"**
4. Em **"Custom Domain"**, clique em **"Add Domain"**
5. Digite: `api.automatex.com.br`
6. Clique em **"Add"**

Railway vai mostrar o endereço CNAME (você já configurou no Passo 1).

### 3.2 Aguardar Ativação

- Railway verifica automaticamente o DNS
- Quando estiver pronto, aparecerá um ✅ verde
- HTTPS é configurado automaticamente (Let's Encrypt)

---

## 🔄 PASSO 4: Atualizar Variáveis de Ambiente

### 4.1 Na Vercel (Frontend)

1. Vá em **"Settings"** → **"Environment Variables"**
2. Edite `NEXT_PUBLIC_API_URL`:
   ```
   https://api.automatex.com.br
   ```
3. Salve
4. Vá em **"Deployments"** → Último deploy → **"Redeploy"**

### 4.2 No Railway (Backend)

1. Vá em **"Variables"**
2. Edite `CORS_ORIGINS`:
   ```
   https://admin.automatex.com.br,https://portal.automatex.com.br,http://localhost:3004
   ```
3. Salve (Railway redeploya automaticamente)

---

## ✅ PASSO 5: Testar Configuração

### Teste 1: DNS Propagado?

No terminal (PowerShell):
```powershell
nslookup admin.automatex.com.br
nslookup portal.automatex.com.br
nslookup api.automatex.com.br
```

Deve retornar endereços válidos.

### Teste 2: Backend Funcionando

Abra no navegador:
```
https://api.automatex.com.br/health
```

Deve retornar:
```json
{"status":"healthy"}
```

### Teste 3: Admin Portal

1. Acesse: `https://admin.automatex.com.br`
2. Deve redirecionar para login
3. Faça login: `pedro@automatex.com.br` / `Smith2026!`
4. Dashboard deve carregar!

### Teste 4: Cliente Portal

1. Acesse: `https://portal.automatex.com.br`
2. Deve mostrar tela de login do cliente
3. Ou acesse link direto de projeto

---

## 📱 BONUS: Atualizar PWA para Domínio Próprio

<function_calls>
<invoke name="Read">
<parameter name="file_path">c:\Users\pedro\Desktop\smith-vendas\frontend\public\manifest.json

## 📱 PWA com Domínio Customizado

O PWA já está configurado e funcionará automaticamente com seus domínios customizados.

Cada subdomínio terá seu próprio PWA:
- **admin.automatex.com.br**: PWA para admin
- **portal.automatex.com.br**: PWA para clientes

---

## 🔒 SSL/HTTPS Automático

### Vercel
- SSL configurado automaticamente (Let's Encrypt)
- Certificado renovado automaticamente
- Nada a fazer\!

### Railway
- SSL configurado automaticamente
- Certificado renovado automaticamente
- Nada a fazer\!

**Seu site estará 100% HTTPS em ~5 minutos após DNS propagar.**

---

## 🐛 Troubleshooting

### DNS não propaga
**Problema**: Domínio não resolve após 1 hora

**Solução**:
1. Verifique se adicionou o ponto (.) no final dos CNAMEs
2. Teste DNS: \Servidor:  UnKnown
Address:  2804:14d:1:0:181:213:132:2
3. Aguarde até 48h (raro, mas pode acontecer)
4. Limpe cache DNS local: Erro: linha de comando n�o reconhecida ou incompleta.

USO:
    ipconfig [/allcompartments] [/? | /all |
                                 /renew [adapter] | /release [adapter] |
                                 /renew6 [adapter] | /release6 [adapter] |
                                 /flushdns | /displaydns | /registerdns |
                                 /showclassid adapter |
                                 /setclassid adapter [classid] |
                                 /showclassid6 adapter |
                                 /setclassid6 adapter [classid] ]

onde
    o nome da conex�o             do adaptador
                       (caracteres curinga * e ? permitidos, veja os exemplos)

    Op��es:
       /?               Exibir essa mensagem de ajuda
       /all             Exibir informa��es completas da configura��o.
       /release         Libere o endere�o IPv4 do adaptador especificado.
       /release6        Liberar o endere�o IPv6 para o adaptador especificado.
       /renew           Renovar o endere�o IPv4 do adaptador especificado.
       /renew6          Renovar o endere�o IPv6 para o adaptador especificado.
       /flushdns        Limpa o cache do Resolvedor de DNS.
       /registerdns     Atualiza todas as concess�es de DHCP e registra novamente os nomes de DNS
       /displaydns      Exibir o conte�do do Cache do Resolvedor de DNS.
       /showclassid     Exibe todas as IDs da classe DHCP permitidas para o adaptador.
       /setclassid      Modifica a ID da classe DHCP.
       /showclassid6    Exibe todas as IDs da classe DHCP IPv6 permitidas para o adaptador.
       /setclassid6     Modifica a ID da classe DHCP IPv6.


O padr�o � exibir apenas o endere�o IP, a m�scara de sub-rede e o
gateway padr�o para cada adaptador ligado ao TCP/IP.

Para Libera��o e Renova��o, se nenhum nome de adaptador for especificado, as concess�es de endere�o IP
para todos os adaptadores vinculados ao TCP/IP ser�o liberadas ou renovadas.

Para Setclassid e Setclassid6, se nenhuma ClassId for especificada, a ClassId ser� removida.

Exemplos:
    > ipconfig                       ... Mostrar informa��es
    > ipconfig /all                  ... Mostrar informa��es detalhadas
    > ipconfig /renew                ... renovar todos os adaptadores
    > ipconfig /renew EL*            ... renovar qualquer conex�o que tenha seu
                                         nome iniciado por EL
    > ipconfig /release *Con*        ... liberar todas as conex�es correspondentes,
                                         por exemplo, Conex�o Ethernet com Fio 1 ou
                                             Conex�o Ethernet com fio 2
    > ipconfig /allcompartments      ... Mostrar informa��es sobre todos
                                         os compartimentos
    > ipconfig /allcompartments /all ... Mostrar informa��es detalhadas sobre todos
                                         os compartimentos

### Vercel não valida domínio
**Problema**: Vercel mostra "Invalid Configuration"

**Solução**:
1. Verifique CNAME no Registro.br
2. Aguarde 15-30 minutos
3. Na Vercel, clique em "Refresh" ao lado do domínio
4. Se persistir, remova e adicione novamente

### Railway não aceita domínio
**Problema**: Railway mostra erro ao adicionar custom domain

**Solução**:
1. Certifique que o CNAME aponta para o endereço correto do Railway
2. Domínio deve estar com DNS propagado primeiro
3. Tente remover e adicionar novamente

### CORS Error no frontend
**Problema**: Frontend não conecta ao backend

**Solução**:
1. Verifique se \ no Railway inclui:
   -    - 2. **SEM** barra (/) no final
3. **COM** https:// no início
4. Faça redeploy do Railway

### PWA não instala
**Problema**: Banner de instalação não aparece

**Solução**:
1. Certifique que está usando HTTPS
2. Limpe cache do navegador (Ctrl+Shift+Del)
3. Verifique se \ está acessível: 4. Teste em aba anônima

---

## 📊 Monitoramento

### Verificar Status dos Serviços

**Vercel**:
- Dashboard: https://vercel.com/dashboard
- Status: https://www.vercel-status.com/

**Railway**:
- Dashboard: https://railway.app/dashboard
- Status: Veja logs em tempo real no dashboard

**Supabase**:
- Dashboard: https://supabase.com/dashboard
- Status: https://status.supabase.com/

---

## 🎯 Resumo das URLs Finais

Depois da configuração:

| Serviço        | URL                             | Acesso        |
|----------------|---------------------------------|---------------|
| Admin Portal   | admin.automatex.com.br          | Você          |
| Cliente Portal | portal.automatex.com.br         | Clientes      |
| Backend API    | api.automatex.com.br            | Interno       |
| GitHub         | github.com/Pedroax/smith-vendas | Código        |

---

## 🚀 Próximos Passos

1. ✅ Configure DNS no Registro.br (PASSO 1)
2. ✅ Adicione domínios na Vercel (PASSO 2)
3. ✅ Adicione domínio no Railway (PASSO 3)
4. ✅ Atualize variáveis de ambiente (PASSO 4)
5. ✅ Teste tudo (PASSO 5)
6. 🎉 Sistema no ar com domínio próprio\!

---

## 💡 Dicas Profissionais

### SEO (Opcional)
Adicione no \ do HTML:
- Meta description personalizada
- Open Graph tags para redes sociais
- Favicon customizado

### Analytics (Opcional)
Integre:
- Google Analytics
- Hotjar (mapas de calor)
- Sentry (monitoramento de erros)

### Email Profissional
Configure email com seu domínio:
- contato@automatex.com.br
- suporte@automatex.com.br

Use: Gmail for Business, Zoho Mail, ou Microsoft 365

---

✨ **Pronto\!** Seu sistema terá URLs profissionais e personalizadas\!
