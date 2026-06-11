-- Create required Supabase tables for the task manager app

create extension if not exists pgcrypto;

create table if not exists profiles (
  id uuid primary key,
  email text unique not null,
  full_name text,
  updated_at timestamptz default now()
);

create table if not exists tasks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  status text default 'Open',
  creator_id uuid references profiles(id),
  assignee_id uuid references profiles(id),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
