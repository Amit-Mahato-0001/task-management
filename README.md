# Task Manager App

This repository contains a simple task management application built with:

- Database: Supabase
- Backend: Flask
- Frontend: Next.js + TypeScript
- Email notifications: Gmail SMTP
- Login: Google OAuth via Supabase

## Features

- Google account login
- Task creation
- Task assignment to other users
- Email notifications on task creation and completion

## Setup

### 1. Backend

1. Copy `backend/.env.example` to `backend/.env`.
2. Fill in your Supabase and Gmail credentials.
3. Install dependencies:

```bash
cd backend
python -m pip install -r requirements.txt
```

4. Run the backend:

```bash
python app.py
```

### 2. Frontend

1. Copy `frontend/.env.example` to `frontend/.env`.
2. Fill in your Supabase values and backend URL.
3. Install dependencies:

```bash
cd frontend
npm install
```

4. Run the frontend:

```bash
npm run dev
```

### 3. Supabase setup

Create tables in Supabase SQL editor:

```sql
create extension if not exists pgcrypto;

create table profiles (
  id uuid primary key,
  email text unique not null,
  full_name text,
  updated_at timestamp with time zone default now()
);

create table tasks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  status text default 'Open',
  creator_id uuid references profiles(id),
  assignee_id uuid references profiles(id),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

Enable Google login in the Supabase Authentication settings and use the same Google Cloud client credentials in the frontend.

### 4. Environment variables

Backend uses:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GMAIL_SMTP_USER`
- `GMAIL_APP_PASSWORD`
- `FRONTEND_URL` (optional)

Frontend uses:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_BACKEND_URL`

## Notes

- Gmail SMTP requires an app password or OAuth-enabled account.
- Supabase handles Google OAuth sign-in on the frontend.
- The backend verifies Supabase session tokens and manages tasks.
