-- PostgreSQL Database Setup Script for Resume Screening Portal

-- Create Users Table
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(100) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL
);

-- Create Messages/Emails Table
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(100) PRIMARY KEY,
    sender_name VARCHAR(255) NOT NULL,
    sender_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    timestamp VARCHAR(50) NOT NULL
);

-- Seed Default Candidate and Official Credentials
INSERT INTO users (username, password, role, name)
VALUES 
('candidate', 'password', 'candidate', 'Candidate User'),
('official', 'password', 'official', 'Official Admin')
ON CONFLICT (username) DO NOTHING;

-- Create Job Descriptions Table
CREATE TABLE IF NOT EXISTS job_descriptions (
    id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at VARCHAR(50) NOT NULL
);
