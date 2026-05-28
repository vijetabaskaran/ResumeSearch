-- PostgreSQL Database Setup Script for Resume Screening Portal
-- Schema v4: Role-based auth — official accounts must be created manually.

-- =============================================================================
-- HOW TO CREATE AN OFFICIAL/ADMIN ACCOUNT
-- =============================================================================
-- Official accounts are NOT publicly registerable. To add a new official:
--
--   1. Generate a bcrypt hash for the password (e.g., using Python):
--        python -c "import bcrypt; print(bcrypt.hashpw(b'YourPassword', bcrypt.gensalt()).decode())"
--
--   2. Insert directly into the users table:
--        INSERT INTO users (username, email, password, role, name)
--        VALUES ('admin_user', 'admin@example.com', '<bcrypt_hash>', 'official', 'Admin Name');
--
--   Note: The application seeds a default official account automatically at startup
--   using the DEFAULT_ADMIN_USERNAME / DEFAULT_ADMIN_PASSWORD env vars.
-- =============================================================================


CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    password TEXT NOT NULL,
    role VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_name VARCHAR(255) NOT NULL,
    sender_email VARCHAR(255) NOT NULL,
    sender_username VARCHAR(100),
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP
);

ALTER TABLE messages ADD COLUMN IF NOT EXISTS sender_username VARCHAR(100);

CREATE TABLE IF NOT EXISTS replies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    sender_username VARCHAR(100) NOT NULL,
    reply_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS job_descriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP
);
