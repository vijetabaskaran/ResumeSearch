-- PostgreSQL Database Setup Script for Resume Screening Portal
-- Schema v2: Native UUID keys, audit timestamps, soft deletes, bcrypt passwords

-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- DROP OLD TABLES (migration from v1 schema)
-- ==========================================
DROP TABLE IF EXISTS job_descriptions CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ==========================================
-- USERS TABLE
-- ==========================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP
);

-- ==========================================
-- MESSAGES / EMAILS TABLE
-- ==========================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_name VARCHAR(255) NOT NULL,
    sender_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP
);

-- ==========================================
-- JOB DESCRIPTIONS TABLE
-- ==========================================
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP
);

-- ==========================================
-- SEED DEFAULT DEMO ACCOUNTS
-- Passwords are bcrypt hashes of "password"
-- ==========================================
INSERT INTO users (username, password, role, name)
VALUES
    ('candidate', '$2b$12$8YwUwmrRZ6DemZw3t/XU5uu2EgVK9NDwyan6rjr.NwBjsz6BMtt3K', 'candidate', 'Candidate User'),
    ('official',  '$2b$12$8YwUwmrRZ6DemZw3t/XU5uu2EgVK9NDwyan6rjr.NwBjsz6BMtt3K', 'official',  'Official Admin')
ON CONFLICT (username) DO NOTHING;
