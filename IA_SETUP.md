# 🤖 Configuração da IA - IH (Gemini + Claude)

## 🎯 Resumo Rápido

Seu sistema agora suporta **dois provedores de IA**:
- ✅ **Google Gemini** (RECOMENDADO) - Gratuito, limite generoso
- ⚠️ **Anthropic Claude** - Pago, muito inteligente

**Prioridade automática:**
1. Tenta Claude (mais inteligente)
2. Se falhar por crédito/erro → Automaticamente tenta Gemini
3. Mostra mensagem se nenhuma IA estiver disponível

---

## 📝 Como Configurar

### Opção 1️⃣: Google Gemini (Recomendado ✅)

#### ✅ Vantagens:
- **Gratuito** 🎉
- Limite generoso (60+ requisições/minuto)
- Sem cartão de crédito necessário
- Integrado com fallback automático

#### 🔧 Passos:

1. **Obter a chave:**
   - Acesse: [https://aistudio.google.com/app/apikeys](https://aistudio.google.com/app/apikeys)
   - Clique em **"Create API Key"** (ou "Criar Nova Chave")
   - Copie a chave gerada

2. **Adicionar ao projeto:**
   - Abra `.env` (ou renomeie `.env.example` → `.env`)
   - Cole no campo `GOOGLE_API_KEY`:
     ```env
     GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```
   - Salve o arquivo

3. **Pronto!** 🚀 Gemini está ativo

---

### Opção 2️⃣: Anthropic Claude (Opcional)

#### ⚠️ Aviso:
- **Pago** 💰 (cobrado por tokens)
- Mais inteligente que Gemini
- Recomendado refazer Gemini para economizar

#### 🔧 Passos:

1. **Obter a chave:**
   - Acesse: [https://console.anthropic.com/](https://console.anthropic.com/)
   - Login com conta Anthropic
   - Vá em **Settings** → **API Keys**
   - Clique em **"Create Key"**
   - Copie a chave

2. **Adicionar ao projeto:**
   - Abra `.env`
   - Cole no campo `ANTHROPIC_API_KEY`:
     ```env
     ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
     ```
   - (Opcional) escolha o modelo:
     ```env
     ANTHROPIC_MODEL=claude-opus-4-5
     ```

3. **Configure também um cartão de crédito:**
   - Claude cobra por use → [Billing](https://console.anthropic.com/settings/billing)

---

## 🎮 Como Usar

Após configurar o `.env`, reinicie a aplicação Streamlit:

```bash
# Ativar ambiente virtual (se não ativado)
.\.venv\Scripts\Activate.ps1

# Instalar dependências (primeira vez)
pip install -r requirements.txt

# Iniciar app
python -m streamlit run app.py
```

Na aba **"🤖 IA - IH"** do dashboard:
1. Escreva sua pergunta
2. Clique em **📤** para enviar
3. IA responde automaticamente! ✨

---

## 🔄 Fluxo Automático de Fallback

```
┌─────────────────────────┐
│  Usuário envia pergunta  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Tenta Claude (Anthropic) │
└────────────┬────────────┘
             │
        ┌────┴────┐
        │          │
   Sucesso!    Erro?
        │          │
        │          ▼
        │    ┌──────────────┐
        │    │ Erro de       │
        │    │ crédito ou    │
        │    │ autenticação? │
        │    └──────┬───────┘
        │           │
        │      Sim  │  Não
        │           │  │
        │           │  ▼
        │           │ ┌──────────────┐
        │           │ │ Retorna erro │
        │           │ │ amigável      │
        │           │ └──────────────┘
        │           │
        │       ┌───┘
        │       │
        │       ▼
        │    ┌──────────────┐
        │    │  Tenta       │
        │    │  Gemini      │
        │    └──────┬───────┘
        │           │
        │      ┌────┴────┐
        │      │          │
        │  Sucesso!   Erro
        │      │          │
        │      │          ▼
        │      │    ┌───────────────┐
        │      │    │ Retorna erro  │
        │      │    │ Gemini        │
        │      │    └───────────────┘
        │      │
        └──────┼───────────────────┐
               │                   │
               ▼                   ▼
        ┌──────────────┬────────────────┐
        │              │                │
        │  Resposta    │  Mensagem de   │
        │  da IA ✅    │  Erro ⚠️       │
        │              │                │
```

---

## ❓ Dúvidas Comuns

### P: Qual IA é mais inteligente?
**R:** Claude (Anthropic) é mais inteligente, mas Gemini é excelente para a maioria das tarefas. O sistema tenta Claude primeiro.

### P: Posso usar apenas Gemini?
**R:** Sim! Deixe `ANTHROPIC_API_KEY` vazio e use apenas `GOOGLE_API_KEY`.

### P: Posso usar apenas Claude?
**R:** Sim, configure apenas `ANTHROPIC_API_KEY`. Se falhar, a IA mostrará que precisa de créditos.

### P: Qual é mais barato?
**R:** **Gemini é gratuito**! Claude é pago. Use Gemini para economizar 💰

### P: Se ambas falharem, o que acontece?
**R:** Será mostrada uma mensagem amigável pedindo para configurar uma das chaves.

---

## 🚀 Próximos Passos

1. ✅ Instale as dependências: `pip install -r requirements.txt`
2. ✅ Configure `.env` com sua chave (pelo menos Gemini)
3. ✅ Reinicie Streamlit
4. ✅ Teste na aba "🤖 IA - IH"

---

## 📞 Support

Se tiver erros:
1. Verifique se `.env` foi criado (não `.env.example`)
2. Confirme que as chaves estão corretas
3. Reinicie Streamlit
4. Verifique a console para logs de erro

---

**Aproveite seu assistente IA! 🎉**
