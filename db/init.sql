CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sessions (
    id            VARCHAR(36) PRIMARY KEY,
    title         VARCHAR(200),
    system_prompt TEXT DEFAULT '',
    few_shots     TEXT DEFAULT '[]',
    use_knowledge BOOLEAN DEFAULT FALSE,
    temperature   DOUBLE PRECISION DEFAULT 0.7,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id         SERIAL PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES sessions(id) ON DELETE CASCADE,
    role       VARCHAR(20) NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);

CREATE TABLE IF NOT EXISTS documents (
    id           SERIAL PRIMARY KEY,
    filename     VARCHAR(300) NOT NULL,
    file_path    VARCHAR(500),
    chunk_count  INTEGER DEFAULT 0,
    status       VARCHAR(20) DEFAULT 'pending',
    is_knowledge BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS embeddings (
    id          SERIAL PRIMARY KEY,
    doc_id      INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text  TEXT NOT NULL,
    embedding   vector(1024),
    chunk_index INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
    ON embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Migration support for older databases (if they already exist without these columns)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS is_knowledge BOOLEAN DEFAULT FALSE;
ALTER TABLE sessions  ADD COLUMN IF NOT EXISTS system_prompt TEXT DEFAULT '';
ALTER TABLE sessions  ADD COLUMN IF NOT EXISTS few_shots     TEXT DEFAULT '[]';
ALTER TABLE sessions  ADD COLUMN IF NOT EXISTS use_knowledge BOOLEAN DEFAULT FALSE;
ALTER TABLE sessions  ADD COLUMN IF NOT EXISTS temperature   DOUBLE PRECISION DEFAULT 0.7;

CREATE TABLE IF NOT EXISTS rag_settings (
    id             INTEGER PRIMARY KEY,
    chunk_size     INTEGER DEFAULT 500,
    chunk_overlap  INTEGER DEFAULT 50,
    retrieve_top_k INTEGER DEFAULT 10,
    rerank_top_n   INTEGER DEFAULT 3
);

INSERT INTO rag_settings (id, chunk_size, chunk_overlap, retrieve_top_k, rerank_top_n)
VALUES (1, 500, 50, 10, 3)
ON CONFLICT (id) DO NOTHING;
