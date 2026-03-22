# Ital In House — Portal do Franqueado (Streamlit)

Dashboard com PostgreSQL, gráficos Plotly e assistente Anthropic.

## Configuração

1. Crie o virtualenv, instale dependências:

```bash
cd streamlit_portal
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Copie `.env.example` para `.env` e preencha `DB_*` e `ANTHROPIC_API_KEY`.

3. Execute a migração em `migrations/001_usuarios_unidades_metas.sql` no PostgreSQL (as demais tabelas já existem no seu banco).

4. Suba o app:

```bash
streamlit run app.py
```

## Isolamento

- **admin**: todas as linhas de `unidade_uf`.
- **franqueado**: apenas unidades ligadas em `usuarios_unidades`.

Todas as consultas de vendas/itens/clientes usam `trade_name` da unidade selecionada.
