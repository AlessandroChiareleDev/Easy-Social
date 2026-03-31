--
-- PostgreSQL database dump
--

\restrict 8I5Ss6ZdGtLNQrm316xLwgd7tpiWjp8gqid4dFS5GrWnV643UuZ0cvsHnuyCyIB

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
-- Name: analise_natureza; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analise_natureza (
    id integer NOT NULL,
    upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    natureza_anterior text,
    natureza_nova text,
    usuario_correcao character varying(255),
    data_correcao timestamp without time zone,
    col_k character varying(255),
    col_l character varying(255),
    col_m character varying(255),
    col_n character varying(255),
    col_o character varying(255),
    col_p character varying(255),
    col_q character varying(255),
    col_r character varying(255),
    col_s character varying(255),
    col_t character varying(255),
    col_u character varying(255),
    col_v character varying(255),
    col_w character varying(255),
    col_x character varying(255),
    col_y character varying(255),
    col_z character varying(255),
    col_aa character varying(255),
    col_ab character varying(255),
    col_ac character varying(255),
    col_ad character varying(255),
    col_ae character varying(255),
    col_af character varying(255),
    col_ag character varying(255),
    col_ah character varying(255),
    col_ai character varying(255),
    col_aj character varying(255),
    col_ak character varying(255),
    col_al character varying(255),
    col_am character varying(255),
    col_an character varying(255),
    col_ao character varying(255),
    col_ap character varying(255),
    col_aq character varying(255),
    col_ar character varying(255),
    col_as character varying(255),
    col_at character varying(255),
    col_au character varying(255),
    col_av character varying(255),
    col_aw character varying(255),
    col_ax character varying(255),
    col_ay character varying(255),
    col_az character varying(255),
    col_ba character varying(255),
    col_bb character varying(255)
);


--
-- Name: analise_natureza_certo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analise_natureza_certo (
    id integer,
    upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    raw_data jsonb,
    created_at timestamp without time zone,
    natureza_anterior text,
    natureza_nova text,
    usuario_correcao character varying(255),
    data_correcao timestamp without time zone,
    col_k character varying(255),
    col_l character varying(255),
    col_m character varying(255),
    col_n character varying(255),
    col_o character varying(255),
    col_p character varying(255),
    col_q character varying(255),
    col_r character varying(255),
    col_s character varying(255),
    col_t character varying(255),
    col_u character varying(255),
    col_v character varying(255),
    col_w character varying(255),
    col_x character varying(255),
    col_y character varying(255),
    col_z character varying(255),
    col_aa character varying(255),
    col_ab character varying(255),
    col_ac character varying(255),
    col_ad character varying(255),
    col_ae character varying(255),
    col_af character varying(255),
    col_ag character varying(255),
    col_ah character varying(255),
    col_ai character varying(255),
    col_aj character varying(255),
    col_ak character varying(255),
    col_al character varying(255),
    col_am character varying(255),
    col_an character varying(255),
    col_ao character varying(255),
    col_ap character varying(255),
    col_aq character varying(255),
    col_ar character varying(255),
    col_as character varying(255),
    col_at character varying(255),
    col_au character varying(255),
    col_av character varying(255),
    col_aw character varying(255),
    col_ax character varying(255),
    col_ay character varying(255),
    col_az character varying(255),
    col_ba character varying(255),
    col_bb character varying(255)
);


--
-- Name: analise_natureza_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.analise_natureza_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: analise_natureza_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.analise_natureza_id_seq OWNED BY public.analise_natureza.id;


--
-- Name: auditoria_naturezas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auditoria_naturezas (
    id integer NOT NULL,
    analise_natureza_id integer,
    codigoevento character varying(255),
    natureza_anterior text,
    natureza_nova text,
    usuario character varying(255) DEFAULT 'sistema'::character varying,
    data_alteracao timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    motivo text
);


--
-- Name: auditoria_naturezas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auditoria_naturezas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auditoria_naturezas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auditoria_naturezas_id_seq OWNED BY public.auditoria_naturezas.id;


--
-- Name: base_ficha_financeira; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.base_ficha_financeira (
    id integer NOT NULL,
    upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    col_k text,
    col_l text,
    col_m text,
    col_n text,
    col_o text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: base_ficha_financeira_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.base_ficha_financeira_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: base_ficha_financeira_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.base_ficha_financeira_id_seq OWNED BY public.base_ficha_financeira.id;


--
-- Name: certificados_a1; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.certificados_a1 (
    id integer NOT NULL,
    cnpj character varying(14) NOT NULL,
    titular character varying(255),
    emissor character varying(255),
    numero_serie character varying(100),
    validade_inicio timestamp without time zone,
    validade_fim timestamp without time zone,
    arquivo_path character varying(500) NOT NULL,
    senha_encrypted text NOT NULL,
    ativo boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: certificados_a1_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.certificados_a1_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: certificados_a1_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.certificados_a1_id_seq OWNED BY public.certificados_a1.id;


--
-- Name: config_esocial; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.config_esocial (
    id integer NOT NULL,
    cnpj character varying(20) NOT NULL,
    ini_valid_padrao character varying(10),
    auto_detected boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: config_esocial_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.config_esocial_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: config_esocial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.config_esocial_id_seq OWNED BY public.config_esocial.id;


--
-- Name: correcoes_staging; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.correcoes_staging (
    id integer NOT NULL,
    analise_natureza_id integer NOT NULL,
    codigoevento character varying(20) NOT NULL,
    nome_evento character varying(500),
    natureza_anterior character varying(500),
    natureza_nova_codigo character varying(20) NOT NULL,
    natureza_nova_nome character varying(500) NOT NULL,
    motivo text DEFAULT ''::text,
    usuario_id integer,
    usuario_nome character varying(200) DEFAULT 'sistema'::character varying,
    status character varying(20) DEFAULT 'pendente'::character varying,
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    aplicado_em timestamp without time zone
);


--
-- Name: correcoes_staging_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.correcoes_staging_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: correcoes_staging_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.correcoes_staging_id_seq OWNED BY public.correcoes_staging.id;


--
-- Name: cruzamento_eb; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cruzamento_eb (
    id integer NOT NULL,
    cod_rubrica character varying(20) NOT NULL,
    descricao text NOT NULL,
    cod_natureza text,
    incid_inss character varying(10),
    incid_irrf character varying(10),
    incid_fgts character varying(10),
    analise text,
    incid_base_legal_inss text,
    incid_base_legal_irrf text,
    incid_base_legal_fgts text,
    importado_em timestamp without time zone DEFAULT now(),
    corrigido boolean DEFAULT false,
    corrigido_em timestamp without time zone,
    envio_status character varying(20) DEFAULT 'pendente'::character varying,
    ini_valid_esocial character varying(10)
);


--
-- Name: cruzamento_eb_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cruzamento_eb_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cruzamento_eb_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cruzamento_eb_id_seq OWNED BY public.cruzamento_eb.id;


--
-- Name: cruzamento_resultado; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cruzamento_resultado (
    id integer NOT NULL,
    cruzamento_upload_id integer,
    codigo text,
    nome_evento text,
    natureza_esocial text,
    cod_fgts text,
    cod_inss text,
    cod_irrf text,
    row_number integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: cruzamento_resultado_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cruzamento_resultado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cruzamento_resultado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cruzamento_resultado_id_seq OWNED BY public.cruzamento_resultado.id;


--
-- Name: cruzamento_tabela_a; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cruzamento_tabela_a (
    id integer NOT NULL,
    cruzamento_upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    col_k text,
    col_l text,
    col_m text,
    col_n text,
    col_o text,
    col_p text,
    col_q text,
    col_r text,
    col_s text,
    col_t text,
    col_u text,
    col_v text,
    col_w text,
    col_x text,
    col_y text,
    col_z text,
    col_aa text,
    col_ab text,
    col_ac text,
    col_ad text,
    col_ae text,
    col_af text,
    col_ag text,
    col_ah text,
    col_ai text,
    col_aj text,
    col_ak text,
    col_al text,
    col_am text,
    col_an text,
    col_ao text,
    col_ap text,
    col_aq text,
    col_ar text,
    col_as text,
    col_at text,
    col_au text,
    col_av text,
    col_aw text,
    col_ax text,
    col_ay text,
    col_az text,
    col_ba text,
    col_bb text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: cruzamento_tabela_a_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cruzamento_tabela_a_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cruzamento_tabela_a_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cruzamento_tabela_a_id_seq OWNED BY public.cruzamento_tabela_a.id;


--
-- Name: cruzamento_tabela_b; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cruzamento_tabela_b (
    id integer NOT NULL,
    cruzamento_upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    col_k text,
    col_l text,
    col_m text,
    col_n text,
    col_o text,
    col_p text,
    col_q text,
    col_r text,
    col_s text,
    col_t text,
    col_u text,
    col_v text,
    col_w text,
    col_x text,
    col_y text,
    col_z text,
    col_aa text,
    col_ab text,
    col_ac text,
    col_ad text,
    col_ae text,
    col_af text,
    col_ag text,
    col_ah text,
    col_ai text,
    col_aj text,
    col_ak text,
    col_al text,
    col_am text,
    col_an text,
    col_ao text,
    col_ap text,
    col_aq text,
    col_ar text,
    col_as text,
    col_at text,
    col_au text,
    col_av text,
    col_aw text,
    col_ax text,
    col_ay text,
    col_az text,
    col_ba text,
    col_bb text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: cruzamento_tabela_b_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cruzamento_tabela_b_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cruzamento_tabela_b_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cruzamento_tabela_b_id_seq OWNED BY public.cruzamento_tabela_b.id;


--
-- Name: cruzamento_uploads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cruzamento_uploads (
    id integer NOT NULL,
    filename character varying(500) NOT NULL,
    original_name character varying(500) NOT NULL,
    file_size bigint NOT NULL,
    upload_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sheet_count integer DEFAULT 0,
    sheet_names text[]
);


--
-- Name: cruzamento_uploads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cruzamento_uploads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cruzamento_uploads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cruzamento_uploads_id_seq OWNED BY public.cruzamento_uploads.id;


--
-- Name: dinamica; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dinamica (
    id integer NOT NULL,
    upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    col_k character varying(255),
    col_l character varying(255),
    col_m character varying(255),
    col_n character varying(255),
    col_o character varying(255),
    col_p character varying(255),
    col_q character varying(255),
    col_r character varying(255),
    col_s character varying(255),
    col_t character varying(255),
    col_u character varying(255),
    col_v character varying(255),
    col_w character varying(255),
    col_x character varying(255),
    col_y character varying(255),
    col_z character varying(255),
    col_aa character varying(255),
    col_ab character varying(255),
    col_ac character varying(255),
    col_ad character varying(255),
    col_ae character varying(255),
    col_af character varying(255),
    col_ag character varying(255),
    col_ah character varying(255),
    col_ai character varying(255),
    col_aj character varying(255),
    col_ak character varying(255),
    col_al character varying(255),
    col_am character varying(255),
    col_an character varying(255),
    col_ao character varying(255),
    col_ap character varying(255),
    col_aq character varying(255),
    col_ar character varying(255),
    col_as character varying(255),
    col_at character varying(255),
    col_au character varying(255),
    col_av character varying(255),
    col_aw character varying(255),
    col_ax character varying(255),
    col_ay character varying(255),
    col_az character varying(255),
    col_ba character varying(255),
    col_bb character varying(255)
);


--
-- Name: dinamica_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dinamica_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dinamica_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dinamica_id_seq OWNED BY public.dinamica.id;


--
-- Name: eb_skills_base_legal; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.eb_skills_base_legal (
    id integer NOT NULL,
    upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: eb_skills_base_legal_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.eb_skills_base_legal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: eb_skills_base_legal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.eb_skills_base_legal_id_seq OWNED BY public.eb_skills_base_legal.id;


--
-- Name: esocial_depara; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.esocial_depara (
    id integer NOT NULL,
    cod_rubrica text NOT NULL,
    campo text NOT NULL,
    valor_anterior text,
    valor_novo text NOT NULL,
    nome_rubrica text,
    regra text DEFAULT 'manual'::text,
    status character varying(20) DEFAULT 'pendente'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    aplicado_em timestamp without time zone
);


--
-- Name: esocial_depara_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.esocial_depara_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: esocial_depara_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.esocial_depara_id_seq OWNED BY public.esocial_depara.id;


--
-- Name: esocial_envios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.esocial_envios (
    id integer NOT NULL,
    tipo_evento character varying(10) DEFAULT 'S-1010'::character varying NOT NULL,
    modo character varying(20) DEFAULT 'alteracao'::character varying NOT NULL,
    status character varying(30) DEFAULT 'enviado'::character varying NOT NULL,
    protocolo_envio character varying(100),
    codigo_resposta character varying(10),
    descricao_resposta text,
    total_eventos integer DEFAULT 0,
    rubrica_ids jsonb,
    xml_retorno text,
    ocorrencias jsonb,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    ambiente character varying(2) DEFAULT '2'::character varying NOT NULL,
    ini_valid character varying(10),
    rubrica_detalhes jsonb,
    xml_enviado text,
    recibo_consulta jsonb
);


--
-- Name: esocial_envios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.esocial_envios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: esocial_envios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.esocial_envios_id_seq OWNED BY public.esocial_envios.id;


--
-- Name: esocial_tabela3_natureza; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.esocial_tabela3_natureza (
    codigo integer NOT NULL,
    nome character varying(200) NOT NULL,
    dt_inicio date NOT NULL,
    dt_fim date,
    descricao text,
    versao integer DEFAULT 17
);


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
-- Name: planilha_1; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.planilha_1 (
    id integer NOT NULL,
    upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: planilha_1_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.planilha_1_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: planilha_1_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.planilha_1_id_seq OWNED BY public.planilha_1.id;


--
-- Name: rubrica_corrections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rubrica_corrections (
    id integer NOT NULL,
    tabela_eb_id integer,
    cod_rubrica text NOT NULL,
    descricao text,
    inss_antes text,
    irrf_antes text,
    fgts_antes text,
    inss_correto text,
    irrf_correto text,
    fgts_correto text,
    status character varying(50) DEFAULT 'pendente'::character varying,
    corrigido_em timestamp without time zone,
    observacao text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: rubrica_corrections_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rubrica_corrections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rubrica_corrections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rubrica_corrections_id_seq OWNED BY public.rubrica_corrections.id;


--
-- Name: senha_certificado_salva; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.senha_certificado_salva (
    id integer NOT NULL,
    senha_encrypted text NOT NULL,
    saved_at timestamp without time zone DEFAULT now(),
    expires_at timestamp without time zone NOT NULL
);


--
-- Name: senha_certificado_salva_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.senha_certificado_salva_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: senha_certificado_salva_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.senha_certificado_salva_id_seq OWNED BY public.senha_certificado_salva.id;


--
-- Name: tabela3_esocial_oficial; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tabela3_esocial_oficial (
    id integer NOT NULL,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: tabela3_esocial_oficial_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tabela3_esocial_oficial_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tabela3_esocial_oficial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tabela3_esocial_oficial_id_seq OWNED BY public.tabela3_esocial_oficial.id;


--
-- Name: tabela_cruzamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tabela_cruzamento (
    id integer NOT NULL,
    upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    col_k text,
    col_l text,
    col_m text,
    col_n text,
    col_o text,
    col_p text,
    col_q text,
    col_r text,
    col_s text,
    col_t text,
    col_u text,
    col_v text,
    col_w text,
    col_x text,
    col_y text,
    col_z text,
    col_aa text,
    col_ab text,
    col_ac text,
    col_ad text,
    col_ae text,
    col_af text,
    col_ag text,
    col_ah text,
    col_ai text,
    col_aj text,
    col_ak text,
    col_al text,
    col_am text,
    col_an text,
    col_ao text,
    col_ap text,
    col_aq text,
    col_ar text,
    col_as text,
    col_at text,
    col_au text,
    col_av text,
    col_aw text,
    col_ax text,
    col_ay text,
    col_az text,
    col_ba text,
    col_bb text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: tabela_cruzamento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tabela_cruzamento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tabela_cruzamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tabela_cruzamento_id_seq OWNED BY public.tabela_cruzamento.id;


--
-- Name: tabela_eb; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tabela_eb (
    id integer NOT NULL,
    upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    col_k character varying(255),
    col_l character varying(255),
    col_m character varying(255),
    col_n character varying(255),
    col_o character varying(255),
    col_p character varying(255),
    col_q character varying(255),
    col_r character varying(255),
    col_s character varying(255),
    col_t character varying(255),
    col_u character varying(255),
    col_v character varying(255),
    col_w character varying(255),
    col_x character varying(255),
    col_y character varying(255),
    col_z character varying(255),
    col_aa character varying(255),
    col_ab character varying(255),
    col_ac character varying(255),
    col_ad character varying(255),
    col_ae character varying(255),
    col_af character varying(255),
    col_ag character varying(255),
    col_ah character varying(255),
    col_ai character varying(255),
    col_aj character varying(255),
    col_ak character varying(255),
    col_al character varying(255),
    col_am character varying(255),
    col_an character varying(255),
    col_ao character varying(255),
    col_ap character varying(255),
    col_aq character varying(255),
    col_ar character varying(255),
    col_as character varying(255),
    col_at character varying(255),
    col_au character varying(255),
    col_av character varying(255),
    col_aw character varying(255),
    col_ax character varying(255),
    col_ay character varying(255),
    col_az character varying(255),
    col_ba character varying(255),
    col_bb character varying(255)
);


--
-- Name: tabela_eb_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tabela_eb_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tabela_eb_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tabela_eb_id_seq OWNED BY public.tabela_eb.id;


--
-- Name: tabela_eventos_gl; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tabela_eventos_gl (
    id integer NOT NULL,
    upload_id integer,
    row_number integer,
    col_a text,
    col_b text,
    col_c text,
    col_d text,
    col_e text,
    col_f text,
    col_g text,
    col_h text,
    col_i text,
    col_j text,
    raw_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    col_k character varying(255),
    col_l character varying(255),
    col_m character varying(255),
    col_n character varying(255),
    col_o character varying(255),
    col_p character varying(255),
    col_q character varying(255),
    col_r character varying(255),
    col_s character varying(255),
    col_t character varying(255),
    col_u character varying(255),
    col_v character varying(255),
    col_w character varying(255),
    col_x character varying(255),
    col_y character varying(255),
    col_z character varying(255),
    col_aa character varying(255),
    col_ab character varying(255),
    col_ac character varying(255),
    col_ad character varying(255),
    col_ae character varying(255),
    col_af character varying(255),
    col_ag character varying(255),
    col_ah character varying(255),
    col_ai character varying(255),
    col_aj character varying(255),
    col_ak character varying(255),
    col_al character varying(255),
    col_am character varying(255),
    col_an character varying(255),
    col_ao character varying(255),
    col_ap character varying(255),
    col_aq character varying(255),
    col_ar character varying(255),
    col_as character varying(255),
    col_at character varying(255),
    col_au character varying(255),
    col_av character varying(255),
    col_aw character varying(255),
    col_ax character varying(255),
    col_ay character varying(255),
    col_az character varying(255),
    col_ba character varying(255),
    col_bb character varying(255)
);


--
-- Name: tabela_eventos_gl_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tabela_eventos_gl_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tabela_eventos_gl_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tabela_eventos_gl_id_seq OWNED BY public.tabela_eventos_gl.id;


--
-- Name: uploads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.uploads (
    id integer NOT NULL,
    file_name character varying(500) NOT NULL,
    original_name character varying(500),
    file_size bigint NOT NULL,
    upload_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(50) DEFAULT 'pendente'::character varying,
    sheets_processed integer DEFAULT 0,
    analysis_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: uploads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.uploads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: uploads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.uploads_id_seq OWNED BY public.uploads.id;


--
-- Name: analise_natureza id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analise_natureza ALTER COLUMN id SET DEFAULT nextval('public.analise_natureza_id_seq'::regclass);


--
-- Name: auditoria_naturezas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria_naturezas ALTER COLUMN id SET DEFAULT nextval('public.auditoria_naturezas_id_seq'::regclass);


--
-- Name: base_ficha_financeira id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.base_ficha_financeira ALTER COLUMN id SET DEFAULT nextval('public.base_ficha_financeira_id_seq'::regclass);


--
-- Name: certificados_a1 id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificados_a1 ALTER COLUMN id SET DEFAULT nextval('public.certificados_a1_id_seq'::regclass);


--
-- Name: config_esocial id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_esocial ALTER COLUMN id SET DEFAULT nextval('public.config_esocial_id_seq'::regclass);


--
-- Name: correcoes_staging id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correcoes_staging ALTER COLUMN id SET DEFAULT nextval('public.correcoes_staging_id_seq'::regclass);


--
-- Name: cruzamento_eb id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_eb ALTER COLUMN id SET DEFAULT nextval('public.cruzamento_eb_id_seq'::regclass);


--
-- Name: cruzamento_resultado id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_resultado ALTER COLUMN id SET DEFAULT nextval('public.cruzamento_resultado_id_seq'::regclass);


--
-- Name: cruzamento_tabela_a id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_tabela_a ALTER COLUMN id SET DEFAULT nextval('public.cruzamento_tabela_a_id_seq'::regclass);


--
-- Name: cruzamento_tabela_b id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_tabela_b ALTER COLUMN id SET DEFAULT nextval('public.cruzamento_tabela_b_id_seq'::regclass);


--
-- Name: cruzamento_uploads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_uploads ALTER COLUMN id SET DEFAULT nextval('public.cruzamento_uploads_id_seq'::regclass);


--
-- Name: dinamica id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dinamica ALTER COLUMN id SET DEFAULT nextval('public.dinamica_id_seq'::regclass);


--
-- Name: eb_skills_base_legal id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eb_skills_base_legal ALTER COLUMN id SET DEFAULT nextval('public.eb_skills_base_legal_id_seq'::regclass);


--
-- Name: esocial_depara id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.esocial_depara ALTER COLUMN id SET DEFAULT nextval('public.esocial_depara_id_seq'::regclass);


--
-- Name: esocial_envios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.esocial_envios ALTER COLUMN id SET DEFAULT nextval('public.esocial_envios_id_seq'::regclass);


--
-- Name: naturezas_esocial id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.naturezas_esocial ALTER COLUMN id SET DEFAULT nextval('public.naturezas_esocial_id_seq'::regclass);


--
-- Name: planilha_1 id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planilha_1 ALTER COLUMN id SET DEFAULT nextval('public.planilha_1_id_seq'::regclass);


--
-- Name: rubrica_corrections id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rubrica_corrections ALTER COLUMN id SET DEFAULT nextval('public.rubrica_corrections_id_seq'::regclass);


--
-- Name: senha_certificado_salva id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.senha_certificado_salva ALTER COLUMN id SET DEFAULT nextval('public.senha_certificado_salva_id_seq'::regclass);


--
-- Name: tabela3_esocial_oficial id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela3_esocial_oficial ALTER COLUMN id SET DEFAULT nextval('public.tabela3_esocial_oficial_id_seq'::regclass);


--
-- Name: tabela_cruzamento id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela_cruzamento ALTER COLUMN id SET DEFAULT nextval('public.tabela_cruzamento_id_seq'::regclass);


--
-- Name: tabela_eb id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela_eb ALTER COLUMN id SET DEFAULT nextval('public.tabela_eb_id_seq'::regclass);


--
-- Name: tabela_eventos_gl id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela_eventos_gl ALTER COLUMN id SET DEFAULT nextval('public.tabela_eventos_gl_id_seq'::regclass);


--
-- Name: uploads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uploads ALTER COLUMN id SET DEFAULT nextval('public.uploads_id_seq'::regclass);


--
-- Name: analise_natureza analise_natureza_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analise_natureza
    ADD CONSTRAINT analise_natureza_pkey PRIMARY KEY (id);


--
-- Name: auditoria_naturezas auditoria_naturezas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria_naturezas
    ADD CONSTRAINT auditoria_naturezas_pkey PRIMARY KEY (id);


--
-- Name: base_ficha_financeira base_ficha_financeira_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.base_ficha_financeira
    ADD CONSTRAINT base_ficha_financeira_pkey PRIMARY KEY (id);


--
-- Name: certificados_a1 certificados_a1_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificados_a1
    ADD CONSTRAINT certificados_a1_pkey PRIMARY KEY (id);


--
-- Name: config_esocial config_esocial_cnpj_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_esocial
    ADD CONSTRAINT config_esocial_cnpj_key UNIQUE (cnpj);


--
-- Name: config_esocial config_esocial_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.config_esocial
    ADD CONSTRAINT config_esocial_pkey PRIMARY KEY (id);


--
-- Name: correcoes_staging correcoes_staging_analise_natureza_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correcoes_staging
    ADD CONSTRAINT correcoes_staging_analise_natureza_id_key UNIQUE (analise_natureza_id);


--
-- Name: correcoes_staging correcoes_staging_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correcoes_staging
    ADD CONSTRAINT correcoes_staging_pkey PRIMARY KEY (id);


--
-- Name: cruzamento_eb cruzamento_eb_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_eb
    ADD CONSTRAINT cruzamento_eb_pkey PRIMARY KEY (id);


--
-- Name: cruzamento_resultado cruzamento_resultado_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_resultado
    ADD CONSTRAINT cruzamento_resultado_pkey PRIMARY KEY (id);


--
-- Name: cruzamento_tabela_a cruzamento_tabela_a_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_tabela_a
    ADD CONSTRAINT cruzamento_tabela_a_pkey PRIMARY KEY (id);


--
-- Name: cruzamento_tabela_b cruzamento_tabela_b_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_tabela_b
    ADD CONSTRAINT cruzamento_tabela_b_pkey PRIMARY KEY (id);


--
-- Name: cruzamento_uploads cruzamento_uploads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_uploads
    ADD CONSTRAINT cruzamento_uploads_pkey PRIMARY KEY (id);


--
-- Name: dinamica dinamica_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dinamica
    ADD CONSTRAINT dinamica_pkey PRIMARY KEY (id);


--
-- Name: eb_skills_base_legal eb_skills_base_legal_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eb_skills_base_legal
    ADD CONSTRAINT eb_skills_base_legal_pkey PRIMARY KEY (id);


--
-- Name: esocial_depara esocial_depara_cod_rubrica_campo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.esocial_depara
    ADD CONSTRAINT esocial_depara_cod_rubrica_campo_key UNIQUE (cod_rubrica, campo);


--
-- Name: esocial_depara esocial_depara_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.esocial_depara
    ADD CONSTRAINT esocial_depara_pkey PRIMARY KEY (id);


--
-- Name: esocial_envios esocial_envios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.esocial_envios
    ADD CONSTRAINT esocial_envios_pkey PRIMARY KEY (id);


--
-- Name: esocial_tabela3_natureza esocial_tabela3_natureza_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.esocial_tabela3_natureza
    ADD CONSTRAINT esocial_tabela3_natureza_pkey PRIMARY KEY (codigo);


--
-- Name: naturezas_esocial naturezas_esocial_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.naturezas_esocial
    ADD CONSTRAINT naturezas_esocial_pkey PRIMARY KEY (id);


--
-- Name: planilha_1 planilha_1_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planilha_1
    ADD CONSTRAINT planilha_1_pkey PRIMARY KEY (id);


--
-- Name: rubrica_corrections rubrica_corrections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rubrica_corrections
    ADD CONSTRAINT rubrica_corrections_pkey PRIMARY KEY (id);


--
-- Name: senha_certificado_salva senha_certificado_salva_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.senha_certificado_salva
    ADD CONSTRAINT senha_certificado_salva_pkey PRIMARY KEY (id);


--
-- Name: tabela3_esocial_oficial tabela3_esocial_oficial_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela3_esocial_oficial
    ADD CONSTRAINT tabela3_esocial_oficial_pkey PRIMARY KEY (id);


--
-- Name: tabela_cruzamento tabela_cruzamento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela_cruzamento
    ADD CONSTRAINT tabela_cruzamento_pkey PRIMARY KEY (id);


--
-- Name: tabela_eb tabela_eb_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela_eb
    ADD CONSTRAINT tabela_eb_pkey PRIMARY KEY (id);


--
-- Name: tabela_eventos_gl tabela_eventos_gl_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela_eventos_gl
    ADD CONSTRAINT tabela_eventos_gl_pkey PRIMARY KEY (id);


--
-- Name: uploads uploads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uploads
    ADD CONSTRAINT uploads_pkey PRIMARY KEY (id);


--
-- Name: idx_analise_natureza_upload; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_analise_natureza_upload ON public.analise_natureza USING btree (upload_id);


--
-- Name: idx_auditoria_naturezas_an; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_auditoria_naturezas_an ON public.auditoria_naturezas USING btree (analise_natureza_id);


--
-- Name: idx_base_ficha_upload; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_base_ficha_upload ON public.base_ficha_financeira USING btree (upload_id);


--
-- Name: idx_dinamica_upload; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dinamica_upload ON public.dinamica USING btree (upload_id);


--
-- Name: idx_eventos_gl_upload; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_eventos_gl_upload ON public.tabela_eventos_gl USING btree (upload_id);


--
-- Name: idx_naturezas_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_naturezas_codigo ON public.naturezas_esocial USING btree (codigo);


--
-- Name: idx_planilha1_upload; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_planilha1_upload ON public.planilha_1 USING btree (upload_id);


--
-- Name: idx_planilha_1_upload; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_planilha_1_upload ON public.planilha_1 USING btree (upload_id);


--
-- Name: idx_rubrica_corrections_eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rubrica_corrections_eb ON public.rubrica_corrections USING btree (tabela_eb_id);


--
-- Name: idx_rubrica_corrections_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rubrica_corrections_status ON public.rubrica_corrections USING btree (status);


--
-- Name: idx_tabela_eb_upload; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tabela_eb_upload ON public.tabela_eb USING btree (upload_id);


--
-- Name: idx_uploads_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_uploads_status ON public.uploads USING btree (status);


--
-- Name: analise_natureza analise_natureza_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analise_natureza
    ADD CONSTRAINT analise_natureza_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES public.uploads(id) ON DELETE CASCADE;


--
-- Name: auditoria_naturezas auditoria_naturezas_analise_natureza_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria_naturezas
    ADD CONSTRAINT auditoria_naturezas_analise_natureza_id_fkey FOREIGN KEY (analise_natureza_id) REFERENCES public.analise_natureza(id);


--
-- Name: base_ficha_financeira base_ficha_financeira_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.base_ficha_financeira
    ADD CONSTRAINT base_ficha_financeira_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES public.uploads(id) ON DELETE CASCADE;


--
-- Name: correcoes_staging correcoes_staging_analise_natureza_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.correcoes_staging
    ADD CONSTRAINT correcoes_staging_analise_natureza_id_fkey FOREIGN KEY (analise_natureza_id) REFERENCES public.analise_natureza(id);


--
-- Name: cruzamento_resultado cruzamento_resultado_cruzamento_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_resultado
    ADD CONSTRAINT cruzamento_resultado_cruzamento_upload_id_fkey FOREIGN KEY (cruzamento_upload_id) REFERENCES public.cruzamento_uploads(id) ON DELETE CASCADE;


--
-- Name: cruzamento_tabela_a cruzamento_tabela_a_cruzamento_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_tabela_a
    ADD CONSTRAINT cruzamento_tabela_a_cruzamento_upload_id_fkey FOREIGN KEY (cruzamento_upload_id) REFERENCES public.cruzamento_uploads(id) ON DELETE CASCADE;


--
-- Name: cruzamento_tabela_b cruzamento_tabela_b_cruzamento_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cruzamento_tabela_b
    ADD CONSTRAINT cruzamento_tabela_b_cruzamento_upload_id_fkey FOREIGN KEY (cruzamento_upload_id) REFERENCES public.cruzamento_uploads(id) ON DELETE CASCADE;


--
-- Name: dinamica dinamica_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dinamica
    ADD CONSTRAINT dinamica_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES public.uploads(id) ON DELETE CASCADE;


--
-- Name: planilha_1 planilha_1_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planilha_1
    ADD CONSTRAINT planilha_1_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES public.uploads(id) ON DELETE CASCADE;


--
-- Name: rubrica_corrections rubrica_corrections_tabela_eb_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rubrica_corrections
    ADD CONSTRAINT rubrica_corrections_tabela_eb_id_fkey FOREIGN KEY (tabela_eb_id) REFERENCES public.tabela_eb(id);


--
-- Name: tabela_eb tabela_eb_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela_eb
    ADD CONSTRAINT tabela_eb_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES public.uploads(id) ON DELETE CASCADE;


--
-- Name: tabela_eventos_gl tabela_eventos_gl_upload_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tabela_eventos_gl
    ADD CONSTRAINT tabela_eventos_gl_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES public.uploads(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 8I5Ss6ZdGtLNQrm316xLwgd7tpiWjp8gqid4dFS5GrWnV643UuZ0cvsHnuyCyIB

