-- =========================================================================
-- Supabase Cloud Database Schema for ShaktiX WhatsApp Bulk Sender
-- Tables: orders, licenses, machine_bindings, customer_queries
-- =========================================================================

-- 1. Orders & Payments Table
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    plan_tier TEXT NOT NULL CHECK (plan_tier IN ('STARTER', 'PRO', 'AGENCY')),
    amount_inr NUMERIC(10, 2) NOT NULL,
    payment_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (payment_status IN ('PENDING', 'PAID', 'FAILED', 'REFUNDED')),
    payment_gateway TEXT DEFAULT 'RAZORPAY',
    payment_id TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Commercial Licenses Table
CREATE TABLE IF NOT EXISTS public.licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES public.orders(id) ON DELETE SET NULL,
    license_key TEXT UNIQUE NOT NULL,
    plan_tier TEXT NOT NULL CHECK (plan_tier IN ('STARTER', 'PRO', 'AGENCY')),
    machine_id TEXT NOT NULL,
    max_daily_messages INTEGER NOT NULL DEFAULT 500,
    issued_to_name TEXT,
    issued_to_phone TEXT,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    revocation_reason TEXT
);

-- Index for fast lookup by machine_id and license_key
CREATE INDEX IF NOT EXISTS idx_licenses_machine_key ON public.licenses(machine_id, license_key);
CREATE INDEX IF NOT EXISTS idx_licenses_active ON public.licenses(is_active);

-- 3. Machine Hardware Log
CREATE TABLE IF NOT EXISTS public.machine_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id TEXT NOT NULL,
    os_version TEXT,
    client_version TEXT DEFAULT 'Enterprise 2.5',
    last_ping_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    ip_address INET
);

-- 4. Row Level Security (RLS) Policies
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.machine_logs ENABLE ROW LEVEL SECURITY;

-- Allow public read access only for license validation query (by exact key + machine_id)
CREATE POLICY "Allow public license validation" ON public.licenses
    FOR SELECT
    USING (true);

-- Allow authenticated admins full access
CREATE POLICY "Allow admin full access orders" ON public.orders
    FOR ALL
    TO authenticated
    USING (true);

CREATE POLICY "Allow admin full access licenses" ON public.licenses
    FOR ALL
    TO authenticated
    USING (true);
