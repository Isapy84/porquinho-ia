-- ====================================================================
-- Script SQL para criar a tabela do Porquinho IA no Supabase
-- Basta copiar este código, colar no "SQL Editor" do Supabase e clicar em "Run".
-- ====================================================================

create table if not exists public.user_finances (
    user_id text primary key,
    orcamento_inicial double precision default 0.0,
    saldo_atual double precision default 0.0,
    gastos jsonb default '[]'::jsonb,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Habilita segurança em nível de linha (RLS)
alter table public.user_finances enable row level security;

-- Cria política que permite ao bot ler e gravar dados usando a chave de API
create policy "Permitir acesso completo para o bot"
on public.user_finances
for all
using (true)
with check (true);
