--
-- PostgreSQL database dump
--

\restrict ugOXxgrh3a4vQgvoDX3TBRfFQfXFO2wXEcCspFvoZdWUh3g6CBdJ2dUXBA7I6td

-- Dumped from database version 16.12
-- Dumped by pg_dump version 16.12

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: empresas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.empresas (
    id integer NOT NULL,
    nome character varying(255) NOT NULL,
    cnpj character varying(18),
    db_name character varying(100) NOT NULL,
    db_host character varying(255) DEFAULT 'localhost'::character varying,
    db_port integer DEFAULT 5432,
    ativo boolean DEFAULT true,
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: empresas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.empresas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: empresas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.empresas_id_seq OWNED BY public.empresas.id;


--
-- Name: naturezas_esocial; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.naturezas_esocial (
    id integer NOT NULL,
    codigo character varying(10) NOT NULL,
    nome character varying(500) NOT NULL,
    descricao text,
    data_inicio date,
    data_fim date,
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: naturezas_esocial_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.naturezas_esocial_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: naturezas_esocial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.naturezas_esocial_id_seq OWNED BY public.naturezas_esocial.id;


--
-- Name: usuario_empresa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario_empresa (
    id integer NOT NULL,
    usuario_id integer,
    empresa_id integer,
    role_emp character varying(20) DEFAULT 'operador'::character varying,
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT usuario_empresa_role_emp_check CHECK (((role_emp)::text = ANY ((ARRAY['admin'::character varying, 'operador'::character varying])::text[])))
);


--
-- Name: usuario_empresa_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuario_empresa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuario_empresa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuario_empresa_id_seq OWNED BY public.usuario_empresa.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    nome character varying(255) NOT NULL,
    senha_hash character varying(255) NOT NULL,
    role character varying(20) DEFAULT 'operador'::character varying,
    ativo boolean DEFAULT true,
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    atualizado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    username character varying(100),
    CONSTRAINT usuarios_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'operador'::character varying])::text[])))
);


--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: empresas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresas ALTER COLUMN id SET DEFAULT nextval('public.empresas_id_seq'::regclass);


--
-- Name: naturezas_esocial id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.naturezas_esocial ALTER COLUMN id SET DEFAULT nextval('public.naturezas_esocial_id_seq'::regclass);


--
-- Name: usuario_empresa id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_empresa ALTER COLUMN id SET DEFAULT nextval('public.usuario_empresa_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: empresas empresas_cnpj_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_cnpj_key UNIQUE (cnpj);


--
-- Name: empresas empresas_db_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_db_name_key UNIQUE (db_name);


--
-- Name: empresas empresas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresas
    ADD CONSTRAINT empresas_pkey PRIMARY KEY (id);


--
-- Name: naturezas_esocial naturezas_esocial_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.naturezas_esocial
    ADD CONSTRAINT naturezas_esocial_codigo_key UNIQUE (codigo);


--
-- Name: naturezas_esocial naturezas_esocial_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.naturezas_esocial
    ADD CONSTRAINT naturezas_esocial_pkey PRIMARY KEY (id);


--
-- Name: usuario_empresa usuario_empresa_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_empresa
    ADD CONSTRAINT usuario_empresa_pkey PRIMARY KEY (id);


--
-- Name: usuario_empresa usuario_empresa_usuario_id_empresa_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_empresa
    ADD CONSTRAINT usuario_empresa_usuario_id_empresa_id_key UNIQUE (usuario_id, empresa_id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_username_key UNIQUE (username);


--
-- Name: usuario_empresa usuario_empresa_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_empresa
    ADD CONSTRAINT usuario_empresa_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE;


--
-- Name: usuario_empresa usuario_empresa_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_empresa
    ADD CONSTRAINT usuario_empresa_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict ugOXxgrh3a4vQgvoDX3TBRfFQfXFO2wXEcCspFvoZdWUh3g6CBdJ2dUXBA7I6td

