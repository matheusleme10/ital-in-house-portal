CREATE TABLE IF NOT EXISTS usuarios_unidades (
    usuario_id  INT NOT NULL REFERENCES usuarios_portal(id) ON DELETE CASCADE,
    unidade_id  INT NOT NULL REFERENCES unidade_uf(id)      ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, unidade_id)
);
CREATE INDEX IF NOT EXISTS idx_uu_user ON usuarios_unidades(usuario_id);

CREATE TABLE IF NOT EXISTS metas (
    id                  SERIAL PRIMARY KEY,
    unidade_id          INT           NOT NULL REFERENCES unidade_uf(id),
    mes                 INT           NOT NULL CHECK (mes BETWEEN 1 AND 12),
    ano                 INT           NOT NULL,
    meta_vendas         NUMERIC(12,2) DEFAULT 0,
    realizado_vendas    NUMERIC(12,2) DEFAULT 0,
    meta_clientes       INT           DEFAULT 0,
    realizado_clientes  INT           DEFAULT 0,
    UNIQUE (unidade_id, mes, ano)
);
