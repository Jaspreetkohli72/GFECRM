-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.clients (
  id integer NOT NULL DEFAULT nextval('clients_id_seq'::regclass),
  name text NOT NULL,
  phone text,
  address text,
  status text DEFAULT 'Active'::text,
  created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
  start_date date,
  internal_estimate jsonb, -- {items: [], days: int, welders: int, helpers: int, profit_margin: int}
  client_estimate jsonb,
  final_settlement_amount numeric,
  next_action_date date,
  assigned_staff jsonb DEFAULT '[]'::jsonb,
  measurements text,
  image_urls ARRAY DEFAULT '{}'::text[],
  projects jsonb DEFAULT '[]'::jsonb,
  CONSTRAINT clients_pkey PRIMARY KEY (id)
);
CREATE TABLE public.inventory (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  item_name text NOT NULL,
  base_rate numeric NOT NULL,
  unit text DEFAULT 'pcs'::text,
  item_type text,
  dimension text,
  CONSTRAINT inventory_pkey PRIMARY KEY (id)
);
CREATE TABLE public.purchase_log (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  supplier_id bigint,
  item_name text,
  qty numeric,
  rate numeric,
  total_cost numeric,
  CONSTRAINT purchase_log_pkey PRIMARY KEY (id),
  CONSTRAINT purchase_log_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id)
);
CREATE TABLE public.settings (
  id bigint NOT NULL,
  daily_labor_cost numeric,
  advance_percentage numeric DEFAULT 10.0,
  profit_margin integer DEFAULT 15,
  CONSTRAINT settings_pkey PRIMARY KEY (id)
);
CREATE TABLE public.staff (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name text NOT NULL,
  role text NOT NULL,
  phone text,
  salary numeric DEFAULT 0,
  joined_date date DEFAULT CURRENT_DATE,
  status text DEFAULT 'Available'::text,
  created_at timestamp with time zone NOT NULL DEFAULT timezone('utc'::text, now()),
  CONSTRAINT staff_pkey PRIMARY KEY (id)
);
CREATE TABLE public.staff_roles (
  role_name text NOT NULL,
  CONSTRAINT staff_roles_pkey PRIMARY KEY (role_name)
);
CREATE TABLE public.supplier_purchases (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  supplier_id bigint,
  item_name text,
  quantity numeric,
  cost numeric,
  purchase_date date,
  notes text,
  CONSTRAINT supplier_purchases_pkey PRIMARY KEY (id),
  CONSTRAINT supplier_purchases_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id)
);
CREATE TABLE public.suppliers (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name text NOT NULL,
  contact_person text,
  phone text,
  gstin text,
  CONSTRAINT suppliers_pkey PRIMARY KEY (id)
);
CREATE TABLE public.users (
  username text NOT NULL,
  password text NOT NULL,
  recovery_key text NOT NULL,
  CONSTRAINT users_pkey PRIMARY KEY (username)
);
