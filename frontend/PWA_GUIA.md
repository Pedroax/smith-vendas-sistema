# Guia PWA - Smith 2.0 Portal

## ✅ O que foi implementado

1. **Service Worker com cache inteligente**
   - Cache de assets estáticos (JS, CSS, imagens)
   - Cache de API com NetworkFirst strategy
   - Cache offline de páginas visitadas

2. **Manifest.json configurado**
   - Ícones em múltiplos tamanhos (72x72 até 512x512)
   - Nome, cores, descrição do app
   - Shortcuts para acesso rápido

3. **Meta tags PWA**
   - Apple touch icons
   - Theme color
   - Status bar style

4. **Banner de instalação**
   - Aparece após 30s de uso
   - Pode ser dismissado
   - Salva preferência do usuário

## 📱 Como Testar no Celular

### Android (Chrome)

1. Acesse o site no Chrome mobile
2. Aguarde 30 segundos ou vá no menu (⋮) > "Instalar app"
3. Clique em "Instalar"
4. O app aparecerá na tela inicial

### iPhone (Safari)

1. Acesse o site no Safari
2. Toque no botão de compartilhar (□↑)
3. Role para baixo e toque em "Adicionar à Tela de Início"
4. Personalize o nome se quiser
5. Toque em "Adicionar"

## 🖥️ Como Testar no Desktop

### Chrome/Edge

1. Abra o DevTools (F12)
2. Vá na aba "Application"
3. Na seção "Manifest" você verá as configurações
4. Na seção "Service Workers" você verá o worker ativo
5. Clique no ícone "+" na barra de endereço para instalar

### Testar Offline

1. No DevTools > Application > Service Workers
2. Marque "Offline"
3. Navegue pelo site - páginas visitadas funcionarão offline!

## 🚀 Deploy para Produção

### Passo 1: Build de produção
```bash
cd frontend
npm run build
```

### Passo 2: Configurar domínio
Atualize estas variáveis:
- `NEXT_PUBLIC_API_URL` - URL da API em produção
- `CORS_ORIGINS` no backend - incluir domínio de produção

### Passo 3: Deploy
- **Vercel**: `vercel --prod`
- **Netlify**: `netlify deploy --prod`
- **Railway/Render**: Push para branch main

### Passo 4: Verificar PWA
Acesse: https://web.dev/measure/
Cole seu domínio e verifique o score PWA

## 🎨 Personalizar Ícones

Os ícones atuais são placeholders azuis com "S2".

### Opção 1: Gerar Online (Recomendado)
1. Acesse: https://realfavicongenerator.net/
2. Faça upload do seu logo
3. Configure as opções
4. Baixe o pacote
5. Substitua os arquivos em `public/icons/`

### Opção 2: Editar Manualmente
1. Crie um logo 512x512px
2. Use o script: `python generate_pwa_icons.py`
3. Personalize as cores no script

## 📊 Funcionalidades PWA Implementadas

- [x] Instalável (Add to Home Screen)
- [x] Cache offline de assets estáticos
- [x] Cache offline de API
- [x] Ícones para todas as plataformas
- [x] Splash screen (iOS/Android)
- [x] Theme color
- [x] Banner de instalação customizado
- [x] Shortcuts (atalhos rápidos)

## 🔔 Próximos Passos (Opcional)

### 1. Push Notifications
Adicionar notificações push quando:
- Cliente aprova/rejeita entrega
- Pagamento confirmado
- Novo comentário

Requer: Firebase Cloud Messaging ou OneSignal

### 2. Background Sync
Sincronizar dados quando voltar online:
- Uploads de arquivos pendentes
- Comentários salvos

### 3. Geolocalização
- Rastrear check-ins de vendedores
- Mapas de clientes

## 🐛 Troubleshooting

### Service Worker não atualiza
1. No DevTools > Application > Service Workers
2. Marque "Update on reload"
3. Force refresh (Ctrl+Shift+R)

### Manifest não carrega
1. Verifique console de erros
2. Valide JSON: https://manifest-validator.appspot.com/
3. Certifique-se que `manifest.json` está em `public/`

### Ícones não aparecem
1. Verifique se os arquivos existem em `public/icons/`
2. Limpe cache do navegador
3. Rode `python generate_pwa_icons.py` novamente

## 📝 Configuração para Desenvolvimento

Por padrão, PWA está **desabilitado em dev** para facilitar debug.

Para testar em dev:
```javascript
// next.config.mjs
disable: false, // Mudar de process.env.NODE_ENV === 'development'
```

## 🎯 Checklist Final

Antes de lançar:
- [ ] Testar instalação no Android
- [ ] Testar instalação no iOS
- [ ] Testar funcionamento offline
- [ ] Substituir ícones placeholder
- [ ] Testar em 4G lento
- [ ] Verificar cache funciona
- [ ] Testar shortcuts do manifest

## 📚 Recursos Úteis

- PWA Builder: https://www.pwabuilder.com/
- Lighthouse (teste PWA): Chrome DevTools > Lighthouse
- Web.dev PWA: https://web.dev/progressive-web-apps/
- Can I Use PWA: https://caniuse.com/?search=pwa

---

✨ **Pronto!** Seu sistema agora é um PWA completo e pode ser instalado como app nativo!
