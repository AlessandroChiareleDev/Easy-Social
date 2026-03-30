--
-- PostgreSQL database dump
--

\restrict sT8hakOYuTfKNj6Yfxsb7h9Q2wpuscE5cxwxNrKfsXvguWT4TWOrVpo0EbIhZst

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

--
-- Data for Name: esocial_depara; Type: TABLE DATA; Schema: public; Owner: easy_social_user
--

COPY public.esocial_depara (id, cod_rubrica, campo, valor_anterior, valor_novo, nome_rubrica, regra, status, created_at, aplicado_em) FROM stdin;
1	1	tpRubr	Vencimento	1	HORAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2	10	tpRubr	Vencimento	1	GRATIFICAÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
3	100	tpRubr	Vencimento	1	HORAS EXTRAS 20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
4	1000	tpRubr	Vencimento	1	ADIC. NOTURNO C/20% - (HORA EXTRA 100%)	automatico	pendente	2026-03-28 03:16:48.023178	\N
5	1001	tpRubr	Vencimento	1	PARCELAMENTO 4	automatico	pendente	2026-03-28 03:16:48.023178	\N
6	1002	tpRubr	Vencimento	1	PARCELAMENTO 5	automatico	pendente	2026-03-28 03:16:48.023178	\N
7	1003	tpRubr	Vencimento	1	PARCELAMENTO 6	automatico	pendente	2026-03-28 03:16:48.023178	\N
8	1004	tpRubr	Desconto	2	DESC. CONVENIO E CONSULTAS - SIEMACO	automatico	pendente	2026-03-28 03:16:48.023178	\N
9	1005	tpRubr	Vencimento	1	REEMBOLSO DESC. INDEVIDO - HORA EXTRA + DSR	automatico	pendente	2026-03-28 03:16:48.023178	\N
10	1006	tpRubr	Vencimento	1	ADIC. NOTURNO C/20% - (HORA EXTRA 100%) - MES ANTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
11	1007	tpRubr	Desconto	2	DESC. MULTA 40% - REITEGRAÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
12	1008	tpRubr	Vencimento	1	FERIAS INDENIZADAS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
13	1009	tpRubr	Vencimento	1	1/3 FERIAS INDENIZADAS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
14	101	tpRubr	Vencimento	1	HORAS EXTRAS 35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
15	1010	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE SOBRE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
16	1011	tpRubr	Vencimento	1	PARTICIPACAO LUCROS/RESULTADOS - 2023	automatico	pendente	2026-03-28 03:16:48.023178	\N
17	1012	tpRubr	Vencimento	1	PARTICIPACAO LUCROS/RESULTADOS - 2024	automatico	pendente	2026-03-28 03:16:48.023178	\N
18	1013	tpRubr	Vencimento	1	REEMB. DESC. PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
19	1014	tpRubr	Vencimento	1	DIF MEDIAS FERIAS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
20	1015	tpRubr	Vencimento	1	REEMBOLSO DE GRATIFICACAO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
21	1016	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
22	1017	tpRubr	Vencimento	1	REEMB. EXAME TROCA DE FUNCAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
23	1018	tpRubr	Desconto	2	DESC. VALE REFEICAO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
24	1019	tpRubr	Vencimento	1	DIF CCT ABONO PECUNIARIO RODOVIARIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
25	102	tpRubr	Vencimento	1	HORAS EXTRAS 60%	automatico	pendente	2026-03-28 03:16:48.023178	\N
26	1020	tpRubr	Vencimento	1	DIFERENCA CCT - 05/24 a 07/24	automatico	pendente	2026-03-28 03:16:48.023178	\N
27	1021	tpRubr	Desconto	2	DESC. VT DIF CCT - 05/24 a 07/24	automatico	pendente	2026-03-28 03:16:48.023178	\N
28	1022	tpRubr	Vencimento	1	DIF CCT PREMIO TEMPO DE SERVICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
29	1023	tpRubr	Vencimento	1	DIF ADIC. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
30	1024	tpRubr	Vencimento	1	DIF ADIC. FERIAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
31	1025	tpRubr	Vencimento	1	LICENCA GESTANTE POR ABORTO NAO CRIMINOSO	automatico	pendente	2026-03-28 03:16:48.023178	\N
32	1026	tpRubr	Vencimento	1	PAGTO. VT E VA - REF FERIADOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
33	1027	tpRubr	Desconto	2	DESCONTO DE NÃO DEV. DO MATERIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
34	1028	tpRubr	Vencimento	1	DIFERENÇA AJUDA DE CUSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
35	1029	tpRubr	Vencimento	1	ADIC. NOTURNO C/20% - MES ANTERIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
36	103	tpRubr	Vencimento	1	HORAS EXTRAS 44%	automatico	pendente	2026-03-28 03:16:48.023178	\N
37	1030	tpRubr	Vencimento	1	REEMB. ATRASO/FALTA HORAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
38	1031	tpRubr	Vencimento	1	DIF. MULTA POR ATRASO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
39	1032	tpRubr	Vencimento	1	D.S.R (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
40	1033	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
41	1034	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
42	1035	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
43	1036	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
44	1037	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
45	1038	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
46	1039	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
47	104	tpRubr	Vencimento	1	HORAS EXTRAS 45%	automatico	pendente	2026-03-28 03:16:48.023178	\N
48	1040	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
49	1041	tpRubr	Vencimento	1	PAGTO. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
50	1042	tpRubr	Vencimento	1	REEMBOLSO CO PARTICIPACAO A.M.	automatico	pendente	2026-03-28 03:16:48.023178	\N
51	1043	tpRubr	Vencimento	1	FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
52	1044	tpRubr	Vencimento	1	AUXILIO ESPECIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
53	1045	tpRubr	Vencimento	1	D.S.R. S/SALARIO AULA	automatico	pendente	2026-03-28 03:16:48.023178	\N
54	1046	tpRubr	Vencimento	1	ADICIONAL EXTRACLASSE	automatico	pendente	2026-03-28 03:16:48.023178	\N
55	1047	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
56	1048	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
57	1049	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - MARCO	automatico	pendente	2026-03-28 03:16:48.023178	\N
58	105	tpRubr	Vencimento	1	HORAS EXTRAS 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
59	1050	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
60	1051	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
61	1052	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
62	1053	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
63	1054	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
64	1055	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1660	187	codIncPisPasep	0	00	P.L.R.	automatico	pendente	2026-03-28 03:16:48.023178	\N
65	1056	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
66	1057	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
67	1058	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
68	1059	tpRubr	Vencimento	1	HORAS EXTRAS 50% - JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
69	106	tpRubr	Vencimento	1	HORAS EXTRAS 50% - 08/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
70	1060	tpRubr	Vencimento	1	HORAS EXTRAS 50% - FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
71	1061	tpRubr	Vencimento	1	HORAS EXTRAS 50% - MARCO	automatico	pendente	2026-03-28 03:16:48.023178	\N
72	1062	tpRubr	Vencimento	1	HORAS EXTRAS 50% - ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
73	1063	tpRubr	Vencimento	1	HORAS EXTRAS 50% - MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
74	1064	tpRubr	Vencimento	1	HORAS EXTRAS 50% - JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
75	1065	tpRubr	Vencimento	1	HORAS EXTRAS 50% - JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
76	1066	tpRubr	Vencimento	1	HORAS EXTRAS 50% - AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
77	1067	tpRubr	Vencimento	1	HORAS EXTRAS 50% - SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
78	1068	tpRubr	Vencimento	1	HORAS EXTRAS 50% - OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
79	1069	tpRubr	Vencimento	1	HORAS EXTRAS 50% - NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
80	107	tpRubr	Vencimento	1	HORAS EXTRAS 50% - 11/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
81	1070	tpRubr	Vencimento	1	HORAS EXTRAS 50% - DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
82	1071	tpRubr	Vencimento	1	MEDIAS FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
83	1072	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
84	1073	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
85	1074	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - MARCO	automatico	pendente	2026-03-28 03:16:48.023178	\N
86	1075	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
87	1076	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
88	1077	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
89	1078	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
90	1079	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
91	108	tpRubr	Vencimento	1	HORAS EXTRAS 50% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
92	1080	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
93	1081	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
94	1082	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
95	1083	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 - DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
96	1084	tpRubr	Vencimento	1	HORAS EXTRAS 100% - JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
97	1085	tpRubr	Vencimento	1	HORAS EXTRAS 100% - FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
98	1086	tpRubr	Vencimento	1	HORAS EXTRAS 100% - MARÇO	automatico	pendente	2026-03-28 03:16:48.023178	\N
99	1087	tpRubr	Vencimento	1	HORAS EXTRAS 100% ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
100	1088	tpRubr	Vencimento	1	HORAS EXTRAS 100% MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
101	1089	tpRubr	Vencimento	1	HORAS EXTRAS 100% JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
102	109	tpRubr	Vencimento	1	HORAS EXTRAS 50% + ADIC NOT 20	automatico	pendente	2026-03-28 03:16:48.023178	\N
103	1090	tpRubr	Vencimento	1	HORAS EXTRAS 100% JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
104	1091	tpRubr	Vencimento	1	HORAS EXTRAS 100% - AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
105	1092	tpRubr	Vencimento	1	HORAS EXTRAS 100% SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
106	1093	tpRubr	Vencimento	1	HORAS EXTRAS 100% OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
107	1094	tpRubr	Vencimento	1	HORAS EXTRAS 100% NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
108	1095	tpRubr	Vencimento	1	HORAS EXTRAS 100% DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
109	1096	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
110	1097	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
111	1098	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 MARCO	automatico	pendente	2026-03-28 03:16:48.023178	\N
112	1099	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
113	11	tpRubr	Vencimento	1	1/3 FERIAS VENCIDAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
114	110	tpRubr	Vencimento	1	HORAS EXTRAS 50% + ADIC. NOT. 35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
115	1100	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
116	1101	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
117	1102	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
118	1103	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
119	1104	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
120	1105	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
121	1106	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
122	1107	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
123	1108	tpRubr	Vencimento	1	1/3 MEDIAS FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
124	1109	tpRubr	Vencimento	1	ADIC. NOTURNO C/25%	automatico	pendente	2026-03-28 03:16:48.023178	\N
125	111	tpRubr	Vencimento	1	HORAS EXTRAS 55%	automatico	pendente	2026-03-28 03:16:48.023178	\N
126	1110	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE 07/2020 a 12/2020	automatico	pendente	2026-03-28 03:16:48.023178	\N
127	1111	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE 01/2021 a 08/2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
128	1112	tpRubr	Desconto	2	CUSTEIO SOCIAL - SINTEAC MG	automatico	pendente	2026-03-28 03:16:48.023178	\N
1990	376	codIncPisPasep	0	00	P.L.R.	automatico	pendente	2026-03-28 03:16:48.023178	\N
129	1113	tpRubr	Desconto	2	TAXA SINDICAL - SINTEAC MG	automatico	pendente	2026-03-28 03:16:48.023178	\N
130	1114	tpRubr	Vencimento	1	MULTA POR ATRASO DE SALARIO 2024	automatico	pendente	2026-03-28 03:16:48.023178	\N
131	1115	tpRubr	Vencimento	1	MULTA POR ATRASO DE SALARIO 2025	automatico	pendente	2026-03-28 03:16:48.023178	\N
132	1116	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
133	1117	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
134	1118	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
135	1119	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
136	112	tpRubr	Vencimento	1	HORAS EXTRAS 60%	automatico	pendente	2026-03-28 03:16:48.023178	\N
137	1120	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
138	1121	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
139	1122	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
140	1123	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
141	1124	tpRubr	Desconto	2	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
142	1125	tpRubr	Desconto	2	DESC. HORAS A COMPENSAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
143	1126	tpRubr	Desconto	2	PROVISAO DESC EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
144	1127	tpRubr	Vencimento	1	DEVOLUCAO PROVISAO DESC EMPREST ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
145	1128	tpRubr	Vencimento	1	DIF ADIC. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
146	1129	tpRubr	Desconto	2	DESC. ATRASOS REF MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
147	113	tpRubr	Vencimento	1	HORAS EXTRAS 60% - 04/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
148	1130	tpRubr	Desconto	2	DESC. ASS. MÉDICA DEP. MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
149	1131	tpRubr	Desconto	2	DESC. CONTRIB. ASSISTENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
150	1132	tpRubr	Desconto	2	DESC. CONTRIB. SOCIO-ASSISTENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
151	1133	tpRubr	Desconto	2	PREMIO ASSIDUIDADE - NUTRI	automatico	pendente	2026-03-28 03:16:48.023178	\N
152	1134	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE MES 12/2025	automatico	pendente	2026-03-28 03:16:48.023178	\N
153	1135	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE MES 01/2026	automatico	pendente	2026-03-28 03:16:48.023178	\N
154	114	tpRubr	Vencimento	1	HORAS EXTRAS 60% - 05/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
155	115	tpRubr	Vencimento	1	HORAS EXTRAS 60% - 09/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
156	116	tpRubr	Vencimento	1	HORAS EXTRAS 60% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
157	117	tpRubr	Vencimento	1	HORAS EXTRAS 65%	automatico	pendente	2026-03-28 03:16:48.023178	\N
158	118	tpRubr	Vencimento	1	HORAS EXTRAS 65% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
159	119	tpRubr	Vencimento	1	HORAS EXTRAS 70%	automatico	pendente	2026-03-28 03:16:48.023178	\N
160	12	tpRubr	Vencimento	1	DIF. SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
161	120	tpRubr	Vencimento	1	HORAS EXTRAS 70% - ART. 71	automatico	pendente	2026-03-28 03:16:48.023178	\N
162	121	tpRubr	Vencimento	1	HORAS EXTRAS 70% + ADIC. NOT. 30%	automatico	pendente	2026-03-28 03:16:48.023178	\N
163	122	tpRubr	Vencimento	1	HORAS EXTRAS 75%	automatico	pendente	2026-03-28 03:16:48.023178	\N
164	123	tpRubr	Vencimento	1	HORAS EXTRAS 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
165	124	tpRubr	Vencimento	1	HORAS EXTRAS 100% - DIF	automatico	pendente	2026-03-28 03:16:48.023178	\N
166	125	tpRubr	Vencimento	1	HORAS EXTRAS 100% - 09/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
167	126	tpRubr	Vencimento	1	HORAS EXTRAS 100% - 11/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
168	127	tpRubr	Vencimento	1	HORAS EXTRAS 100% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
169	128	tpRubr	Vencimento	1	HORAS EXTRAS 100% + ADIC. NOT. 35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
170	129	tpRubr	Vencimento	1	HORAS EXTRAS 110%	automatico	pendente	2026-03-28 03:16:48.023178	\N
172	130	tpRubr	Vencimento	1	HORAS EXTRAS 110%	automatico	pendente	2026-03-28 03:16:48.023178	\N
173	131	tpRubr	Vencimento	1	HORAS EXTRAS 122%	automatico	pendente	2026-03-28 03:16:48.023178	\N
174	132	tpRubr	Vencimento	1	HORAS EXTRAS 130%	automatico	pendente	2026-03-28 03:16:48.023178	\N
175	133	tpRubr	Vencimento	1	HORAS EXTRAS 150%	automatico	pendente	2026-03-28 03:16:48.023178	\N
176	134	tpRubr	Vencimento	1	HORAS EXTRAS 175%	automatico	pendente	2026-03-28 03:16:48.023178	\N
177	135	tpRubr	Vencimento	1	D.S.R. S/HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
178	1350	tpRubr	Vencimento	1	FERIAS (ANTECIPAÇÃO) - ESOCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
179	136	tpRubr	Vencimento	1	D.S.R. S/ADICIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
180	137	tpRubr	Vencimento	1	REEMB. EXAME ADMISSIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
181	138	tpRubr	Vencimento	1	DIA DO RODOVIARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
182	139	tpRubr	Vencimento	1	MULTA CLAUSULA OCTAGESIMA PRIMEIRA  CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
183	14	tpRubr	Vencimento	1	REEMB. CONTRIBUICAO COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
184	140	tpRubr	Vencimento	1	MULTA CLAUSULA QUINTA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
185	141	tpRubr	Vencimento	1	H E 100% - SUMULA 444	automatico	pendente	2026-03-28 03:16:48.023178	\N
186	142	tpRubr	Vencimento	1	ADIC. NOTURNO C/34%	automatico	pendente	2026-03-28 03:16:48.023178	\N
187	143	tpRubr	Vencimento	1	FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
188	144	tpRubr	Vencimento	1	1/3 FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
189	145	tpRubr	Vencimento	1	DEV. FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
190	146	tpRubr	Vencimento	1	DEV. D.S.R. S/FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
191	147	tpRubr	Vencimento	1	REEMB. DESC. V REFEIC N UTILIZ	automatico	pendente	2026-03-28 03:16:48.023178	\N
192	148	tpRubr	Vencimento	1	MULTA CLAUSULA DECIMA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
193	149	tpRubr	Vencimento	1	REEMB D.S.R MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
194	15	tpRubr	Vencimento	1	GRATIFICAÇÃO - EXECUTIVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
195	150	tpRubr	Vencimento	1	H E 100% - SUMULA 444 - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
196	151	tpRubr	Vencimento	1	REEMB. VALE TRANSPORTE MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
197	152	tpRubr	Vencimento	1	DIF. AD. INSALUBRIDADE REF. 12/2014 A 09/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
198	153	tpRubr	Vencimento	1	DIF. ADIC. PERICULOSIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
199	154	tpRubr	Vencimento	1	HORAS REDUZIDAS ADIC. NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
200	155	tpRubr	Vencimento	1	REEMB. VALE ALIMENTACAO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
201	156	tpRubr	Vencimento	1	DIF. FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
202	157	tpRubr	Vencimento	1	DIF PAGTO AGO-2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
203	158	tpRubr	Vencimento	1	D.S.R. S/PREMIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
204	159	tpRubr	Vencimento	1	D.S.R. S/ADICIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
205	16	tpRubr	Vencimento	1	SALARIO MES	automatico	pendente	2026-03-28 03:16:48.023178	\N
206	160	tpRubr	Vencimento	1	D.S.R. S/HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
207	161	tpRubr	Vencimento	1	D.S.R. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
208	162	tpRubr	Vencimento	1	D.S.R. S/FERIADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
209	163	tpRubr	Vencimento	1	D.S.R. S/FERIADO - HS	automatico	pendente	2026-03-28 03:16:48.023178	\N
210	164	tpRubr	Vencimento	1	D.S.R. COMPETENCIA 08/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
211	165	tpRubr	Vencimento	1	D.S.R. DIFERENCA	automatico	pendente	2026-03-28 03:16:48.023178	\N
212	166	tpRubr	Vencimento	1	D.S.R. COMPETENCIA 10/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
213	167	tpRubr	Vencimento	1	D.S.R. COMPETENCIA 11/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
214	168	tpRubr	Vencimento	1	D.S.R. COMPETENCIA 12/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
215	169	tpRubr	Vencimento	1	SABADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
216	17	tpRubr	Vencimento	1	SALARIO MES	automatico	pendente	2026-03-28 03:16:48.023178	\N
217	170	tpRubr	Vencimento	1	D.S.R. S/COMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
218	171	tpRubr	Vencimento	1	AUX. DOENÇA	automatico	pendente	2026-03-28 03:16:48.023178	\N
219	172	tpRubr	Vencimento	1	ACIDENTE DE TRABALHO (15 DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
220	173	tpRubr	Vencimento	1	ACIDENTE DE TRABALHO (F.G.T.S.)	automatico	pendente	2026-03-28 03:16:48.023178	\N
221	174	tpRubr	Vencimento	1	AUX. DOENÇA (F.G.T.S.)	automatico	pendente	2026-03-28 03:16:48.023178	\N
222	175	tpRubr	Vencimento	1	SAIDAS ABONADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
223	176	tpRubr	Vencimento	1	SALARIO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
224	177	tpRubr	Vencimento	1	SALARIO SUBSTITUTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
225	178	tpRubr	Vencimento	1	TRIENIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
226	179	tpRubr	Vencimento	1	ATESTADO MEDICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
227	18	tpRubr	Vencimento	1	ADICIONAL DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
228	180	tpRubr	Vencimento	1	LICENCA PATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
229	181	tpRubr	Vencimento	1	DOMINGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
230	182	tpRubr	Vencimento	1	FALTAS ABONADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
231	183	tpRubr	Vencimento	1	FERIADO (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
232	184	tpRubr	Vencimento	1	HORAS REDUZIDAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
233	185	tpRubr	Vencimento	1	INDENIZACAO LEI Nº 7.238/84	automatico	pendente	2026-03-28 03:16:48.023178	\N
234	186	tpRubr	Vencimento	1	LOCACAO MOTO/AUTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
235	187	tpRubr	Vencimento	1	P.L.R.	automatico	pendente	2026-03-28 03:16:48.023178	\N
236	188	tpRubr	Vencimento	1	P.L.R. REF.CCT 2011 TRT CPS	automatico	pendente	2026-03-28 03:16:48.023178	\N
237	189	tpRubr	Vencimento	1	QUEBRA DE CAIXA	automatico	pendente	2026-03-28 03:16:48.023178	\N
239	190	tpRubr	Vencimento	1	REEMB. FALTAS DESC. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
240	191	tpRubr	Vencimento	1	REINTEGRAÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
241	192	tpRubr	Vencimento	1	DECLARAÇÃO JUDICIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
242	193	tpRubr	Vencimento	1	F.G.T.S. PAGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
243	194	tpRubr	Vencimento	1	F.G.T.S. MES ANTERIOR (TEMP)	automatico	pendente	2026-03-28 03:16:48.023178	\N
244	195	tpRubr	Vencimento	1	F.G.T.S. FIM DE CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
245	196	tpRubr	Vencimento	1	HORAS DOBRADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
246	197	tpRubr	Vencimento	1	DIF. CCT - 2016	automatico	pendente	2026-03-28 03:16:48.023178	\N
247	198	tpRubr	Vencimento	1	SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
248	199	tpRubr	Vencimento	1	DIF. SALARIO PISO RJ	automatico	pendente	2026-03-28 03:16:48.023178	\N
249	2	tpRubr	Vencimento	1	SALARIO MES	automatico	pendente	2026-03-28 03:16:48.023178	\N
250	20	tpRubr	Vencimento	1	QUINQUENIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
251	200	tpRubr	Vencimento	1	ADIC. SALARIO COMP 04/2018	automatico	pendente	2026-03-28 03:16:48.023178	\N
252	201	tpRubr	Vencimento	1	ADIC. SALARIO REF. 08/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
253	202	tpRubr	Vencimento	1	ADIC. SALARIO REF. 09/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
254	203	tpRubr	Vencimento	1	ADIC. SALARIO REF. 10/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
255	204	tpRubr	Vencimento	1	DIF. SALARIO 01/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
256	205	tpRubr	Vencimento	1	DIF. SALARIO 08/2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
257	206	tpRubr	Vencimento	1	DIF. SALARIO 09/2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
258	207	tpRubr	Vencimento	1	DIF. SALARIO 10/2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
259	208	tpRubr	Vencimento	1	DIF. SALARIO 06/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
260	209	tpRubr	Vencimento	1	DIF. SALARIO 07/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
261	21	tpRubr	Vencimento	1	SALARIO SUBSTITUTO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
262	210	tpRubr	Vencimento	1	DIF. SALARIO 08/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
263	211	tpRubr	Vencimento	1	DIF. SALARIO 09/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
264	212	tpRubr	Vencimento	1	DIF. SALARIO 10/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
265	213	tpRubr	Vencimento	1	ABONO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
266	214	tpRubr	Vencimento	1	ACERTO DE FOLHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
267	215	tpRubr	Vencimento	1	HORAS DOBRADAS - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
268	216	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 01/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
269	217	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 02/12	automatico	pendente	2026-03-28 03:16:48.023178	\N
270	218	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 02/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
271	219	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 03/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
272	22	tpRubr	Vencimento	1	DIF. CCT - 2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
273	220	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 04/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
274	221	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 05/11	automatico	pendente	2026-03-28 03:16:48.023178	\N
275	222	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 05/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
276	223	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 09/11	automatico	pendente	2026-03-28 03:16:48.023178	\N
277	224	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 10/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
278	225	tpRubr	Vencimento	1	DIF HE CCT 2018	automatico	pendente	2026-03-28 03:16:48.023178	\N
279	226	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 12/12	automatico	pendente	2026-03-28 03:16:48.023178	\N
280	227	tpRubr	Vencimento	1	REEMB. HORAS EXTRAS 12/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
281	228	tpRubr	Vencimento	1	REEMB. DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
282	229	tpRubr	Vencimento	1	REEMB. CESTA PREMIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
283	23	tpRubr	Vencimento	1	DIF. CCT - 2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
284	230	tpRubr	Vencimento	1	REEMB. DESC. CONF./ASSI	automatico	pendente	2026-03-28 03:16:48.023178	\N
285	231	tpRubr	Vencimento	1	REEMB. DESPESAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
286	232	tpRubr	Vencimento	1	REEMB. EXAME DEMISSIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
287	233	tpRubr	Vencimento	1	REEMB. REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
288	234	tpRubr	Vencimento	1	REEMB. EXAMES MÉDICOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
289	235	tpRubr	Vencimento	1	TERCO CONSTIT FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
290	236	tpRubr	Vencimento	1	REEMB. VALE REFEICAO DIF.DISSIDIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
291	237	tpRubr	Vencimento	1	REEMB. SERVICOS EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
292	238	tpRubr	Vencimento	1	REEMB. VALE GUELTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
293	239	tpRubr	Vencimento	1	REEMB. VALE REFEICAO DIF. 03/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
294	24	tpRubr	Vencimento	1	PREMIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
295	240	tpRubr	Vencimento	1	REEMB. SALARIO FAMILIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
296	241	tpRubr	Vencimento	1	SALÁRIO FAMILIA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
297	242	tpRubr	Vencimento	1	REEMB. VALE REFEICAO DIF. 10/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
298	243	tpRubr	Vencimento	1	REEMB. CONTRIB. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
299	244	tpRubr	Vencimento	1	HORAS EXTRAS 50% - 04/2017	automatico	pendente	2026-03-28 03:16:48.023178	\N
300	245	tpRubr	Vencimento	1	HORAS EXTRAS 50% - 07/2016	automatico	pendente	2026-03-28 03:16:48.023178	\N
301	246	tpRubr	Vencimento	1	HORAS EXTRAS 50% - 09/2016	automatico	pendente	2026-03-28 03:16:48.023178	\N
302	247	tpRubr	Vencimento	1	DIF. SALARIO FAMILIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
303	248	tpRubr	Vencimento	1	REEMB  CONTRIB. ASSIST	automatico	pendente	2026-03-28 03:16:48.023178	\N
304	249	tpRubr	Vencimento	1	REEMB. DESC. ASS. ODONTOLOGICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
305	25	tpRubr	Vencimento	1	PREMIO CONSIGNADO - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
306	250	tpRubr	Vencimento	1	ADIC. NOTURNO C/100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
307	251	tpRubr	Vencimento	1	HORAS EXTRAS 80%	automatico	pendente	2026-03-28 03:16:48.023178	\N
308	252	tpRubr	Vencimento	1	AJUDA CRECHE CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
309	253	tpRubr	Vencimento	1	DEV. ATRASO/FALTA HORAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
310	254	tpRubr	Vencimento	1	REEMB. MENSALIDADE. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
311	255	tpRubr	Vencimento	1	DIF. CCT - 2017	automatico	pendente	2026-03-28 03:16:48.023178	\N
312	256	tpRubr	Vencimento	1	REEMB. DESC. REFEICAO (PAT)	automatico	pendente	2026-03-28 03:16:48.023178	\N
313	257	tpRubr	Vencimento	1	ABONO DE FERIAS ARTº 143 (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
314	258	tpRubr	Vencimento	1	1/3 S/ABONO FERIAS ARTº 143 (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
315	259	tpRubr	Vencimento	1	GRATIFICAÇÃO - BILINGUE	automatico	pendente	2026-03-28 03:16:48.023178	\N
316	26	tpRubr	Vencimento	1	PREMIO DOMINGOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
317	260	tpRubr	Vencimento	1	DIF. CCT S/FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
318	261	tpRubr	Vencimento	1	REEMB. CONTRIBUICOES	automatico	pendente	2026-03-28 03:16:48.023178	\N
319	262	tpRubr	Vencimento	1	HORAS EXTRAS 60% - MES 04-2017	automatico	pendente	2026-03-28 03:16:48.023178	\N
320	263	tpRubr	Vencimento	1	MULTA CLAUSULA DECIMA SEXTA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
321	264	tpRubr	Vencimento	1	MULTA VIGESIMA SETIMA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
322	265	tpRubr	Vencimento	1	REEMB. EMPRESTIMO CONSIGNADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
323	266	tpRubr	Vencimento	1	REEMB. CURSOS / TREINAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
324	267	tpRubr	Vencimento	1	HORAS EXTRAS COMPL 60%	automatico	pendente	2026-03-28 03:16:48.023178	\N
325	268	tpRubr	Vencimento	1	DIF GRATIFICACAO MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
326	269	tpRubr	Vencimento	1	HORAS EXTRAS 75% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
327	27	tpRubr	Vencimento	1	PREMIO GAR EXTEN ELETRO - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
328	270	tpRubr	Vencimento	1	H E 50% - ART. 71	automatico	pendente	2026-03-28 03:16:48.023178	\N
329	271	tpRubr	Vencimento	1	TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
330	272	tpRubr	Vencimento	1	TRANSPORTE OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
331	273	tpRubr	Vencimento	1	ARREDONDAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
332	274	tpRubr	Vencimento	1	TRANSPORTE SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
333	275	tpRubr	Vencimento	1	VALE REFEIÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
334	276	tpRubr	Vencimento	1	PAGTO. VALE-TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
335	277	tpRubr	Vencimento	1	PAGTO. VALE REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
336	278	tpRubr	Vencimento	1	PAGTO. CESTA BASICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
337	279	tpRubr	Vencimento	1	DEVOL DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
338	28	tpRubr	Vencimento	1	PREMIO GAR EXTEN MOVEIS - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
339	280	tpRubr	Vencimento	1	DIF. AJUDA CRECHE CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
340	281	tpRubr	Vencimento	1	PAGTO. ASSIST. ODONTOLOGICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
341	282	tpRubr	Vencimento	1	ADIANTAMENTO NORMAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
342	283	tpRubr	Vencimento	1	1ª PARCELA 13º SALARIO NAO SUJEITO F.G.T.S.	automatico	pendente	2026-03-28 03:16:48.023178	\N
343	284	tpRubr	Vencimento	1	PAGTO. VALE ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
344	285	tpRubr	Vencimento	1	PAGTO. OUTROS BENEFICIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
345	286	tpRubr	Vencimento	1	REEMB. VALE TRANSP. TREINAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
346	287	tpRubr	Vencimento	1	REEMB. CONTRIB. COL. LAB. SIEEACON	automatico	pendente	2026-03-28 03:16:48.023178	\N
347	288	tpRubr	Vencimento	1	ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
348	289	tpRubr	Vencimento	1	MEDIAS ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
349	29	tpRubr	Vencimento	1	PREMIO L.B. VENDAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
350	290	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE S/1ª PARCELA 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
351	291	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE S/1ª 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
352	292	tpRubr	Vencimento	1	ADIC. NOT MES ANT C/30%	automatico	pendente	2026-03-28 03:16:48.023178	\N
353	293	tpRubr	Vencimento	1	F.G.T.S. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
354	294	tpRubr	Vencimento	1	DESP DE VIAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
355	295	tpRubr	Vencimento	1	REEMB. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
356	296	tpRubr	Vencimento	1	HORAS EXTRAS 115%	automatico	pendente	2026-03-28 03:16:48.023178	\N
357	297	tpRubr	Vencimento	1	COMPLEMENTO PREVIDENCIARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
358	298	tpRubr	Vencimento	1	ADIANT. COMPLEMENTAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
359	299	tpRubr	Vencimento	1	ADIC. SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
360	3	tpRubr	Vencimento	1	BOLSA AUXILIO (ESTAGIARIO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
361	30	tpRubr	Vencimento	1	PREMIO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
362	300	tpRubr	Vencimento	1	ABONO IDADE TEMP SERVICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
363	301	tpRubr	Vencimento	1	ACORDO JUDICIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
364	302	tpRubr	Vencimento	1	REEMB. DESC.VALE TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
365	303	tpRubr	Vencimento	1	REEMB. DESC. FALTAS E ATRASOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
366	304	tpRubr	Vencimento	1	REEMB. VALE REFEICAO 01 E 02/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
367	305	tpRubr	Vencimento	1	REEMB.V.REFEICAO./ ALIM. REF. EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
368	306	tpRubr	Vencimento	1	REEMB. VALE-TRANSPORTE REF. EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
369	307	tpRubr	Vencimento	1	ADIC DE SALARIO MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
370	308	tpRubr	Vencimento	1	BENEFICIOS GERENTES	automatico	pendente	2026-03-28 03:16:48.023178	\N
371	309	tpRubr	Vencimento	1	BENEFICIOS PAGOS A MENOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
372	31	tpRubr	Vencimento	1	PREMIO MOVEIS - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
373	310	tpRubr	Vencimento	1	REEMB DESC INDEVIDO - D.S.R	automatico	pendente	2026-03-28 03:16:48.023178	\N
374	311	tpRubr	Vencimento	1	COMPLEMENTO HORAS EXTRAS 50% - 08/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
375	312	tpRubr	Vencimento	1	COMPLEMENTO PGTO.	automatico	pendente	2026-03-28 03:16:48.023178	\N
376	313	tpRubr	Vencimento	1	DEVOLUCAO DESC. CRACHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
377	314	tpRubr	Vencimento	1	DIF. CESTA BASICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
378	315	tpRubr	Vencimento	1	DIF. GUELTA PAGA	automatico	pendente	2026-03-28 03:16:48.023178	\N
379	316	tpRubr	Vencimento	1	DIF. VALE REFEICAO ANCINE 08/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
380	317	tpRubr	Vencimento	1	DIF. VALE REFEICAO TJMG 01 E 02/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
381	318	tpRubr	Vencimento	1	DIF. VENDA MOVEIS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
382	319	tpRubr	Vencimento	1	REEMB. CONSULTA. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
383	32	tpRubr	Vencimento	1	PREMIO PRODUTIVIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
384	320	tpRubr	Vencimento	1	SOBRE AVISO	automatico	pendente	2026-03-28 03:16:48.023178	\N
385	321	tpRubr	Vencimento	1	AUXILIO LENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
386	322	tpRubr	Vencimento	1	TEMPO DE ESPERA	automatico	pendente	2026-03-28 03:16:48.023178	\N
387	323	tpRubr	Vencimento	1	HORA FICTA SEAC	automatico	pendente	2026-03-28 03:16:48.023178	\N
388	324	tpRubr	Vencimento	1	DIF. CCT - 2018	automatico	pendente	2026-03-28 03:16:48.023178	\N
389	325	tpRubr	Vencimento	1	HORA FICTA SEAC - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
390	326	tpRubr	Vencimento	1	1/3 FERIAS COMPLEMENTARES(VLR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
391	327	tpRubr	Vencimento	1	ABONADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
392	328	tpRubr	Vencimento	1	ADIANTAMENTO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
393	329	tpRubr	Vencimento	1	ABONO 50% - clausula 32 item V CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
394	33	tpRubr	Vencimento	1	PREMIO SEGUROS	automatico	pendente	2026-03-28 03:16:48.023178	\N
395	330	tpRubr	Vencimento	1	AJUSTE AVISO PREVIO CLAUSULA 28° CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
396	331	tpRubr	Vencimento	1	AUXILIO FILHO EXCEPCIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
397	332	tpRubr	Vencimento	1	AUXILIO UNIFORME	automatico	pendente	2026-03-28 03:16:48.023178	\N
398	333	tpRubr	Vencimento	1	AUXILIO UNIFORME DIF. CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
399	334	tpRubr	Vencimento	1	AVISO PREVIO ADICIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
400	335	tpRubr	Vencimento	1	AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
401	336	tpRubr	Vencimento	1	AVISO PREVIO INDENIZADO - S/VA	automatico	pendente	2026-03-28 03:16:48.023178	\N
402	337	tpRubr	Vencimento	1	D.S.R. S/VARIAVEIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
403	338	tpRubr	Vencimento	1	D.S.R. SOBRE HORAS EXTRAS / AD. NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
404	339	tpRubr	Vencimento	1	DEVOLUCAO FALTAS / DSR	automatico	pendente	2026-03-28 03:16:48.023178	\N
405	34	tpRubr	Vencimento	1	PREMIO SEGUROS GER	automatico	pendente	2026-03-28 03:16:48.023178	\N
406	340	tpRubr	Vencimento	1	DIF. ADICIONAL NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
407	341	tpRubr	Vencimento	1	DIF. CCT/2019	automatico	pendente	2026-03-28 03:16:48.023178	\N
408	342	tpRubr	Vencimento	1	DIF. CESTA BASICA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
409	343	tpRubr	Vencimento	1	DIF. VALE REFEICAO CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
410	344	tpRubr	Vencimento	1	DIFERENCA DE DISSIDIO 07 2012	automatico	pendente	2026-03-28 03:16:48.023178	\N
411	345	tpRubr	Vencimento	1	DIFERENCA DE DISSIDIO 08 2012	automatico	pendente	2026-03-28 03:16:48.023178	\N
412	346	tpRubr	Vencimento	1	DIFERENCA DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
413	347	tpRubr	Vencimento	1	FERIAS VENCIDAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
414	348	tpRubr	Vencimento	1	1/3 FERIAS VENCIDAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
415	349	tpRubr	Vencimento	1	AVISO PREVIO INDENIZADO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
416	35	tpRubr	Vencimento	1	DIF. D.S.R.	automatico	pendente	2026-03-28 03:16:48.023178	\N
417	350	tpRubr	Vencimento	1	FERIAS NORMAIS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
418	351	tpRubr	Vencimento	1	1/3 FERIAS NORMAIS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
419	352	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE S/FERIAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
420	353	tpRubr	Vencimento	1	AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
421	354	tpRubr	Vencimento	1	MEDIAS S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
422	355	tpRubr	Vencimento	1	ADIC. FERIAS TEMP	automatico	pendente	2026-03-28 03:16:48.023178	\N
423	356	tpRubr	Vencimento	1	BOLSA AUXILIO (ESTAGIARIO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
424	357	tpRubr	Vencimento	1	FERIAS PROPORCIONAIS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
425	358	tpRubr	Vencimento	1	1/3 FERIAS PROPORCIONAIS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
426	359	tpRubr	Vencimento	1	ADIC. FERIAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
427	36	tpRubr	Vencimento	1	DIF.CONV COLETIVA	automatico	pendente	2026-03-28 03:16:48.023178	\N
428	360	tpRubr	Vencimento	1	1/3 ADIC. FERIAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
429	361	tpRubr	Vencimento	1	ADIC. FERIAS S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
430	362	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE S/FERIAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
431	363	tpRubr	Vencimento	1	EMPRESTIMO SALDO NEGATIVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
432	364	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE FERIAS INDENIZADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
433	365	tpRubr	Vencimento	1	ABONO APOSENTADORIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
434	366	tpRubr	Vencimento	1	DEVOL. I.N.S.S.- FOLHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
435	367	tpRubr	Vencimento	1	13º SALARIO PROP. S/AVISO PREVIO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
436	368	tpRubr	Vencimento	1	FERIAS S/AVISO PREVIO INDENIZADO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
437	369	tpRubr	Vencimento	1	1/3 FERIAS S/AVISO PREVIO INDENIZADO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
438	37	tpRubr	Vencimento	1	DIF. DISSIDIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
439	370	tpRubr	Vencimento	1	13º SALARIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
440	371	tpRubr	Vencimento	1	13º SALARIO PROP. S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
441	372	tpRubr	Vencimento	1	FERIAS S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
442	373	tpRubr	Vencimento	1	1/3 FERIAS S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
443	374	tpRubr	Vencimento	1	1/3 ADIC. FERIAS S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
444	375	tpRubr	Vencimento	1	ADIC. 13º SALARIO S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
445	376	tpRubr	Vencimento	1	P.L.R.	automatico	pendente	2026-03-28 03:16:48.023178	\N
446	377	tpRubr	Vencimento	1	PREMIO TEMPO DE SERVICO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
447	378	tpRubr	Vencimento	1	REEMBOLSO DE UNIFORMES	automatico	pendente	2026-03-28 03:16:48.023178	\N
448	379	tpRubr	Vencimento	1	REEMB VALE REFEICAO/ ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
449	38	tpRubr	Vencimento	1	DIF. DISSIDIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
450	380	tpRubr	Vencimento	1	SALDO DE SALARIOS.	automatico	pendente	2026-03-28 03:16:48.023178	\N
451	381	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
452	382	tpRubr	Vencimento	1	BOLSA AUXILIO (ESTAGIARIO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
453	383	tpRubr	Vencimento	1	Diferenca Dissidio 2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
454	384	tpRubr	Vencimento	1	EMPRESTIMO FOLHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
455	385	tpRubr	Vencimento	1	FERIAS COMPLEMENTARES (VLR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
456	386	tpRubr	Vencimento	1	FERIAS PROPORCIONAIS - S/VAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
457	387	tpRubr	Vencimento	1	FERIAS VENCIDAS INDENIZ.	automatico	pendente	2026-03-28 03:16:48.023178	\N
458	388	tpRubr	Vencimento	1	FERIAS VENCIDAS INDENIZ. S/VAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
459	389	tpRubr	Vencimento	1	HORA EXTRA NOTURNA	automatico	pendente	2026-03-28 03:16:48.023178	\N
460	39	tpRubr	Vencimento	1	DIF. DISSIDIO - 02/2010	automatico	pendente	2026-03-28 03:16:48.023178	\N
461	390	tpRubr	Vencimento	1	SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
462	391	tpRubr	Vencimento	1	SALARIO MATERNIDADE (antigo)	automatico	pendente	2026-03-28 03:16:48.023178	\N
463	392	tpRubr	Vencimento	1	HORAS INTERJORN 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
464	393	tpRubr	Vencimento	1	F.G.T.S. S/AVISO PREVIO (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
465	394	tpRubr	Desconto	2	DESC. PROGAM.QUALIFI.PROFISSIONAL - PQM	automatico	pendente	2026-03-28 03:16:48.023178	\N
466	395	tpRubr	Vencimento	1	DIF - DIA DO RODOVIARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
467	396	tpRubr	Vencimento	1	DEVOL. I.N.S.S. - 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
468	397	tpRubr	Vencimento	1	DIF - DESP DE VIAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
469	398	tpRubr	Desconto	2	DIF-DESC. AJUSTE DESP DE VIAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
470	399	tpRubr	Vencimento	1	1/3 FERIAS NORMAIS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
471	4	tpRubr	Vencimento	1	COMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
472	40	tpRubr	Vencimento	1	DIF. DISSIDIO - 03/2010	automatico	pendente	2026-03-28 03:16:48.023178	\N
473	400	tpRubr	Vencimento	1	COMPLEMENTO FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
474	401	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
475	402	tpRubr	Vencimento	1	PREMIO TEMPO DE SERVICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
476	403	tpRubr	Vencimento	1	COMPLEMENTO FERIAS (DISSIDIO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
477	404	tpRubr	Vencimento	1	DIF. FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
478	405	tpRubr	Vencimento	1	MEDIAS FERIAS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
479	406	tpRubr	Vencimento	1	1/3 MEDIAS FERIAS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
480	407	tpRubr	Vencimento	1	MEDIAS FERIAS S/ABONO (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
481	408	tpRubr	Vencimento	1	1/3 MEDIAS FERIAS S/ABONO (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
482	409	tpRubr	Vencimento	1	FERIAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
483	41	tpRubr	Vencimento	1	DIF. DISSIDIO - 03/2012	automatico	pendente	2026-03-28 03:16:48.023178	\N
484	410	tpRubr	Vencimento	1	FERIAS MES SEGUINTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
485	411	tpRubr	Vencimento	1	MEDIA HORAS EXTRAS FERIAS PROP	automatico	pendente	2026-03-28 03:16:48.023178	\N
486	412	tpRubr	Vencimento	1	1/3 ADIC. FERIAS MES SEGUINTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
487	413	tpRubr	Vencimento	1	1/3 FERIAS FERIAS PROPORCIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
488	414	tpRubr	Vencimento	1	1/3 FERIAS MES SEGUINTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
489	415	tpRubr	Vencimento	1	1/3 FERIAS S/AVISO	automatico	pendente	2026-03-28 03:16:48.023178	\N
490	416	tpRubr	Vencimento	1	1/3 MEDIA FERIAS PROPORCIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
491	417	tpRubr	Vencimento	1	1/3 S/ABONO DE FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
492	418	tpRubr	Vencimento	1	1/3 S/ADIC. ABONO FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
493	419	tpRubr	Vencimento	1	ABONO DE FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
494	42	tpRubr	Vencimento	1	DIF. DISSIDIO - 04/2010	automatico	pendente	2026-03-28 03:16:48.023178	\N
495	420	tpRubr	Vencimento	1	ABONO PECUNIARIO RODOVIARIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
496	421	tpRubr	Vencimento	1	AJUDA DE CUSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
497	422	tpRubr	Vencimento	1	ANTECIPACAO DE PGTO.	automatico	pendente	2026-03-28 03:16:48.023178	\N
498	423	tpRubr	Vencimento	1	AUXILIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
499	424	tpRubr	Vencimento	1	AUXILIO FUNERAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
500	425	tpRubr	Vencimento	1	AUXILIO MORADIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
501	426	tpRubr	Vencimento	1	COMBUSTIVEL	automatico	pendente	2026-03-28 03:16:48.023178	\N
502	427	tpRubr	Vencimento	1	ATUALIZACAO MONETARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
503	428	tpRubr	Vencimento	1	REEMBOLSO DESC. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
504	429	tpRubr	Vencimento	1	DESC. INDEVIDO DE FALTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
505	43	tpRubr	Vencimento	1	DIF. DISSIDIO - 04/2012	automatico	pendente	2026-03-28 03:16:48.023178	\N
506	430	tpRubr	Vencimento	1	DEVOLUCAO DESC. VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
507	431	tpRubr	Vencimento	1	DEVOLUCAO DESC. MULTAS TRANSITO	automatico	pendente	2026-03-28 03:16:48.023178	\N
508	432	tpRubr	Vencimento	1	DEVOLUCAO PENDEN PREST CONTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
509	433	tpRubr	Vencimento	1	DEVOLUCAO UNIFORMES	automatico	pendente	2026-03-28 03:16:48.023178	\N
510	434	tpRubr	Vencimento	1	ADIC. DE ABONO	automatico	pendente	2026-03-28 03:16:48.023178	\N
511	435	tpRubr	Vencimento	1	ADIC. FERIAS MES SEGUINTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
512	436	tpRubr	Vencimento	1	ADIC. FERIAS VENCIDAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
513	437	tpRubr	Vencimento	1	ADIC. S/ABONO FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
514	438	tpRubr	Vencimento	1	HORA EXTRA NOTURNA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
515	439	tpRubr	Vencimento	1	HORAS EXTRAS 100% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
516	44	tpRubr	Vencimento	1	DIF. DISSIDIO - 09/2009	automatico	pendente	2026-03-28 03:16:48.023178	\N
517	440	tpRubr	Vencimento	1	HORAS EXTRAS 140%	automatico	pendente	2026-03-28 03:16:48.023178	\N
518	441	tpRubr	Vencimento	1	HORAS EXTRAS 50% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
519	442	tpRubr	Vencimento	1	HORAS NORMAIS CREDITO	automatico	pendente	2026-03-28 03:16:48.023178	\N
520	443	tpRubr	Vencimento	1	INDEN. ADIC. TEMPO SERVICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
521	444	tpRubr	Vencimento	1	DIF. VA E VR - CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
522	445	tpRubr	Vencimento	1	DIF. OUTROS BENEFICIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
523	446	tpRubr	Vencimento	1	GRATIFICACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
524	447	tpRubr	Vencimento	1	GRATIFICACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
525	448	tpRubr	Vencimento	1	GRATIFICACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
526	449	tpRubr	Vencimento	1	GRATIFICACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
527	45	tpRubr	Vencimento	1	DIF. DISSIDIO - 10/2008	automatico	pendente	2026-03-28 03:16:48.023178	\N
528	450	tpRubr	Vencimento	1	FERIAS MES A MES INDENIZADA  (TEMP)	automatico	pendente	2026-03-28 03:16:48.023178	\N
529	451	tpRubr	Vencimento	1	1/3 FERIAS MES A MES INDENIZADA	automatico	pendente	2026-03-28 03:16:48.023178	\N
530	452	tpRubr	Desconto	2	DESC GRAT - EXECUTIVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
531	453	tpRubr	Vencimento	1	ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
532	454	tpRubr	Desconto	2	DESC. AVARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
533	455	tpRubr	Vencimento	1	ADIC. INSAL 12092018 27022019	automatico	pendente	2026-03-28 03:16:48.023178	\N
534	456	tpRubr	Vencimento	1	DIF. CCT - 2020	automatico	pendente	2026-03-28 03:16:48.023178	\N
535	457	tpRubr	Vencimento	1	ADIC. NOTURNO C/20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
536	458	tpRubr	Vencimento	1	HORAS EXTRAS 70% MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
537	459	tpRubr	Vencimento	1	13 SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
538	46	tpRubr	Vencimento	1	DIF. DISSIDIO - 10/2009	automatico	pendente	2026-03-28 03:16:48.023178	\N
539	460	tpRubr	Vencimento	1	FERIAS PARA ABATER DESCONTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
540	461	tpRubr	Vencimento	1	DESC. FERIAS PARA ABATER DESCONTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
541	462	tpRubr	Desconto	2	DESC H EXTRAS 50% - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
542	463	tpRubr	Vencimento	1	FERIAS A COMPENSAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
543	464	tpRubr	Vencimento	1	DIF. 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
544	465	tpRubr	Vencimento	1	DIF. 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
545	466	tpRubr	Vencimento	1	CLAUSULA 22ª CCT TRT SP 06/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
546	467	tpRubr	Vencimento	1	CLAUSULA 22ª CCT TRT SP 07/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
547	468	tpRubr	Vencimento	1	CLAUSULA 22ª CCT TRT SP 08/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
548	469	tpRubr	Vencimento	1	13º SALARIO S/SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
549	47	tpRubr	Vencimento	1	SALARIO FAMILIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
550	470	tpRubr	Vencimento	1	13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
551	471	tpRubr	Vencimento	1	CLAUSULA 22ª CCT TRT SP 09/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
552	472	tpRubr	Vencimento	1	CLAUSULA 22ª CCT TRT SP 10/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
553	473	tpRubr	Vencimento	1	ARTIGO 071	automatico	pendente	2026-03-28 03:16:48.023178	\N
554	474	tpRubr	Vencimento	1	ARTIGO 071 MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
555	475	tpRubr	Vencimento	1	ARTIGO 071 TRT EMERGENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
556	476	tpRubr	Vencimento	1	TRIBUTO S/SALARIO (NÃO UTILIZAR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
557	477	tpRubr	Vencimento	1	TRIBUTO S/BENEFICIO (NÃO UTILIZAR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
558	478	tpRubr	Vencimento	1	ARTIGO 477	automatico	pendente	2026-03-28 03:16:48.023178	\N
559	479	tpRubr	Vencimento	1	INDENIZACAO ARTº 479	automatico	pendente	2026-03-28 03:16:48.023178	\N
560	48	tpRubr	Vencimento	1	DIF. DISSIDIO - 11/2008	automatico	pendente	2026-03-28 03:16:48.023178	\N
561	480	tpRubr	Vencimento	1	ADIC. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
562	481	tpRubr	Vencimento	1	ADIC. 13º SALARIO S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
563	482	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE S/2ª PARCELA 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
564	483	tpRubr	Vencimento	1	F.G.T.S. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
565	484	tpRubr	Vencimento	1	AJUDA COMPUSORIA MP936	automatico	pendente	2026-03-28 03:16:48.023178	\N
566	485	tpRubr	Vencimento	1	DIF. ASSISTENCIA ODONTOLOGICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
567	486	tpRubr	Vencimento	1	F.G.T.S. 13º  FATURADO 1 AVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
568	487	tpRubr	Vencimento	1	ENCARGOS S/ FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
569	488	tpRubr	Vencimento	1	DIF. VALE REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
570	489	tpRubr	Vencimento	1	DIF. CESTA BASICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
571	49	tpRubr	Vencimento	1	DIF. DISSIDIO - 11/2009	automatico	pendente	2026-03-28 03:16:48.023178	\N
572	490	tpRubr	Vencimento	1	DIF. ASSISTENCIA MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
573	491	tpRubr	Vencimento	1	FERIAS (FATURAMENTO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
574	492	tpRubr	Vencimento	1	ENCARGOS S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
575	493	tpRubr	Vencimento	1	13º SALARIO (FATURAMENTO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
576	494	tpRubr	Vencimento	1	F.G.T.S. S/13º SALARIO DEPOSITADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
577	495	tpRubr	Vencimento	1	COMPLEMENTO D.S.	automatico	pendente	2026-03-28 03:16:48.023178	\N
578	496	tpRubr	Vencimento	1	F.G.T.S. (FATURAMENTO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
579	497	tpRubr	Vencimento	1	ENCARGOS S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
580	498	tpRubr	Vencimento	1	ENCARGOS S/FOLHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
581	499	tpRubr	Vencimento	1	DIF. VALE-TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
582	5	tpRubr	Vencimento	1	PARTICIPACAO LUCROS/RESULTADOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
583	50	tpRubr	Vencimento	1	SALARIO AUTONOMO	automatico	pendente	2026-03-28 03:16:48.023178	\N
584	500	tpRubr	Desconto	2	DESC. FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
585	501	tpRubr	Desconto	2	DESC. FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
586	502	tpRubr	Desconto	2	DESC. ATRASO/FALTA HORAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
587	503	tpRubr	Desconto	2	DESC. D.S.R. S/FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
588	504	tpRubr	Desconto	2	DESC. D.S.R. S/FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
589	505	tpRubr	Desconto	2	DESC. ATRASOS/SAIDAS ANTECIPADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
590	506	tpRubr	Desconto	2	DESC. ATRASOS/SAIDAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
591	507	tpRubr	Desconto	2	DESC. D.S.R. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
592	508	tpRubr	Desconto	2	DESC. D.S.R. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
593	509	tpRubr	Desconto	2	DESC. DEV. HE/A.N./DSR - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
594	51	tpRubr	Vencimento	1	ADIC. NOT. COMPLEMENTAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
595	510	tpRubr	Desconto	2	DESC. DEVOL.PAGTO A MAIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
596	511	tpRubr	Desconto	2	DESC. DIF.DISSIDIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
597	512	tpRubr	Desconto	2	DESC. FALTAS HORAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
598	513	tpRubr	Desconto	2	DESC. HE/FICTA -  PAGAS A MAIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
599	514	tpRubr	Desconto	2	DESC. FALTA DEVOLUCAO MATERIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
600	515	tpRubr	Desconto	2	DESC. SAIDA ANTECIPADA	automatico	pendente	2026-03-28 03:16:48.023178	\N
601	516	tpRubr	Desconto	2	DESC. ASSIST. ODONTOLOGICA DEPENDENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
602	517	tpRubr	Desconto	2	Desc Art 480	automatico	pendente	2026-03-28 03:16:48.023178	\N
603	518	tpRubr	Desconto	2	ESTORNO DE PAGAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
604	519	tpRubr	Desconto	2	DESC. CONTRIB. ASSISTENCIAL LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
605	52	tpRubr	Vencimento	1	ADIC. NOTURNO C/20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
606	520	tpRubr	Desconto	2	DESC. AVARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
607	521	tpRubr	Desconto	2	DESC. AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
608	522	tpRubr	Desconto	2	DESC. CO PARTICIPACAO A.M.	automatico	pendente	2026-03-28 03:16:48.023178	\N
609	523	tpRubr	Desconto	2	DESC. COMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
610	524	tpRubr	Desconto	2	DESC. DIF. SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
611	525	tpRubr	Desconto	2	DESC. PGTO. ANTECIPADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
612	526	tpRubr	Desconto	2	DESC. PLR	automatico	pendente	2026-03-28 03:16:48.023178	\N
613	527	tpRubr	Desconto	2	DESC. PROGRAMA ASSIST. FAMILIAR (PAF)	automatico	pendente	2026-03-28 03:16:48.023178	\N
614	528	tpRubr	Desconto	2	DESC. QUEBRA CAIXA (FALTA DE  CAIXA)	automatico	pendente	2026-03-28 03:16:48.023178	\N
615	529	tpRubr	Desconto	2	DESC. BENEFICIO SOC. FAMILIAR - 02/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
616	53	tpRubr	Vencimento	1	REEMB. I.R.F.	automatico	pendente	2026-03-28 03:16:48.023178	\N
617	530	tpRubr	Desconto	2	DESC. VALE-TRANSP DISSIDIO 6%	automatico	pendente	2026-03-28 03:16:48.023178	\N
618	531	tpRubr	Desconto	2	DESC. VA/ VR NAO UTILIZADO ATESTADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
619	532	tpRubr	Desconto	2	DESC. CONTRIB. COFEDERATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
620	533	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
621	534	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
622	535	tpRubr	Desconto	2	DESC. CONTRIB. COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
623	536	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
624	537	tpRubr	Desconto	2	DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
625	538	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
626	539	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
627	54	tpRubr	Vencimento	1	ADIC. NOTURNO C/25%	automatico	pendente	2026-03-28 03:16:48.023178	\N
628	540	tpRubr	Desconto	2	DESC. SALDO NEGATIVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
629	541	tpRubr	Desconto	2	DESC. ARREDONDAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
630	542	tpRubr	Desconto	2	DESC. ADIANT. NORMAL(DENTRO DO MES)	automatico	pendente	2026-03-28 03:16:48.023178	\N
631	543	tpRubr	Desconto	2	DESC. VALE-TRANSP - CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
632	544	tpRubr	Desconto	2	DESC. DIVERSOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
633	545	tpRubr	Desconto	2	DESC. EMPRESTIMO	automatico	pendente	2026-03-28 03:16:48.023178	\N
634	546	tpRubr	Desconto	2	DESC. ADIANT. NORMAL (FORAMES)	automatico	pendente	2026-03-28 03:16:48.023178	\N
635	547	tpRubr	Desconto	2	DESC. ESTACIONAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
636	548	tpRubr	Desconto	2	DESC. VR NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
637	549	tpRubr	Desconto	2	DESC. EXTRAVIO MAT EMPRESA	automatico	pendente	2026-03-28 03:16:48.023178	\N
638	55	tpRubr	Vencimento	1	PRO-LABORE	automatico	pendente	2026-03-28 03:16:48.023178	\N
639	550	tpRubr	Desconto	2	DESC. PAGTO. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
640	551	tpRubr	Desconto	2	DESC. ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
641	552	tpRubr	Desconto	2	DESC. CONTRIB. ASSISTENCIAL LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
642	553	tpRubr	Desconto	2	DESC. 13º SALARIO PAGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
643	554	tpRubr	Desconto	2	DESC. 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
644	555	tpRubr	Desconto	2	DESC. 13º SALARIO ANTECIPADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
645	556	tpRubr	Desconto	2	DESC. MEDIAS ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
646	557	tpRubr	Desconto	2	DESC. ADIC. PERICULOSIDADE S/1ª PARCEL 13ª SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
647	558	tpRubr	Desconto	2	DESC. ANTEC. ADIC. INSALUBRIDADE S/13º 1ª PARCELA	automatico	pendente	2026-03-28 03:16:48.023178	\N
648	559	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
649	56	tpRubr	Vencimento	1	ADIC. NOTURNO C/30%	automatico	pendente	2026-03-28 03:16:48.023178	\N
650	560	tpRubr	Desconto	2	DESC. FERIAS PAGAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
651	561	tpRubr	Desconto	2	DESC. ANTECIPACAO 13º SALARIO (FERIAS) PARA ABATER	automatico	pendente	2026-03-28 03:16:48.023178	\N
652	562	tpRubr	Desconto	2	DESC. EXTRAVIO CELULAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
653	563	tpRubr	Desconto	2	LIQUIDO EM INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
654	564	tpRubr	Desconto	2	DESC. 2ª VIA CARTAO ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
655	565	tpRubr	Desconto	2	DESC. H E 60% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
656	566	tpRubr	Desconto	2	DESC. I.N.S.S.	automatico	pendente	2026-03-28 03:16:48.023178	\N
657	567	tpRubr	Desconto	2	LIQ EM DUPLIC 07-2015 13ºSAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
658	568	tpRubr	Desconto	2	DESC. PAGTO DIF VALE ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
659	569	tpRubr	Desconto	2	DESC. I.R.F. S/ PARTICIPACAO NOS LUCROS	automatico	pendente	2026-03-28 03:16:48.023178	\N
660	57	tpRubr	Vencimento	1	ADIC. NOTURNO C/35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
661	570	tpRubr	Desconto	2	DESC. I.R.F.	automatico	pendente	2026-03-28 03:16:48.023178	\N
662	571	tpRubr	Desconto	2	DESC. I.R.F. S/FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
663	572	tpRubr	Desconto	2	DESC. I.R.F. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
664	573	tpRubr	Desconto	2	DESC. I.R.F. S/ PARTICIPACAO NOS LUCROS	automatico	pendente	2026-03-28 03:16:48.023178	\N
665	574	tpRubr	Desconto	2	DESC. DIF. I.R.F.	automatico	pendente	2026-03-28 03:16:48.023178	\N
666	575	tpRubr	Desconto	2	DESC. CONTRIB. ASSISTENCIAL - SINDMAN	automatico	pendente	2026-03-28 03:16:48.023178	\N
667	576	tpRubr	Desconto	2	DESC. VALE TRANSP. NAO UTILIZADO PROX MES	automatico	pendente	2026-03-28 03:16:48.023178	\N
668	577	tpRubr	Desconto	2	DESC. VA NAO UTILIZADO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
669	578	tpRubr	Desconto	2	DESC. VALE LANCHE NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
670	579	tpRubr	Desconto	2	DESC. FALTAS (DIAS) MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
671	58	tpRubr	Vencimento	1	ADIC. NOTURNO C/40%	automatico	pendente	2026-03-28 03:16:48.023178	\N
672	580	tpRubr	Desconto	2	INDENIZACAO ARTº 480	automatico	pendente	2026-03-28 03:16:48.023178	\N
673	581	tpRubr	Desconto	2	DESC. CONTRIB. ASS. LAB. SETUHCAM	automatico	pendente	2026-03-28 03:16:48.023178	\N
674	582	tpRubr	Desconto	2	DESC. CONTRIB. COL. LAB. SINTACLUNS	automatico	pendente	2026-03-28 03:16:48.023178	\N
675	583	tpRubr	Desconto	2	DESC. CONTRIB. COL. LAB. SIEEACON	automatico	pendente	2026-03-28 03:16:48.023178	\N
676	584	tpRubr	Desconto	2	DESC. MENS. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
677	585	tpRubr	Desconto	2	DESC. MENS. SINDICAL MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
678	586	tpRubr	Desconto	2	DESC. CONTRIB. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
679	587	tpRubr	Desconto	2	DESC. CONTRIB. CONFEDERATIVA	automatico	pendente	2026-03-28 03:16:48.023178	\N
680	588	tpRubr	Desconto	2	DESC. CONTRIB. CONFEDERATIVA ASSISTENCIAL BH 2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
681	589	tpRubr	Desconto	2	DESC. CONTRIB. CONFEDERATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
682	59	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE 08/2019	automatico	pendente	2026-03-28 03:16:48.023178	\N
683	590	tpRubr	Desconto	2	DESC. CONTRIB. ASSISTENCIAL MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
684	591	tpRubr	Desconto	2	DESC. CONTRIB. COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
685	592	tpRubr	Desconto	2	DESC. CONTRIB. ASSISTENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
686	593	tpRubr	Desconto	2	DESC. CONTRIB. ASSISTENCIAL 13º	automatico	pendente	2026-03-28 03:16:48.023178	\N
687	594	tpRubr	Desconto	2	DESC. CONTRIB. SOC. LABORAL ANCINE	automatico	pendente	2026-03-28 03:16:48.023178	\N
688	595	tpRubr	Desconto	2	DESC. CONTRIB. NEGOCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
689	596	tpRubr	Desconto	2	DESC. I.N.S.S. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
690	597	tpRubr	Desconto	2	DESC. D.S.R. S/FALTAS (DIAS) MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
691	598	tpRubr	Desconto	2	DESC PAGTO A MAIOR AD NOT	automatico	pendente	2026-03-28 03:16:48.023178	\N
692	599	tpRubr	Desconto	2	DESC H.E PAGO MAIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
693	6	tpRubr	Vencimento	1	COMISSAO ELETRO - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
694	60	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE 07/2019	automatico	pendente	2026-03-28 03:16:48.023178	\N
695	600	tpRubr	Desconto	2	DESC. ACIDENTE DE TRABALHO (F.G.T.S.)	automatico	pendente	2026-03-28 03:16:48.023178	\N
696	601	tpRubr	Desconto	2	DESC. AUXILIO DOENCA	automatico	pendente	2026-03-28 03:16:48.023178	\N
697	602	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
698	603	tpRubr	Desconto	2	DESC. ASS. MÉDICA BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
699	604	tpRubr	Desconto	2	DESC BASE SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
700	605	tpRubr	Desconto	2	DESC. ASSIST. ODONTO. DEPENDENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
701	606	tpRubr	Desconto	2	DESC. ASSIST. ODONTO. DEPENDENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
702	607	tpRubr	Desconto	2	DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
703	608	tpRubr	Desconto	2	DESC. CONTRIB. COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
704	609	tpRubr	Desconto	2	DESC. HORAS MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
705	61	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
706	610	tpRubr	Desconto	2	DESC. VT NAO UTILIZADO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
707	611	tpRubr	Desconto	2	DESC. VALE ALIMENTACAO - CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
708	612	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
709	613	tpRubr	Desconto	2	DESC. JUDICIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
710	614	tpRubr	Desconto	2	DESC. EMPRESTIMO BV	automatico	pendente	2026-03-28 03:16:48.023178	\N
711	615	tpRubr	Desconto	2	DESC. ASS. MÉDICA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
712	616	tpRubr	Desconto	2	DESC. CONTRIB. ASSISTENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
713	617	tpRubr	Desconto	2	DESC. ASS. MÉDICA FIOCRUZ	automatico	pendente	2026-03-28 03:16:48.023178	\N
714	618	tpRubr	Desconto	2	DESC. ASS. MÉDICA MES ANT FIOCRUZ	automatico	pendente	2026-03-28 03:16:48.023178	\N
715	619	tpRubr	Desconto	2	DESC. ASS. MÉDICA DEP.	automatico	pendente	2026-03-28 03:16:48.023178	\N
716	62	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
717	620	tpRubr	Desconto	2	DESC. ASS. MÉDICA DEP. MES ANT FIOCRUZ	automatico	pendente	2026-03-28 03:16:48.023178	\N
718	621	tpRubr	Desconto	2	DESC. BB DETAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
719	622	tpRubr	Desconto	2	DESC. VT NAO UTILIZADO MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
720	623	tpRubr	Desconto	2	DESC. REFEIÇÃO/ALIMENTAÇÃO PRÓXIMO MÊS	automatico	pendente	2026-03-28 03:16:48.023178	\N
721	624	tpRubr	Desconto	2	DESC. VALE REFEIÇÃO - CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
722	625	tpRubr	Desconto	2	DESPESAS POSTAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
723	626	tpRubr	Desconto	2	DESC. ATRASO/FALTA HORAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
724	627	tpRubr	Desconto	2	DESC. ADIANT. NORMAL(DENTRO DO MES)	automatico	pendente	2026-03-28 03:16:48.023178	\N
725	628	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA ABONO	automatico	pendente	2026-03-28 03:16:48.023178	\N
726	629	tpRubr	Desconto	2	DESC HE 100 - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
727	63	tpRubr	Vencimento	1	AUX. NATALIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
728	630	tpRubr	Desconto	2	DESC H EXTRAS 60% - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
729	631	tpRubr	Desconto	2	DESC. ASSIST. ODONT. SINTACLUNS	automatico	pendente	2026-03-28 03:16:48.023178	\N
730	632	tpRubr	Desconto	2	DESC. CONT.. COLAB. LAB. CABINEIROS	automatico	pendente	2026-03-28 03:16:48.023178	\N
731	633	tpRubr	Desconto	2	DESC H EXTRAS 100% - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
732	634	tpRubr	Desconto	2	DESC. CONTRIB. ASS. LAB. SIEEACON	automatico	pendente	2026-03-28 03:16:48.023178	\N
733	635	tpRubr	Desconto	2	DIF EMPRESTIMO	automatico	pendente	2026-03-28 03:16:48.023178	\N
734	636	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
735	637	tpRubr	Desconto	2	DESC. CONTRIB. COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
736	638	tpRubr	Desconto	2	DESC. ASSIST. ODONT. DEP. SINTACLUNS	automatico	pendente	2026-03-28 03:16:48.023178	\N
737	639	tpRubr	Desconto	2	ESTORNO DE PAGAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
738	64	tpRubr	Vencimento	1	ADIC. NOTURNO C/50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
739	640	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
740	641	tpRubr	Desconto	2	DESC. I.N.S.S. (FÉRIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
741	642	tpRubr	Desconto	2	DESC INSALUBRIDADE INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
742	643	tpRubr	Desconto	2	DESC. PROGRAMA ASSIST. FAMILIAR (PAF) M/ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
743	644	tpRubr	Desconto	2	DESC. CONTRIB. ASSISTENCIAL 13 SAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
744	645	tpRubr	Desconto	2	DESCONTO DE 2 VIA VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
745	646	tpRubr	Desconto	2	DESC. MENS. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
746	647	tpRubr	Desconto	2	DESC. EMPRESTIMO ZIPDIN	automatico	pendente	2026-03-28 03:16:48.023178	\N
747	648	tpRubr	Desconto	2	DESC. CONTRIB. SOCIAL SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
748	649	tpRubr	Desconto	2	DESC. CONTRIB. SOCIAL SINDICAL MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
749	65	tpRubr	Vencimento	1	ADIC. NOTURNO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
750	650	tpRubr	Vencimento	1	COMPL AJ COMPUSORIA MP936	automatico	pendente	2026-03-28 03:16:48.023178	\N
751	651	tpRubr	Desconto	2	REDUCAO JORNADA COVID - 25%	automatico	pendente	2026-03-28 03:16:48.023178	\N
752	652	tpRubr	Desconto	2	REDUCAO JORNADA COVID - 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
753	653	tpRubr	Desconto	2	REDUCAO JORNADA COVID - 70%	automatico	pendente	2026-03-28 03:16:48.023178	\N
754	654	tpRubr	Vencimento	1	FATURAMENTO DE SUSPENSAO - GARCOM/GARCONETE	automatico	pendente	2026-03-28 03:16:48.023178	\N
755	655	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
756	656	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
757	657	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA EM FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
758	658	tpRubr	Desconto	2	DESC. PENSAO ALIM S/ Férias	automatico	pendente	2026-03-28 03:16:48.023178	\N
759	659	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA ACORDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
760	66	tpRubr	Vencimento	1	ADIC. NOTURNO MES ANT 20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
761	660	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA MES ANTERIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
762	661	tpRubr	Vencimento	1	REEMB. VT-SALVADORCARD	automatico	pendente	2026-03-28 03:16:48.023178	\N
763	662	tpRubr	Vencimento	1	PENSAO INDENIZATORIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
764	663	tpRubr	Vencimento	1	REEMB. VT-SALVADORCARD NAO CARREGADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
765	664	tpRubr	Desconto	2	DESC. VALE ALIMENTACAO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
766	665	tpRubr	Vencimento	1	DIF CCT COMPUS MP936	automatico	pendente	2026-03-28 03:16:48.023178	\N
767	666	tpRubr	Vencimento	1	COMPL AJ COMPUSORIA MP936	automatico	pendente	2026-03-28 03:16:48.023178	\N
768	667	tpRubr	Desconto	2	DESC. MENS. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
769	668	tpRubr	Vencimento	1	DIF. CCT 2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
770	669	tpRubr	Vencimento	1	ADIC. NOTURNO C/39%	automatico	pendente	2026-03-28 03:16:48.023178	\N
771	67	tpRubr	Vencimento	1	DIF. ADIC. INSALUBRIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
772	670	tpRubr	Vencimento	1	ADIC. NOTURNO C/39%	automatico	pendente	2026-03-28 03:16:48.023178	\N
773	671	tpRubr	Desconto	2	DESC. VALE-TRANSPORTE NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
774	672	tpRubr	Desconto	2	DESC. VALE-TRANSPORTE 6%	automatico	pendente	2026-03-28 03:16:48.023178	\N
775	673	tpRubr	Desconto	2	DESC. CARTAO BHBUS / OTIMO	automatico	pendente	2026-03-28 03:16:48.023178	\N
776	674	tpRubr	Desconto	2	DESC. DEV VT RED TARIFA TRANSPORTES	automatico	pendente	2026-03-28 03:16:48.023178	\N
777	675	tpRubr	Vencimento	1	ANTEC INST REDUCAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
778	676	tpRubr	Desconto	2	DESC. ADIANT. VALE-TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
779	677	tpRubr	Desconto	2	DESC. VALE TRANSP. NAO UTILIZADO MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
780	678	tpRubr	Desconto	2	DESC. VALE-TRANSPORTE 06% - 02/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
781	679	tpRubr	Desconto	2	DESC. VALE-TRANSPORTE MES ANTERIOR 6%	automatico	pendente	2026-03-28 03:16:48.023178	\N
782	68	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE 11/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
783	680	tpRubr	Desconto	2	DESC. VALE-TRANSP NAO UTILIZADO ATESTADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
784	681	tpRubr	Vencimento	1	SOBRE AVISO 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
785	682	tpRubr	Vencimento	1	HORAS EXTRAS INSAL 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
786	683	tpRubr	Vencimento	1	DIF CCT 2021 - FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
787	684	tpRubr	Vencimento	1	ADIC. NOTURNO C/20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
788	685	tpRubr	Desconto	2	DESC. ADIANTAMENTO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
789	686	tpRubr	Desconto	2	DESC. AVISO PREVIO NAO TRABALHADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
790	687	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
791	688	tpRubr	Desconto	2	DESC. CONVENIO ODONTOLOGICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
792	689	tpRubr	Desconto	2	DESC. VT DIF CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
793	69	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE MES ANTER	automatico	pendente	2026-03-28 03:16:48.023178	\N
794	690	tpRubr	Desconto	2	DESC. VA E VR DIF CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
795	691	tpRubr	Desconto	2	DESC. ANTECIPACAO VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
796	692	tpRubr	Desconto	2	DESC. 2 VIA CARTAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
797	693	tpRubr	Desconto	2	DESC. EMPRESTIMO FOLHA PGTO ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
798	694	tpRubr	Desconto	2	DESC. HORA EXTRA PAGO A MAIOR / DSR	automatico	pendente	2026-03-28 03:16:48.023178	\N
799	695	tpRubr	Vencimento	1	DESC. HORAS NORMAIS DEBITO	automatico	pendente	2026-03-28 03:16:48.023178	\N
800	696	tpRubr	Vencimento	1	ABONO PECUNIARIO RODOVIARIOS 2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
801	697	tpRubr	Vencimento	1	ADIC. NOTURNO C/39% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
802	698	tpRubr	Desconto	2	DESC. ADIANT. COMISSOES	automatico	pendente	2026-03-28 03:16:48.023178	\N
803	699	tpRubr	Desconto	2	DESC. ADIANT. DESPESAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
804	7	tpRubr	Vencimento	1	COMISSAO MOVEIS - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
805	70	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
806	700	tpRubr	Desconto	2	DESC. F.G.T.S. DEPOSITO RESCISAO - G.R.F.C.	automatico	pendente	2026-03-28 03:16:48.023178	\N
807	701	tpRubr	Desconto	2	DESC. 2ª VIA CARTAO ALELO	automatico	pendente	2026-03-28 03:16:48.023178	\N
808	702	tpRubr	Desconto	2	DESC. 2ª VIA CARTAO REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
809	703	tpRubr	Desconto	2	DESC. 2ª VIA CARTAO RIO CARD	automatico	pendente	2026-03-28 03:16:48.023178	\N
810	704	tpRubr	Desconto	2	DESC. 2ª VIA CRACHÁ MAGNETICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
811	705	tpRubr	Desconto	2	2ª VIA CARTEIRINHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
812	706	tpRubr	Desconto	2	DESC. ABONO PAGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
813	707	tpRubr	Desconto	2	DESC. ACERTO PENDENCIAS PREST CONTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
814	708	tpRubr	Desconto	2	DESC. AJUDA CUSTO NAO UTILIZAD	automatico	pendente	2026-03-28 03:16:48.023178	\N
815	709	tpRubr	Desconto	2	DESC. AJUSTE DESP DE VIAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
816	71	tpRubr	Vencimento	1	AJUD FILHO DEFICIENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
817	710	tpRubr	Desconto	2	DESC. ALIMENTACAO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
818	711	tpRubr	Desconto	2	DESC. ALOJAMENTO(USO FUTURO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
819	712	tpRubr	Desconto	2	DESC. BENEFICIO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
820	713	tpRubr	Desconto	2	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
821	714	tpRubr	Desconto	2	DESC. BENEFÍCIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
822	715	tpRubr	Desconto	2	DESC. PAGOS ANTECIPADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
823	716	tpRubr	Desconto	2	DESC. CELULAR NAO DEVOLVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
824	717	tpRubr	Desconto	2	DESC. COMBUSTIVEL UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
825	718	tpRubr	Desconto	2	DESC. CONVENIO FARMACIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
826	719	tpRubr	Desconto	2	DESC. CRACHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
827	72	tpRubr	Vencimento	1	DIF - AJUD FILHO DEFICIENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
828	720	tpRubr	Desconto	2	DESC. FARMACIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
829	721	tpRubr	Desconto	2	DESC. FORNECIMENTO CAFE	automatico	pendente	2026-03-28 03:16:48.023178	\N
830	722	tpRubr	Desconto	2	DESC. FRANQUIA VEICULO	automatico	pendente	2026-03-28 03:16:48.023178	\N
831	723	tpRubr	Desconto	2	DESC. MAU USO MATERIAL EMPRESA	automatico	pendente	2026-03-28 03:16:48.023178	\N
832	724	tpRubr	Desconto	2	DESC. MULTA DE TRANSITO	automatico	pendente	2026-03-28 03:16:48.023178	\N
833	725	tpRubr	Desconto	2	DESC. PENDENCIAS PREST CONTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
834	726	tpRubr	Desconto	2	DESC. PREJUIZO CAUSADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
835	727	tpRubr	Desconto	2	DESC. REFEIÇÃO MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
836	728	tpRubr	Desconto	2	DESC. REFEICOES	automatico	pendente	2026-03-28 03:16:48.023178	\N
837	729	tpRubr	Desconto	2	DESC. SEGURO DE VIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
838	73	tpRubr	Vencimento	1	ADIC. NOTURNO - 01/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
839	730	tpRubr	Desconto	2	DESC. SMARTPHONE NAO DEVOLVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
840	731	tpRubr	Desconto	2	DESC. TARIFA BANCARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
841	732	tpRubr	Desconto	2	DESC. TAXA ADESAO PROMED MG	automatico	pendente	2026-03-28 03:16:48.023178	\N
842	733	tpRubr	Desconto	2	DESC. UNIFORME	automatico	pendente	2026-03-28 03:16:48.023178	\N
843	734	tpRubr	Desconto	2	DESC. USO CELULAR DANIFICADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
844	735	tpRubr	Vencimento	1	HORAS EXTRAS INSAL 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
845	736	tpRubr	Desconto	2	DESC. VALE	automatico	pendente	2026-03-28 03:16:48.023178	\N
846	737	tpRubr	Desconto	2	DESC. VALE COMPRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
847	738	tpRubr	Vencimento	1	ADIC.INSALUB.ACORDO TRAB	automatico	pendente	2026-03-28 03:16:48.023178	\N
848	739	tpRubr	Desconto	2	CONTRIB. ASSIST- PROCESSO	automatico	pendente	2026-03-28 03:16:48.023178	\N
849	74	tpRubr	Vencimento	1	DIF. DISSIDIO 2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
850	740	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50	automatico	pendente	2026-03-28 03:16:48.023178	\N
851	741	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
852	742	tpRubr	Vencimento	1	DIF. CCT 2022	automatico	pendente	2026-03-28 03:16:48.023178	\N
853	743	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50	automatico	pendente	2026-03-28 03:16:48.023178	\N
854	744	tpRubr	Vencimento	1	H EXTRAS 50% NOT22,50 MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
855	745	tpRubr	Vencimento	1	H EXTRAS 100% NOT 22,50 - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
856	746	tpRubr	Vencimento	1	DIFERENCA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
857	747	tpRubr	Vencimento	1	DIF. ADIC. INSALUBRIDADE CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
858	748	tpRubr	Desconto	2	DESC. JUDICIAL - 2	automatico	pendente	2026-03-28 03:16:48.023178	\N
859	749	tpRubr	Vencimento	1	ADIC. NOTURNO 22,50% - MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
860	75	tpRubr	Vencimento	1	DIF. HORAS EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
861	750	tpRubr	Vencimento	1	ADIC. NOTURNO C/39% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
862	751	tpRubr	Desconto	2	DESC. CESTA BASICA NAO UTILIZADA	automatico	pendente	2026-03-28 03:16:48.023178	\N
863	752	tpRubr	Vencimento	1	DIF. 1/3 DAS FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
864	753	tpRubr	Vencimento	1	REEMB VALE REFEICAO/ ALIMENTACAO - HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
865	754	tpRubr	Vencimento	1	DIF ABONO DE FERIAS ARTº 143 (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
866	755	tpRubr	Vencimento	1	REEMB. VALE TRANSPORTE - HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
867	756	tpRubr	Vencimento	1	DIF 1/3 S/ABONO FERIAS ARTº 143 (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
868	757	tpRubr	Desconto	2	DESC. CONTRIB. DE NATUREZA PREVIDENCIARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
869	758	tpRubr	Desconto	2	DESC. CONTRIB. DE NATUREZA PREVIDENCIARIA -MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
870	759	tpRubr	Desconto	2	DESC. AUX. DOENÇA INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
871	76	tpRubr	Vencimento	1	DIF. HORAS EXTRAS DISSIDIO 04/2010	automatico	pendente	2026-03-28 03:16:48.023178	\N
872	760	tpRubr	Desconto	2	DESC. SALDO DE QUITACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
873	761	tpRubr	Desconto	2	DESC. TAXA NEGOCIAL LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
874	762	tpRubr	Desconto	2	DESC. MENSALIDADE SINDICAL - BA	automatico	pendente	2026-03-28 03:16:48.023178	\N
875	763	tpRubr	Desconto	2	DESC. MENSALIDADE SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
876	764	tpRubr	Vencimento	1	REEMBOLSO DESC. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
877	765	tpRubr	Desconto	2	DESC. ASSIST. ODONT. MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
878	766	tpRubr	Desconto	2	DESC. ASSIST. ODONT. DEP. MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
879	767	tpRubr	Desconto	2	DESC. PAGTO. SALARIO INDEV.	automatico	pendente	2026-03-28 03:16:48.023178	\N
880	768	tpRubr	Vencimento	1	ADIC. 13º SALARIO S/AVISO PREVIO (Lei 12.506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
881	769	tpRubr	Desconto	2	DESC. VALE REFEICAO NAO UTILIZADO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
882	77	tpRubr	Vencimento	1	DIF. MINIMO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
883	770	tpRubr	Desconto	2	DESC. ADIANT. VALE REFEIÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
884	771	tpRubr	Desconto	2	DESC. VALE REFEICAO NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
885	772	tpRubr	Desconto	2	DESC. CESTA BASICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
886	773	tpRubr	Desconto	2	DESC. VALE REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
887	774	tpRubr	Desconto	2	DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
888	775	tpRubr	Desconto	2	DESC. ASSIST. ODONTOLOGICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
889	776	tpRubr	Desconto	2	DESC. VALE ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
890	777	tpRubr	Desconto	2	DESC. OUTROS BENEFICIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
891	778	tpRubr	Desconto	2	DESC. VALE ALIMENTACAO NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
892	779	tpRubr	Desconto	2	DESC. ASSIST. MEDICA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
893	78	tpRubr	Vencimento	1	HORAS NOTURNAS 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
894	780	tpRubr	Desconto	2	DESC. ASSIST. MEDICA REF. PENSÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
895	781	tpRubr	Vencimento	1	ADIC. FÉRIAS S/AVISO PREVIO (Lei 12.506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
896	782	tpRubr	Vencimento	1	1/3 ADIC. FERIAS S/AVISO PREVIO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
897	783	tpRubr	Vencimento	1	HORAS EXTRAS 115% MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
898	784	tpRubr	Desconto	2	DESC. VT DIF SAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
899	785	tpRubr	Vencimento	1	ABONO PECUNIARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
900	786	tpRubr	Vencimento	1	ADIANTAMENTO - (PGTO FÉRIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
901	787	tpRubr	Desconto	2	DESC SALARIO FAMILIA INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
902	788	tpRubr	Desconto	2	DESC. CARTAO SALARIO - ADMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
903	789	tpRubr	Desconto	2	DESC. CARTAO SALARIO - DEMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
904	79	tpRubr	Vencimento	1	HORAS NOTURNAS REDUZIDAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
905	790	tpRubr	Desconto	2	DESC. SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
906	791	tpRubr	Vencimento	1	MULTA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
907	792	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE (SEM INCIDENCIA)	automatico	pendente	2026-03-28 03:16:48.023178	\N
908	793	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE (SEM INCIDENCIA) MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
909	794	tpRubr	Vencimento	1	REEMBOLSO SEGURO DE VIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
910	795	tpRubr	Vencimento	1	ADIC. NOTURNO C/35% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
911	796	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
912	797	tpRubr	Vencimento	1	ADIANTAMENTO - (PGTO FÉRIAS - COM INCIDENCIA)	automatico	pendente	2026-03-28 03:16:48.023178	\N
913	798	tpRubr	Vencimento	1	ADIC. PERIC. S/AVISO PREVIO INDENIZADO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
914	799	tpRubr	Desconto	2	DESC. DSR HE - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
915	8	tpRubr	Vencimento	1	SALARIO NORMATIVO - GER	automatico	pendente	2026-03-28 03:16:48.023178	\N
916	80	tpRubr	Vencimento	1	HORAS NOTURNAS REDUZIDAS 35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
917	800	tpRubr	Vencimento	1	ADIC. PERIC. S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
918	801	tpRubr	Vencimento	1	DIFERENCA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
919	802	tpRubr	Vencimento	1	ADIC. PERIC. S/FERIAS PROPORCIONAIS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
920	803	tpRubr	Vencimento	1	ADIC. PERIC. S/13º SALARIO PROP. S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
921	804	tpRubr	Vencimento	1	SOBRE AVISO- MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
922	805	tpRubr	Vencimento	1	ADIC. PERIC. S/FERIAS S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
923	806	tpRubr	Desconto	2	DESC. EMPRESTIMO NEON	automatico	pendente	2026-03-28 03:16:48.023178	\N
924	807	tpRubr	Desconto	2	DESC. FERIAS PAGAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
925	808	tpRubr	Vencimento	1	GRATIFICACAO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
926	809	tpRubr	Desconto	2	DESC ADIC. PERICULOSIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
927	81	tpRubr	Vencimento	1	HORAS REDUZIDAS ADIC. NOT MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
928	810	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
929	811	tpRubr	Vencimento	1	ACUMULO DE FUNCAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
930	812	tpRubr	Vencimento	1	REEMBOLSO DE HORAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
931	813	tpRubr	Vencimento	1	DIF. SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
932	814	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE SOBRE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
933	815	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
934	816	tpRubr	Desconto	2	DESC. 1/3 FERIAS PAGAS A MAIS CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
935	817	tpRubr	Vencimento	1	DEMONSTRATIVO PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
936	818	tpRubr	Desconto	2	DESC. FERIAS PAGAS A MAIS CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
937	819	tpRubr	Desconto	2	DESC. CB DIF CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
938	82	tpRubr	Vencimento	1	HORAS REDUZIDAS ADIC. NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
939	820	tpRubr	Vencimento	1	SALARIO DIA (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
940	821	tpRubr	Vencimento	1	HORAS NORMAIS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
941	822	tpRubr	Vencimento	1	D.S.R. S/FERIADO - HS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
942	823	tpRubr	Vencimento	1	FERIAS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
943	824	tpRubr	Vencimento	1	1/3 FERIAS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
944	825	tpRubr	Vencimento	1	13º SALÁRIO (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
945	826	tpRubr	Vencimento	1	INDENIZACAO ARTº 480	automatico	pendente	2026-03-28 03:16:48.023178	\N
946	827	tpRubr	Desconto	2	DESCONTO JUDICIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
947	828	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
948	829	tpRubr	Desconto	2	PROCESSO TRAB	automatico	pendente	2026-03-28 03:16:48.023178	\N
949	83	tpRubr	Vencimento	1	HORAS REDUZIDAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
950	830	tpRubr	Desconto	2	DESC. ADTO (PGTO FÉRIAS - COM INCIDENCIA)	automatico	pendente	2026-03-28 03:16:48.023178	\N
951	831	tpRubr	Vencimento	1	SALARIO MATERNIDADE (MES ANTERIOR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
952	832	tpRubr	Vencimento	1	DIF. VALE ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
953	833	tpRubr	Desconto	2	DESC. HORAS PAGAS A MAIS NO MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
954	834	tpRubr	Vencimento	1	HORAS EXTRAS 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
955	835	tpRubr	Vencimento	1	HORAS EXTRAS 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
956	836	tpRubr	Vencimento	1	ADIC. NOTURNO C/20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
957	837	tpRubr	Desconto	2	DESC. FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
958	838	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA EM FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
959	839	tpRubr	Desconto	2	DESC. FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
960	84	tpRubr	Vencimento	1	NONA HORA	automatico	pendente	2026-03-28 03:16:48.023178	\N
961	840	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
962	841	tpRubr	Desconto	2	DESC. ATRASOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
963	842	tpRubr	Desconto	2	DESC. CONTRIB. NEGOCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
964	843	tpRubr	Desconto	2	DESC AD NOT INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
965	844	tpRubr	Vencimento	1	FGTS COMPLEMENTAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
966	845	tpRubr	Vencimento	1	REEMB. DESPESAS - INVISIVEL	automatico	pendente	2026-03-28 03:16:48.023178	\N
967	846	tpRubr	Desconto	2	DESC. ADIANT. DESPESAS - INVISIVEL	automatico	pendente	2026-03-28 03:16:48.023178	\N
968	847	tpRubr	Vencimento	1	H.EXTRA  NOTURNO C/100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
969	848	tpRubr	Vencimento	1	ACUMULO DE FUNCAO MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
970	849	tpRubr	Vencimento	1	DIF. PAGTO CONDUCAO VAN	automatico	pendente	2026-03-28 03:16:48.023178	\N
971	85	tpRubr	Vencimento	1	HORAS EXTRAS REF.DIF 50 x100	automatico	pendente	2026-03-28 03:16:48.023178	\N
972	850	tpRubr	Vencimento	1	ADIC. NOTURNO C/100% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
973	851	tpRubr	Vencimento	1	REEMB. I.N.S.S.	automatico	pendente	2026-03-28 03:16:48.023178	\N
974	852	tpRubr	Vencimento	1	HORAS EXTRAS 50% C/ INSALUBRIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
975	853	tpRubr	Vencimento	1	HORAS EXTRAS 100% C/ INSALUBRIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
976	854	tpRubr	Desconto	2	DESC. CREDENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
977	855	tpRubr	Vencimento	1	ADIANTAMENTO DE SALARIOS COM INCIDÊNCIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
978	856	tpRubr	Vencimento	1	PRORROGAÇÃO SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
979	857	tpRubr	Desconto	2	DESC. ATRASO/FALTA HORAS MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
980	858	tpRubr	Vencimento	1	HORAS NORMAIS MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
981	859	tpRubr	Vencimento	1	HORAS EXTRAS 100% C/ INSALUBRIDADE MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
982	86	tpRubr	Vencimento	1	HORA FICTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
983	860	tpRubr	Vencimento	1	HORAS EXTRAS 50% C/ INSALUBRIDADE MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
984	861	tpRubr	Desconto	2	DESC. D.S.R. S/FALTAS (HORAS) MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
985	862	tpRubr	Vencimento	1	ADIC. NOTURNO C/20% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
986	863	tpRubr	Vencimento	1	ADIC. NOTURNO C/50% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
987	864	tpRubr	Vencimento	1	ADIC. INSALUBRIDADE SOBRE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
988	865	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
989	866	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
990	867	tpRubr	Vencimento	1	DEV. ATRASO/D.S.R. HORAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
991	868	tpRubr	Desconto	2	DEV. FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
992	869	tpRubr	Vencimento	1	REEMBOLSO DESC. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
993	87	tpRubr	Vencimento	1	HORA FICTA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
994	870	tpRubr	Vencimento	1	ADICIONAL DE ESTIMULO	automatico	pendente	2026-03-28 03:16:48.023178	\N
995	871	tpRubr	Vencimento	1	H.EXTRA  NOTURNO C/100% MÊS ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
996	872	tpRubr	Vencimento	1	HORAS EXTRAS 50% - DIF	automatico	pendente	2026-03-28 03:16:48.023178	\N
997	873	tpRubr	Vencimento	1	REEMB. 6% VALE TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
998	874	tpRubr	Vencimento	1	DEV. FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
999	875	tpRubr	Vencimento	1	DEV. D.S.R FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1000	876	tpRubr	Vencimento	1	DIF H.E. 50% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1001	877	tpRubr	Vencimento	1	DIF H.E. 100% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1002	878	tpRubr	Desconto	2	DESC. ATRASOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1003	879	tpRubr	Vencimento	1	ADIC. SALARIO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1004	88	tpRubr	Vencimento	1	HORA NOTURNA REDUZIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1005	880	tpRubr	Vencimento	1	H E 50% - ART. 71 MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1006	881	tpRubr	Vencimento	1	PARTICIPAÇÃO DE LUCRO/RESULTADOS 2023	automatico	pendente	2026-03-28 03:16:48.023178	\N
1007	882	tpRubr	Vencimento	1	REEMB. DESC. VALE REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1008	883	tpRubr	Desconto	2	DESC. CONTRIB. NEGOCIAL MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1009	884	tpRubr	Vencimento	1	ABONO - SEERC	automatico	pendente	2026-03-28 03:16:48.023178	\N
1010	885	tpRubr	Vencimento	1	PREMIO ASSIDUIDADE MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1011	886	tpRubr	Desconto	2	DESC. CONTRIB. NEGOCIAL SINTRAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1012	887	tpRubr	Desconto	2	DESC. FALTAS (Horas)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1013	888	tpRubr	Desconto	2	DESC. D.S.R. S/FALTAS (Horas)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1014	889	tpRubr	Vencimento	1	AUX. DOENÇA MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1015	89	tpRubr	Vencimento	1	HORA REDUZIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1016	890	tpRubr	Desconto	2	DESC. PAGTO. SALARIO INDEV. MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1017	891	tpRubr	Vencimento	1	REEMB VALE LANCHE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1018	892	tpRubr	Vencimento	1	REEMB. EXAME RETORNO AO TRABALHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1019	893	tpRubr	Desconto	2	DESC. VALE-TRANSPORTE 6% MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1020	894	tpRubr	Desconto	2	DESC. ASSIST. ODONTOLOGICA MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1021	895	tpRubr	Desconto	2	DESC. ASSIST. ODONTO. DEPENDENTE MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1022	896	tpRubr	Desconto	2	DESC. CO PARTICIPACAO A.M. Mês Anterior	automatico	pendente	2026-03-28 03:16:48.023178	\N
1023	897	tpRubr	Desconto	2	DESC. ANTECIPACAO VA E VR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1024	898	tpRubr	Vencimento	1	MULTA CCT CLÁSULA 6ª - 03/2024	automatico	pendente	2026-03-28 03:16:48.023178	\N
1025	899	tpRubr	Desconto	2	DESC. PAGTO. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1026	9	tpRubr	Vencimento	1	SALARIO NORMATIVO -VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
1027	90	tpRubr	Vencimento	1	HORAS A COMPENSAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1028	900	tpRubr	Desconto	2	VALE LANCHE NAO UTILIZADO MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1029	901	tpRubr	Vencimento	1	BENEFICIOS MENSAIS E DIARIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1030	902	tpRubr	Vencimento	1	UNIFORME	automatico	pendente	2026-03-28 03:16:48.023178	\N
1031	903	tpRubr	Vencimento	1	MAO DE OBRA ENCARREGADO BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1032	904	tpRubr	Vencimento	1	MAO DE OBRA ALMOXARIFE BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1033	905	tpRubr	Vencimento	1	MAO DE OBRA AUXILIAR OPER BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1034	906	tpRubr	Vencimento	1	REPOSIÇÃO PROFISSIONAL AUSENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1035	907	tpRubr	Vencimento	1	FATURAMENTO DE DIARIAS, DESLOCAMENTOS E PASSAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1036	908	tpRubr	Vencimento	1	CUSTO OPERACIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1037	909	tpRubr	Vencimento	1	RECRUTAMENTO E SELECAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1038	91	tpRubr	Vencimento	1	HORAS A DESC. FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1039	910	tpRubr	Vencimento	1	MAO DE OBRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1040	911	tpRubr	Vencimento	1	FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1041	912	tpRubr	Vencimento	1	SUBSTITUICAO DE FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1042	913	tpRubr	Vencimento	1	FATURAMENTO DE VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1043	914	tpRubr	Vencimento	1	FATURAMENTO DE VA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1044	915	tpRubr	Vencimento	1	FATURAMENTO DE SEGURO DE VIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1045	916	tpRubr	Vencimento	1	DISSIDIO CONFORME CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1046	917	tpRubr	Vencimento	1	REAJUSTE CONFORME CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1047	918	tpRubr	Vencimento	1	FATURAMENTO DE RESCISÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1048	919	tpRubr	Vencimento	1	FATURAMENTO DE FALTAS LEGAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1049	92	tpRubr	Vencimento	1	HORAS ABONADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1050	920	tpRubr	Vencimento	1	FATURAMENTO DE PAF	automatico	pendente	2026-03-28 03:16:48.023178	\N
1051	921	tpRubr	Vencimento	1	FATURAMENTO DE MATERIAL DE LIMPEZA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1052	922	tpRubr	Vencimento	1	FATURAMENTO DE REEMBOLSO DE ATESTADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1053	923	tpRubr	Vencimento	1	FATURAMENTO DE 13º SALARIO 1º PARCELA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1054	924	tpRubr	Vencimento	1	FATURAMENTO DE 13º SALARIO 2º PARCELA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1055	925	tpRubr	Vencimento	1	FATURAMENTO DE HORAS EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1056	926	tpRubr	Vencimento	1	FATURAMENTO DE DIARIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1057	927	tpRubr	Vencimento	1	MOTORISTA EVENTUAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1058	9276	tpRubr	Vencimento	1	VALE TRANSPORTE (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1059	9277	tpRubr	Vencimento	1	VALE REFEICAO (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1060	9278	tpRubr	Vencimento	1	CESTA BASICA (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1061	9279	tpRubr	Vencimento	1	ASSISTENCIA MEDICA (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1062	928	tpRubr	Vencimento	1	REPACTUACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1063	9281	tpRubr	Vencimento	1	ASSISTENCIA ODONTOLOGICA (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1064	9284	tpRubr	Vencimento	1	VALE ALIMENTACAO (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1065	9285	tpRubr	Vencimento	1	BENEFICIO OUTROS (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1066	9286	tpRubr	Vencimento	1	BENEFICIO INFORMADO (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1067	9287	tpRubr	Vencimento	1	BENEFICIO PROMOCAO (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1068	929	tpRubr	Vencimento	1	FATURAMENTO DE ART-RRT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1069	93	tpRubr	Vencimento	1	F.G.T.S. MULTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1070	930	tpRubr	Vencimento	1	REPACTUAÇÃO DE CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1071	931	tpRubr	Vencimento	1	REPACTUAÇÃO DE CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1072	932	tpRubr	Vencimento	1	MAO DE OBRA - 1/2 OFICIAL BORRACHEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1073	933	tpRubr	Vencimento	1	MAO DE OBRA - 1/2 OFICIAL MECANICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1074	934	tpRubr	Vencimento	1	AJUDA DE CUSTO - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1075	935	tpRubr	Vencimento	1	DEMONSTRATIVO DE HORAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1076	936	tpRubr	Vencimento	1	MAO DE OBRA - 1/2 OFICIAL ELETRICISTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1077	937	tpRubr	Vencimento	1	DEMONSTRATIVO DE HORAS EXTRAS 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1078	938	tpRubr	Vencimento	1	DIFERENCA DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1079	939	tpRubr	Vencimento	1	DEMONSTRATIVO DE HORAS EXTRAS 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1080	94	tpRubr	Vencimento	1	H EXTRAS DIF 50% X 60%- MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1081	940	tpRubr	Vencimento	1	GRATIFICAÇÃO MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1082	941	tpRubr	Vencimento	1	DEMONSTRATIVO DE ADICIONAL NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1083	942	tpRubr	Vencimento	1	PAGTO. V. T - NAO LIQUIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1084	943	tpRubr	Vencimento	1	MULTA CCT CLÁSULA 6ª - 04/2024	automatico	pendente	2026-03-28 03:16:48.023178	\N
1085	944	tpRubr	Vencimento	1	DEMONSTRATIVO DE SOBREAVISO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1086	945	tpRubr	Vencimento	1	MAO DE OBRA - GARCON  E GARCONETE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1087	946	tpRubr	Vencimento	1	DIFERENÇA - PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1088	947	tpRubr	Vencimento	1	MAO DE OBRA - COPEIRO E COPEIRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1089	948	tpRubr	Vencimento	1	MULTA POR ATRASO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1090	949	tpRubr	Desconto	2	DESC. I.N.S.S. MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1091	95	tpRubr	Vencimento	1	HORAS EXTRAS 06/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1092	950	tpRubr	Desconto	2	DIF. ASSISTENCIA MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1093	951	tpRubr	Desconto	2	DESCONTO REF. FALTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1094	952	tpRubr	Desconto	2	DESCONTO REF. RECESSO FORENSE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1095	953	tpRubr	Desconto	2	DESCONTO DE VR REF. RECESSO FORENSE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1096	954	tpRubr	Desconto	2	DIFERENÇA DE DISSIDIO CONFORME CCT 2016	automatico	pendente	2026-03-28 03:16:48.023178	\N
1097	955	tpRubr	Desconto	2	DESC. ADIC. NOTURNO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1098	956	tpRubr	Desconto	2	DESCONTO REF. ATRASOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1099	957	tpRubr	Desconto	2	DESCONTO DE 7 DIAS REF. REAJUSTE CONTRATUAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1100	958	tpRubr	Desconto	2	DESCONTO HORAS REDUZIDAS ADIC. NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1101	959	tpRubr	Desconto	2	DESCONTO DE DIFERENÇA DE REPACTUAÇÃO DE VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1102	96	tpRubr	Vencimento	1	HORAS EXTRAS 07/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1103	960	tpRubr	Desconto	2	DESCONTO REF. FALTAS - 1/2 OFICIAL BORRACHEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1104	961	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1105	962	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA EM FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1106	963	tpRubr	Desconto	2	DESCONTO REF. FALTAS - 1/2 OFICIAL MECANICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1107	964	tpRubr	Desconto	2	DESC. PENSAO ALIMENTICIA S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1108	965	tpRubr	Desconto	2	DESCONTO REF. FALTAS - GARCON E GARCONETE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1109	966	tpRubr	Vencimento	1	HORAS EXTRAS 30%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1110	967	tpRubr	Vencimento	1	HORAS EXTRAS 30% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1111	968	tpRubr	Desconto	2	DESCONTO REF. FALTAS - 1/2 OFICIAL ELETRICISTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1112	969	tpRubr	Desconto	2	DESCONTO REF. RECESSO FORENSE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1113	97	tpRubr	Vencimento	1	HORAS EXTRAS 08/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1114	970	tpRubr	Vencimento	1	PARTICIPACAO LUCROS/RESULTADOS SÓCIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1115	971	tpRubr	Desconto	2	DESC.CESTA BASICA SOCIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1116	972	tpRubr	Vencimento	1	SALARIO DIA (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1117	973	tpRubr	Vencimento	1	FERIAS (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1118	974	tpRubr	Vencimento	1	1/3 FERIAS (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1119	975	tpRubr	Desconto	2	DESCONTO REF. FALTAS - COPEIRO E COPEIRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1120	976	tpRubr	Desconto	2	DESCONTO RECESSO FORENSE - GARCON E GARCONETE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1121	977	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE S/ HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1122	978	tpRubr	Vencimento	1	ADIC. PERICULOSIDADE SOBRE HORAS EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1123	979	tpRubr	Desconto	2	DESCONTO RECESSO FORENSE - COPEIRO E COPEIRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1124	98	tpRubr	Vencimento	1	HORAS EXTRAS 09/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1125	980	tpRubr	Desconto	2	DESCONTO REF. FALTAS ENCARREGADO BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1126	981	tpRubr	Desconto	2	DESCONTO REF. FALTAS ALMOXARIFE BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1127	982	tpRubr	Desconto	2	DESCONTO REF. FALTAS AUXILIAR OPER BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1128	983	tpRubr	Vencimento	1	DIFERENCA FERIAS (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1129	984	tpRubr	Vencimento	1	HORA CORRIDA REFEICAO 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1130	985	tpRubr	Vencimento	1	HORA CORRIDA REFEICAO 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1131	986	tpRubr	Vencimento	1	DIFERENCA ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1132	987	tpRubr	Vencimento	1	DIFERENCA 1/3 FERIAS (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1133	988	tpRubr	Vencimento	1	*** BASE IRRF ***	automatico	pendente	2026-03-28 03:16:48.023178	\N
1134	989	tpRubr	Desconto	2	DESC. PGTO ASSIDUIDADE MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1135	99	tpRubr	Vencimento	1	HORAS EXTRAS 10/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1136	990	tpRubr	Vencimento	1	REEMB. FALTAS (HORAS) - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1137	991	tpRubr	Vencimento	1	REEMB. FALTAS D.S.R (HORAS) - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1138	992	tpRubr	Vencimento	1	REEMB. ATRASO (HORAS) - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1139	993	tpRubr	Vencimento	1	ADICIONAL DE ESTIMULO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1140	994	tpRubr	Vencimento	1	PARCELAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1141	995	tpRubr	Vencimento	1	LICENCA REMUNERADA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1142	996	tpRubr	Vencimento	1	F.G.T.S. PAGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1143	997	tpRubr	Desconto	2	DESC. MULTA 40% - REITEGRAÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1144	998	tpRubr	Vencimento	1	PARCELAMENTO 2	automatico	pendente	2026-03-28 03:16:48.023178	\N
1145	999	tpRubr	Vencimento	1	PARCELAMENTO 3	automatico	pendente	2026-03-28 03:16:48.023178	\N
1146	951	codIncPisPasep	0	00	DESCONTO REF. FALTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1147	346	codIncPisPasep	0	00	DIFERENCA DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1148	525	codIncPisPasep	0	00	DESC. PGTO. ANTECIPADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1149	95	codIncPisPasep	0	00	HORAS EXTRAS 06/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1150	263	codIncPisPasep	0	00	MULTA CLAUSULA DECIMA SEXTA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1151	863	codIncPisPasep	0	00	ADIC. NOTURNO C/50% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1152	319	codIncPisPasep	0	00	REEMB. CONSULTA. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1153	391	codIncPisPasep	0	00	SALARIO MATERNIDADE (antigo)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1154	1006	codIncPisPasep	0	00	ADIC. NOTURNO C/20% - (HORA EXTRA 100%) - MES ANTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1155	799	codIncPisPasep	0	00	DESC. DSR HE - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1156	980	codIncPisPasep	0	00	DESCONTO REF. FALTAS ENCARREGADO BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1157	531	codIncPisPasep	0	00	DESC. VA/ VR NAO UTILIZADO ATESTADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1158	781	codIncPisPasep	0	00	ADIC. FÉRIAS S/AVISO PREVIO (Lei 12.506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1159	559	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1160	214	codIncPisPasep	0	00	ACERTO DE FOLHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1161	74	codIncPisPasep	0	00	DIF. DISSIDIO 2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
1162	719	codIncPisPasep	0	00	DESC. CRACHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1163	445	codIncPisPasep	0	00	DIF. OUTROS BENEFICIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1164	866	codIncPisPasep	0	00	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1165	476	codIncPisPasep	0	00	TRIBUTO S/SALARIO (NÃO UTILIZAR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1166	390	codIncPisPasep	0	00	SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1167	225	codIncPisPasep	0	00	DIF HE CCT 2018	automatico	pendente	2026-03-28 03:16:48.023178	\N
1168	865	codIncPisPasep	0	00	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1169	775	codIncPisPasep	0	00	DESC. ASSIST. ODONTOLOGICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1170	467	codIncPisPasep	0	00	CLAUSULA 22ª CCT TRT SP 07/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
1171	255	codIncPisPasep	0	00	DIF. CCT - 2017	automatico	pendente	2026-03-28 03:16:48.023178	\N
1172	177	codIncPisPasep	0	00	SALARIO SUBSTITUTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1173	960	codIncPisPasep	0	00	DESCONTO REF. FALTAS - 1/2 OFICIAL BORRACHEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1174	420	codIncPisPasep	0	00	ABONO PECUNIARIO RODOVIARIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1175	989	codIncPisPasep	0	00	DESC. PGTO ASSIDUIDADE MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1176	595	codIncPisPasep	0	00	DESC. CONTRIB. NEGOCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1177	758	codIncPisPasep	0	00	DESC. CONTRIB. DE NATUREZA PREVIDENCIARIA -MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1178	221	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 05/11	automatico	pendente	2026-03-28 03:16:48.023178	\N
1179	472	codIncPisPasep	0	00	CLAUSULA 22ª CCT TRT SP 10/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
1180	364	codIncPisPasep	0	00	ADIC. PERICULOSIDADE FERIAS INDENIZADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1181	663	codIncPisPasep	0	00	REEMB. VT-SALVADORCARD NAO CARREGADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1182	929	codIncPisPasep	0	00	FATURAMENTO DE ART-RRT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1183	407	codIncPisPasep	0	00	MEDIAS FERIAS S/ABONO (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1184	572	codIncPisPasep	0	00	DESC. I.R.F. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1185	555	codIncPisPasep	0	00	DESC. 13º SALARIO ANTECIPADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1186	1053	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1187	283	codIncPisPasep	0	00	1ª PARCELA 13º SALARIO NAO SUJEITO F.G.T.S.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1188	881	codIncPisPasep	0	00	PARTICIPAÇÃO DE LUCRO/RESULTADOS 2023	automatico	pendente	2026-03-28 03:16:48.023178	\N
1189	395	codIncPisPasep	0	00	DIF - DIA DO RODOVIARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1190	778	codIncPisPasep	0	00	DESC. VALE ALIMENTACAO NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1191	516	codIncPisPasep	0	00	DESC. ASSIST. ODONTOLOGICA DEPENDENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1192	93	codIncPisPasep	0	00	F.G.T.S. MULTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1193	212	codIncPisPasep	0	00	DIF. SALARIO 10/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
1194	1043	codIncPisPasep	0	00	FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1195	1008	codIncPisPasep	0	00	FERIAS INDENIZADAS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1196	1095	codIncPisPasep	0	00	HORAS EXTRAS 100% DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1197	1091	codIncPisPasep	0	00	HORAS EXTRAS 100% - AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1198	788	codIncPisPasep	0	00	DESC. CARTAO SALARIO - ADMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1199	978	codIncPisPasep	0	00	ADIC. PERICULOSIDADE SOBRE HORAS EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1200	130	codIncPisPasep	0	00	HORAS EXTRAS 110%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1201	571	codIncPisPasep	0	00	DESC. I.R.F. S/FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1202	107	codIncPisPasep	0	00	HORAS EXTRAS 50% - 11/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1203	466	codIncPisPasep	0	00	CLAUSULA 22ª CCT TRT SP 06/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
1204	17	codIncPisPasep	0	00	SALARIO MES	automatico	pendente	2026-03-28 03:16:48.023178	\N
1205	745	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1206	535	codIncPisPasep	0	00	DESC. CONTRIB. COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1207	1120	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1208	231	codIncPisPasep	0	00	REEMB. DESPESAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1209	619	codIncPisPasep	0	00	DESC. ASS. MÉDICA DEP.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1210	321	codIncPisPasep	0	00	AUXILIO LENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1211	819	codIncPisPasep	0	00	DESC. CB DIF CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1212	210	codIncPisPasep	0	00	DIF. SALARIO 08/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
1213	1077	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1214	529	codIncPisPasep	0	00	DESC. BENEFICIO SOC. FAMILIAR - 02/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
1215	682	codIncPisPasep	0	00	HORAS EXTRAS INSAL 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1216	795	codIncPisPasep	0	00	ADIC. NOTURNO C/35% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1217	372	codIncPisPasep	0	00	FERIAS S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1218	88	codIncPisPasep	0	00	HORA NOTURNA REDUZIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1219	548	codIncPisPasep	0	00	DESC. VR NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1220	711	codIncPisPasep	0	00	DESC. ALOJAMENTO(USO FUTURO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1221	419	codIncPisPasep	0	00	ABONO DE FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1222	239	codIncPisPasep	0	00	REEMB. VALE REFEICAO DIF. 03/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
1223	350	codIncPisPasep	0	00	FERIAS NORMAIS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1224	434	codIncPisPasep	0	00	ADIC. DE ABONO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1225	337	codIncPisPasep	0	00	D.S.R. S/VARIAVEIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1226	49	codIncPisPasep	0	00	DIF. DISSIDIO - 11/2009	automatico	pendente	2026-03-28 03:16:48.023178	\N
1227	860	codIncPisPasep	0	00	HORAS EXTRAS 50% C/ INSALUBRIDADE MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1228	453	codIncPisPasep	0	00	ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1229	313	codIncPisPasep	0	00	DEVOLUCAO DESC. CRACHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1230	1124	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1231	198	codIncPisPasep	0	00	SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1232	946	codIncPisPasep	0	00	DIFERENÇA - PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1233	706	codIncPisPasep	0	00	DESC. ABONO PAGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1234	1048	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1235	828	codIncPisPasep	0	00	PREMIO ASSIDUIDADE MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1236	413	codIncPisPasep	0	00	1/3 FERIAS FERIAS PROPORCIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1237	474	codIncPisPasep	0	00	ARTIGO 071 MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1238	733	codIncPisPasep	0	00	DESC. UNIFORME	automatico	pendente	2026-03-28 03:16:48.023178	\N
1239	926	codIncPisPasep	0	00	FATURAMENTO DE DIARIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1240	908	codIncPisPasep	0	00	CUSTO OPERACIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1241	165	codIncPisPasep	0	00	D.S.R. DIFERENCA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1242	304	codIncPisPasep	0	00	REEMB. VALE REFEICAO 01 E 02/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
1243	579	codIncPisPasep	0	00	DESC. FALTAS (DIAS) MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1244	727	codIncPisPasep	0	00	DESC. REFEIÇÃO MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1245	234	codIncPisPasep	0	00	REEMB. EXAMES MÉDICOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1246	931	codIncPisPasep	0	00	REPACTUAÇÃO DE CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1247	549	codIncPisPasep	0	00	DESC. EXTRAVIO MAT EMPRESA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1248	1044	codIncPisPasep	0	00	AUXILIO ESPECIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1249	54	codIncPisPasep	0	00	ADIC. NOTURNO C/25%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1250	489	codIncPisPasep	0	00	DIF. CESTA BASICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1251	783	codIncPisPasep	0	00	HORAS EXTRAS 115% MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1252	962	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA EM FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1253	651	codIncPisPasep	0	00	REDUCAO JORNADA COVID - 25%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1254	1119	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1255	961	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1256	992	codIncPisPasep	0	00	REEMB. ATRASO (HORAS) - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1257	355	codIncPisPasep	0	00	ADIC. FERIAS TEMP	automatico	pendente	2026-03-28 03:16:48.023178	\N
1258	171	codIncPisPasep	0	00	AUX. DOENÇA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1259	859	codIncPisPasep	0	00	HORAS EXTRAS 100% C/ INSALUBRIDADE MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1260	1104	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1261	670	codIncPisPasep	0	00	ADIC. NOTURNO C/39%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1262	612	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1263	977	codIncPisPasep	0	00	ADIC. PERICULOSIDADE S/ HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1264	869	codIncPisPasep	0	00	REEMBOLSO DESC. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1265	357	codIncPisPasep	0	00	FERIAS PROPORCIONAIS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1266	358	codIncPisPasep	0	00	1/3 FERIAS PROPORCIONAIS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1267	61	codIncPisPasep	0	00	ADIC. INSALUBRIDADE MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1268	342	codIncPisPasep	0	00	DIF. CESTA BASICA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1269	427	codIncPisPasep	0	00	ATUALIZACAO MONETARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1270	759	codIncPisPasep	0	00	DESC. AUX. DOENÇA INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1271	387	codIncPisPasep	0	00	FERIAS VENCIDAS INDENIZ.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1272	311	codIncPisPasep	0	00	COMPLEMENTO HORAS EXTRAS 50% - 08/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1273	880	codIncPisPasep	0	00	H E 50% - ART. 71 MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1274	909	codIncPisPasep	0	00	RECRUTAMENTO E SELECAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1275	361	codIncPisPasep	0	00	ADIC. FERIAS S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1276	672	codIncPisPasep	0	00	DESC. VALE-TRANSPORTE 6%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1277	801	codIncPisPasep	0	00	DIFERENCA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1278	479	codIncPisPasep	0	00	INDENIZACAO ARTº 479	automatico	pendente	2026-03-28 03:16:48.023178	\N
1279	328	codIncPisPasep	0	00	ADIANTAMENTO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1280	591	codIncPisPasep	0	00	DESC. CONTRIB. COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1281	615	codIncPisPasep	0	00	DESC. ASS. MÉDICA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1282	791	codIncPisPasep	0	00	MULTA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1283	939	codIncPisPasep	0	00	DEMONSTRATIVO DE HORAS EXTRAS 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1284	806	codIncPisPasep	0	00	DESC. EMPRESTIMO NEON	automatico	pendente	2026-03-28 03:16:48.023178	\N
1285	6	codIncPisPasep	0	00	COMISSAO ELETRO - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
1286	436	codIncPisPasep	0	00	ADIC. FERIAS VENCIDAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1287	374	codIncPisPasep	0	00	1/3 ADIC. FERIAS S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1288	270	codIncPisPasep	0	00	H E 50% - ART. 71	automatico	pendente	2026-03-28 03:16:48.023178	\N
1289	345	codIncPisPasep	0	00	DIFERENCA DE DISSIDIO 08 2012	automatico	pendente	2026-03-28 03:16:48.023178	\N
1290	425	codIncPisPasep	0	00	AUXILIO MORADIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1291	267	codIncPisPasep	0	00	HORAS EXTRAS COMPL 60%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1292	333	codIncPisPasep	0	00	AUXILIO UNIFORME DIF. CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1293	673	codIncPisPasep	0	00	DESC. CARTAO BHBUS / OTIMO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1294	895	codIncPisPasep	0	00	DESC. ASSIST. ODONTO. DEPENDENTE MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1295	720	codIncPisPasep	0	00	DESC. FARMACIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1296	1105	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1297	1022	codIncPisPasep	0	00	DIF CCT PREMIO TEMPO DE SERVICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1298	9276	codIncPisPasep	0	00	VALE TRANSPORTE (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1299	462	codIncPisPasep	0	00	DESC H EXTRAS 50% - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1300	902	codIncPisPasep	0	00	UNIFORME	automatico	pendente	2026-03-28 03:16:48.023178	\N
1301	843	codIncPisPasep	0	00	DESC AD NOT INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1302	155	codIncPisPasep	0	00	REEMB. VALE ALIMENTACAO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1303	291	codIncPisPasep	0	00	ADIC. INSALUBRIDADE S/1ª 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1304	284	codIncPisPasep	0	00	PAGTO. VALE ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1305	430	codIncPisPasep	0	00	DEVOLUCAO DESC. VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1306	513	codIncPisPasep	0	00	DESC. HE/FICTA -  PAGAS A MAIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1307	787	codIncPisPasep	0	00	DESC SALARIO FAMILIA INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1308	519	codIncPisPasep	0	00	DESC. CONTRIB. ASSISTENCIAL LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1309	780	codIncPisPasep	0	00	DESC. ASSIST. MEDICA REF. PENSÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1310	593	codIncPisPasep	0	00	DESC. CONTRIB. ASSISTENCIAL 13º	automatico	pendente	2026-03-28 03:16:48.023178	\N
1311	717	codIncPisPasep	0	00	DESC. COMBUSTIVEL UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1312	677	codIncPisPasep	0	00	DESC. VALE TRANSP. NAO UTILIZADO MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1313	197	codIncPisPasep	0	00	DIF. CCT - 2016	automatico	pendente	2026-03-28 03:16:48.023178	\N
1314	835	codIncPisPasep	0	00	HORAS EXTRAS 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1315	207	codIncPisPasep	0	00	DIF. SALARIO 10/2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
1316	1085	codIncPisPasep	0	00	HORAS EXTRAS 100% - FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1317	956	codIncPisPasep	0	00	DESCONTO REF. ATRASOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1318	339	codIncPisPasep	0	00	DEVOLUCAO FALTAS / DSR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1319	754	codIncPisPasep	0	00	DIF ABONO DE FERIAS ARTº 143 (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1320	628	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA ABONO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1321	883	codIncPisPasep	0	00	DESC. CONTRIB. NEGOCIAL MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1322	904	codIncPisPasep	0	00	MAO DE OBRA ALMOXARIFE BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1323	59	codIncPisPasep	0	00	ADIC. INSALUBRIDADE 08/2019	automatico	pendente	2026-03-28 03:16:48.023178	\N
1324	1017	codIncPisPasep	0	00	REEMB. EXAME TROCA DE FUNCAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1325	876	codIncPisPasep	0	00	DIF H.E. 50% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1326	684	codIncPisPasep	0	00	ADIC. NOTURNO C/20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1327	327	codIncPisPasep	0	00	ABONADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1328	845	codIncPisPasep	0	00	REEMB. DESPESAS - INVISIVEL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1329	581	codIncPisPasep	0	00	DESC. CONTRIB. ASS. LAB. SETUHCAM	automatico	pendente	2026-03-28 03:16:48.023178	\N
1330	116	codIncPisPasep	0	00	HORAS EXTRAS 60% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1331	465	codIncPisPasep	0	00	DIF. 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1332	1047	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1333	760	codIncPisPasep	0	00	DESC. SALDO DE QUITACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1334	309	codIncPisPasep	0	00	BENEFICIOS PAGOS A MENOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1335	121	codIncPisPasep	0	00	HORAS EXTRAS 70% + ADIC. NOT. 30%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1336	796	codIncPisPasep	0	00	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1337	307	codIncPisPasep	0	00	ADIC DE SALARIO MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1338	242	codIncPisPasep	0	00	REEMB. VALE REFEICAO DIF. 10/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1339	752	codIncPisPasep	0	00	DIF. 1/3 DAS FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1340	821	codIncPisPasep	0	00	HORAS NORMAIS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1341	300	codIncPisPasep	0	00	ABONO IDADE TEMP SERVICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1342	721	codIncPisPasep	0	00	DESC. FORNECIMENTO CAFE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1343	1134	codIncPisPasep	0	00	ADIC. PERICULOSIDADE MES 12/2025	automatico	pendente	2026-03-28 03:16:48.023178	\N
1344	195	codIncPisPasep	0	00	F.G.T.S. FIM DE CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1345	1061	codIncPisPasep	0	00	HORAS EXTRAS 50% - MARCO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1346	496	codIncPisPasep	0	00	F.G.T.S. (FATURAMENTO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1347	592	codIncPisPasep	0	00	DESC. CONTRIB. ASSISTENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1348	831	codIncPisPasep	0	00	SALARIO MATERNIDADE (MES ANTERIOR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1349	1056	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1350	199	codIncPisPasep	0	00	DIF. SALARIO PISO RJ	automatico	pendente	2026-03-28 03:16:48.023178	\N
1351	1103	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1352	805	codIncPisPasep	0	00	ADIC. PERIC. S/FERIAS S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1354	1083	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1355	218	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 02/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
1356	739	codIncPisPasep	0	00	CONTRIB. ASSIST- PROCESSO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1357	253	codIncPisPasep	0	00	DEV. ATRASO/FALTA HORAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1358	334	codIncPisPasep	0	00	AVISO PREVIO ADICIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1359	802	codIncPisPasep	0	00	ADIC. PERIC. S/FERIAS PROPORCIONAIS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1360	411	codIncPisPasep	0	00	MEDIA HORAS EXTRAS FERIAS PROP	automatico	pendente	2026-03-28 03:16:48.023178	\N
1361	689	codIncPisPasep	0	00	DESC. VT DIF CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1362	1096	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1363	403	codIncPisPasep	0	00	COMPLEMENTO FERIAS (DISSIDIO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1364	1030	codIncPisPasep	0	00	REEMB. ATRASO/FALTA HORAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1365	564	codIncPisPasep	0	00	DESC. 2ª VIA CARTAO ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1366	1028	codIncPisPasep	0	00	DIFERENÇA AJUDA DE CUSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1367	310	codIncPisPasep	0	00	REEMB DESC INDEVIDO - D.S.R	automatico	pendente	2026-03-28 03:16:48.023178	\N
1368	181	codIncPisPasep	0	00	DOMINGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1369	1051	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1370	907	codIncPisPasep	0	00	FATURAMENTO DE DIARIAS, DESLOCAMENTOS E PASSAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1371	941	codIncPisPasep	0	00	DEMONSTRATIVO DE ADICIONAL NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1372	1118	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1373	530	codIncPisPasep	0	00	DESC. VALE-TRANSP DISSIDIO 6%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1374	837	codIncPisPasep	0	00	DESC. FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1375	623	codIncPisPasep	0	00	DESC. REFEIÇÃO/ALIMENTAÇÃO PRÓXIMO MÊS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1376	800	codIncPisPasep	0	00	ADIC. PERIC. S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1377	492	codIncPisPasep	0	00	ENCARGOS S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1378	178	codIncPisPasep	0	00	TRIENIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1379	143	codIncPisPasep	0	00	FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1380	725	codIncPisPasep	0	00	DESC. PENDENCIAS PREST CONTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1381	482	codIncPisPasep	0	00	ADIC. PERICULOSIDADE S/2ª PARCELA 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1382	1100	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1383	86	codIncPisPasep	0	00	HORA FICTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1384	75	codIncPisPasep	0	00	DIF. HORAS EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1385	688	codIncPisPasep	0	00	DESC. CONVENIO ODONTOLOGICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1386	97	codIncPisPasep	0	00	HORAS EXTRAS 08/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1387	657	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA EM FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1388	77	codIncPisPasep	0	00	DIF. MINIMO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1389	1004	codIncPisPasep	0	00	DESC. CONVENIO E CONSULTAS - SIEMACO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1390	848	codIncPisPasep	0	00	ACUMULO DE FUNCAO MES ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1391	8	codIncPisPasep	0	00	SALARIO NORMATIVO - GER	automatico	pendente	2026-03-28 03:16:48.023178	\N
1392	47	codIncPisPasep	0	00	SALARIO FAMILIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1393	607	codIncPisPasep	0	00	DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1394	691	codIncPisPasep	0	00	DESC. ANTECIPACAO VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1395	1021	codIncPisPasep	0	00	DESC. VT DIF CCT - 05/24 a 07/24	automatico	pendente	2026-03-28 03:16:48.023178	\N
1396	1082	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1397	966	codIncPisPasep	0	00	HORAS EXTRAS 30%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1398	808	codIncPisPasep	0	00	GRATIFICACAO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1399	1074	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - MARCO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1400	380	codIncPisPasep	0	00	SALDO DE SALARIOS.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1401	172	codIncPisPasep	0	00	ACIDENTE DE TRABALHO (15 DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1402	443	codIncPisPasep	0	00	INDEN. ADIC. TEMPO SERVICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1403	377	codIncPisPasep	0	00	PREMIO TEMPO DE SERVICO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1404	288	codIncPisPasep	0	00	ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1405	586	codIncPisPasep	0	00	DESC. CONTRIB. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1406	716	codIncPisPasep	0	00	DESC. CELULAR NAO DEVOLVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1407	954	codIncPisPasep	0	00	DIFERENÇA DE DISSIDIO CONFORME CCT 2016	automatico	pendente	2026-03-28 03:16:48.023178	\N
1408	741	codIncPisPasep	0	00	ADIC. NOTURNO 22,50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1409	722	codIncPisPasep	0	00	DESC. FRANQUIA VEICULO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1410	381	codIncPisPasep	0	00	ADIC. INSALUBRIDADE S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1411	236	codIncPisPasep	0	00	REEMB. VALE REFEICAO DIF.DISSIDIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1412	269	codIncPisPasep	0	00	HORAS EXTRAS 75% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1413	810	codIncPisPasep	0	00	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1414	451	codIncPisPasep	0	00	1/3 FERIAS MES A MES INDENIZADA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1415	1075	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1416	153	codIncPisPasep	0	00	DIF. ADIC. PERICULOSIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1417	315	codIncPisPasep	0	00	DIF. GUELTA PAGA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1418	96	codIncPisPasep	0	00	HORAS EXTRAS 07/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1419	1019	codIncPisPasep	0	00	DIF CCT ABONO PECUNIARIO RODOVIARIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1420	131	codIncPisPasep	0	00	HORAS EXTRAS 122%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1421	504	codIncPisPasep	0	00	DESC. D.S.R. S/FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1422	188	codIncPisPasep	0	00	P.L.R. REF.CCT 2011 TRT CPS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1423	987	codIncPisPasep	0	00	DIFERENCA 1/3 FERIAS (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1424	743	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50	automatico	pendente	2026-03-28 03:16:48.023178	\N
1425	40	codIncPisPasep	0	00	DIF. DISSIDIO - 03/2010	automatico	pendente	2026-03-28 03:16:48.023178	\N
1426	583	codIncPisPasep	0	00	DESC. CONTRIB. COL. LAB. SIEEACON	automatico	pendente	2026-03-28 03:16:48.023178	\N
1427	246	codIncPisPasep	0	00	HORAS EXTRAS 50% - 09/2016	automatico	pendente	2026-03-28 03:16:48.023178	\N
1428	1073	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1429	820	codIncPisPasep	0	00	SALARIO DIA (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1430	250	codIncPisPasep	0	00	ADIC. NOTURNO C/100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1431	144	codIncPisPasep	0	00	1/3 FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1432	647	codIncPisPasep	0	00	DESC. EMPRESTIMO ZIPDIN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1433	643	codIncPisPasep	0	00	DESC. PROGRAMA ASSIST. FAMILIAR (PAF) M/ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1434	292	codIncPisPasep	0	00	ADIC. NOT MES ANT C/30%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1435	634	codIncPisPasep	0	00	DESC. CONTRIB. ASS. LAB. SIEEACON	automatico	pendente	2026-03-28 03:16:48.023178	\N
1436	584	codIncPisPasep	0	00	DESC. MENS. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1437	545	codIncPisPasep	0	00	DESC. EMPRESTIMO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1438	769	codIncPisPasep	0	00	DESC. VALE REFEICAO NAO UTILIZADO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1439	1086	codIncPisPasep	0	00	HORAS EXTRAS 100% - MARÇO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1440	874	codIncPisPasep	0	00	DEV. FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1441	148	codIncPisPasep	0	00	MULTA CLAUSULA DECIMA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1442	92	codIncPisPasep	0	00	HORAS ABONADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1443	856	codIncPisPasep	0	00	PRORROGAÇÃO SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1444	963	codIncPisPasep	0	00	DESCONTO REF. FALTAS - 1/2 OFICIAL MECANICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1445	646	codIncPisPasep	0	00	DESC. MENS. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1446	101	codIncPisPasep	0	00	HORAS EXTRAS 35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1447	278	codIncPisPasep	0	00	PAGTO. CESTA BASICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1448	892	codIncPisPasep	0	00	REEMB. EXAME RETORNO AO TRABALHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1449	449	codIncPisPasep	0	00	GRATIFICACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1450	39	codIncPisPasep	0	00	DIF. DISSIDIO - 02/2010	automatico	pendente	2026-03-28 03:16:48.023178	\N
1451	1034	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1452	867	codIncPisPasep	0	00	DEV. ATRASO/D.S.R. HORAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1453	35	codIncPisPasep	0	00	DIF. D.S.R.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1454	933	codIncPisPasep	0	00	MAO DE OBRA - 1/2 OFICIAL MECANICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1455	886	codIncPisPasep	0	00	DESC. CONTRIB. NEGOCIAL SINTRAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1456	509	codIncPisPasep	0	00	DESC. DEV. HE/A.N./DSR - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1457	1112	codIncPisPasep	0	00	CUSTEIO SOCIAL - SINTEAC MG	automatico	pendente	2026-03-28 03:16:48.023178	\N
1458	847	codIncPisPasep	0	00	H.EXTRA  NOTURNO C/100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1459	1070	codIncPisPasep	0	00	HORAS EXTRAS 50% - DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1460	222	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 05/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
1461	1131	codIncPisPasep	0	00	DESC. CONTRIB. ASSISTENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1462	1087	codIncPisPasep	0	00	HORAS EXTRAS 100% ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1463	429	codIncPisPasep	0	00	DESC. INDEVIDO DE FALTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1464	1133	codIncPisPasep	0	00	PREMIO ASSIDUIDADE - NUTRI	automatico	pendente	2026-03-28 03:16:48.023178	\N
1465	139	codIncPisPasep	0	00	MULTA CLAUSULA OCTAGESIMA PRIMEIRA  CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1466	680	codIncPisPasep	0	00	DESC. VALE-TRANSP NAO UTILIZADO ATESTADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1467	923	codIncPisPasep	0	00	FATURAMENTO DE 13º SALARIO 1º PARCELA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1468	353	codIncPisPasep	0	00	AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1469	63	codIncPisPasep	0	00	AUX. NATALIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1470	919	codIncPisPasep	0	00	FATURAMENTO DE FALTAS LEGAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1471	511	codIncPisPasep	0	00	DESC. DIF.DISSIDIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1472	249	codIncPisPasep	0	00	REEMB. DESC. ASS. ODONTOLOGICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1473	631	codIncPisPasep	0	00	DESC. ASSIST. ODONT. SINTACLUNS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1474	627	codIncPisPasep	0	00	DESC. ADIANT. NORMAL(DENTRO DO MES)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1475	955	codIncPisPasep	0	00	DESC. ADIC. NOTURNO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1476	544	codIncPisPasep	0	00	DESC. DIVERSOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1477	1055	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1478	368	codIncPisPasep	0	00	FERIAS S/AVISO PREVIO INDENIZADO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1479	220	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 04/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
1480	872	codIncPisPasep	0	00	HORAS EXTRAS 50% - DIF	automatico	pendente	2026-03-28 03:16:48.023178	\N
1481	169	codIncPisPasep	0	00	SABADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1482	299	codIncPisPasep	0	00	ADIC. SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1483	944	codIncPisPasep	0	00	DEMONSTRATIVO DE SOBREAVISO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1484	901	codIncPisPasep	0	00	BENEFICIOS MENSAIS E DIARIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1485	184	codIncPisPasep	0	00	HORAS REDUZIDAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1486	160	codIncPisPasep	0	00	D.S.R. S/HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1487	653	codIncPisPasep	0	00	REDUCAO JORNADA COVID - 70%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1488	761	codIncPisPasep	0	00	DESC. TAXA NEGOCIAL LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1489	279	codIncPisPasep	0	00	DEVOL DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1490	1009	codIncPisPasep	0	00	1/3 FERIAS INDENIZADAS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1491	649	codIncPisPasep	0	00	DESC. CONTRIB. SOCIAL SINDICAL MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1492	484	codIncPisPasep	0	00	AJUDA COMPUSORIA MP936	automatico	pendente	2026-03-28 03:16:48.023178	\N
1493	949	codIncPisPasep	0	00	DESC. I.N.S.S. MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1494	668	codIncPisPasep	0	00	DIF. CCT 2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
1495	273	codIncPisPasep	0	00	ARREDONDAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1496	161	codIncPisPasep	0	00	D.S.R. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1497	934	codIncPisPasep	0	00	AJUDA DE CUSTO - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1498	546	codIncPisPasep	0	00	DESC. ADIANT. NORMAL (FORAMES)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1499	18	codIncPisPasep	0	00	ADICIONAL DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1500	296	codIncPisPasep	0	00	HORAS EXTRAS 115%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1501	774	codIncPisPasep	0	00	DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1502	471	codIncPisPasep	0	00	CLAUSULA 22ª CCT TRT SP 09/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
1503	707	codIncPisPasep	0	00	DESC. ACERTO PENDENCIAS PREST CONTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1504	568	codIncPisPasep	0	00	DESC. PAGTO DIF VALE ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1505	64	codIncPisPasep	0	00	ADIC. NOTURNO C/50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1506	613	codIncPisPasep	0	00	DESC. JUDICIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1507	324	codIncPisPasep	0	00	DIF. CCT - 2018	automatico	pendente	2026-03-28 03:16:48.023178	\N
1508	506	codIncPisPasep	0	00	DESC. ATRASOS/SAIDAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1509	997	codIncPisPasep	0	00	DESC. MULTA 40% - REITEGRAÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1510	686	codIncPisPasep	0	00	DESC. AVISO PREVIO NAO TRABALHADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1511	170	codIncPisPasep	0	00	D.S.R. S/COMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1512	740	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50	automatico	pendente	2026-03-28 03:16:48.023178	\N
1513	367	codIncPisPasep	0	00	13º SALARIO PROP. S/AVISO PREVIO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1514	704	codIncPisPasep	0	00	DESC. 2ª VIA CRACHÁ MAGNETICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1515	1012	codIncPisPasep	0	00	PARTICIPACAO LUCROS/RESULTADOS - 2024	automatico	pendente	2026-03-28 03:16:48.023178	\N
1516	1003	codIncPisPasep	0	00	PARCELAMENTO 6	automatico	pendente	2026-03-28 03:16:48.023178	\N
1517	414	codIncPisPasep	0	00	1/3 FERIAS MES SEGUINTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1518	526	codIncPisPasep	0	00	DESC. PLR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1519	157	codIncPisPasep	0	00	DIF PAGTO AGO-2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
1520	136	codIncPisPasep	0	00	D.S.R. S/ADICIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1521	1081	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1522	609	codIncPisPasep	0	00	DESC. HORAS MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1523	522	codIncPisPasep	0	00	DESC. CO PARTICIPACAO A.M.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1524	675	codIncPisPasep	0	00	ANTEC INST REDUCAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1525	417	codIncPisPasep	0	00	1/3 S/ABONO DE FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1526	416	codIncPisPasep	0	00	1/3 MEDIA FERIAS PROPORCIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1527	979	codIncPisPasep	0	00	DESCONTO RECESSO FORENSE - COPEIRO E COPEIRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1528	773	codIncPisPasep	0	00	DESC. VALE REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1529	502	codIncPisPasep	0	00	DESC. ATRASO/FALTA HORAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1530	305	codIncPisPasep	0	00	REEMB.V.REFEICAO./ ALIM. REF. EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1531	9287	codIncPisPasep	0	00	BENEFICIO PROMOCAO (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1532	320	codIncPisPasep	0	00	SOBRE AVISO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1533	233	codIncPisPasep	0	00	REEMB. REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1534	1110	codIncPisPasep	0	00	ADIC. INSALUBRIDADE 07/2020 a 12/2020	automatico	pendente	2026-03-28 03:16:48.023178	\N
1535	442	codIncPisPasep	0	00	HORAS NORMAIS CREDITO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1536	541	codIncPisPasep	0	00	DESC. ARREDONDAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1537	520	codIncPisPasep	0	00	DESC. AVARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1538	1122	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1539	750	codIncPisPasep	0	00	ADIC. NOTURNO C/39% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1540	151	codIncPisPasep	0	00	REEMB. VALE TRANSPORTE MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1541	441	codIncPisPasep	0	00	HORAS EXTRAS 50% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1542	650	codIncPisPasep	0	00	COMPL AJ COMPUSORIA MP936	automatico	pendente	2026-03-28 03:16:48.023178	\N
1543	174	codIncPisPasep	0	00	AUX. DOENÇA (F.G.T.S.)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1544	1052	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1545	626	codIncPisPasep	0	00	DESC. ATRASO/FALTA HORAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1546	527	codIncPisPasep	0	00	DESC. PROGRAMA ASSIST. FAMILIAR (PAF)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1547	68	codIncPisPasep	0	00	ADIC. PERICULOSIDADE 11/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1548	679	codIncPisPasep	0	00	DESC. VALE-TRANSPORTE MES ANTERIOR 6%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1549	317	codIncPisPasep	0	00	DIF. VALE REFEICAO TJMG 01 E 02/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
1550	873	codIncPisPasep	0	00	REEMB. 6% VALE TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1551	487	codIncPisPasep	0	00	ENCARGOS S/ FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1552	183	codIncPisPasep	0	00	FERIADO (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1553	543	codIncPisPasep	0	00	DESC. VALE-TRANSP - CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1554	1072	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1555	159	codIncPisPasep	0	00	D.S.R. S/ADICIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1556	1068	codIncPisPasep	0	00	HORAS EXTRAS 50% - OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1557	849	codIncPisPasep	0	00	DIF. PAGTO CONDUCAO VAN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1558	176	codIncPisPasep	0	00	SALARIO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1559	708	codIncPisPasep	0	00	DESC. AJUDA CUSTO NAO UTILIZAD	automatico	pendente	2026-03-28 03:16:48.023178	\N
1560	9277	codIncPisPasep	0	00	VALE REFEICAO (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1561	182	codIncPisPasep	0	00	FALTAS ABONADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1562	764	codIncPisPasep	0	00	REEMBOLSO DESC. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1563	285	codIncPisPasep	0	00	PAGTO. OUTROS BENEFICIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1564	260	codIncPisPasep	0	00	DIF. CCT S/FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1565	728	codIncPisPasep	0	00	DESC. REFEICOES	automatico	pendente	2026-03-28 03:16:48.023178	\N
1566	370	codIncPisPasep	0	00	13º SALARIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1567	11	codIncPisPasep	0	00	1/3 FERIAS VENCIDAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1568	635	codIncPisPasep	0	00	DIF EMPRESTIMO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1569	1058	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1570	505	codIncPisPasep	0	00	DESC. ATRASOS/SAIDAS ANTECIPADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1571	1024	codIncPisPasep	0	00	DIF ADIC. FERIAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1572	399	codIncPisPasep	0	00	1/3 FERIAS NORMAIS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1573	145	codIncPisPasep	0	00	DEV. FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1574	588	codIncPisPasep	0	00	DESC. CONTRIB. CONFEDERATIVA ASSISTENCIAL BH 2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
1575	694	codIncPisPasep	0	00	DESC. HORA EXTRA PAGO A MAIOR / DSR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1576	753	codIncPisPasep	0	00	REEMB VALE REFEICAO/ ALIMENTACAO - HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1577	126	codIncPisPasep	0	00	HORAS EXTRAS 100% - 11/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1578	606	codIncPisPasep	0	00	DESC. ASSIST. ODONTO. DEPENDENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1579	523	codIncPisPasep	0	00	DESC. COMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1580	108	codIncPisPasep	0	00	HORAS EXTRAS 50% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1581	266	codIncPisPasep	0	00	REEMB. CURSOS / TREINAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1582	611	codIncPisPasep	0	00	DESC. VALE ALIMENTACAO - CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1583	935	codIncPisPasep	0	00	DEMONSTRATIVO DE HORAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1584	925	codIncPisPasep	0	00	FATURAMENTO DE HORAS EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1585	893	codIncPisPasep	0	00	DESC. VALE-TRANSPORTE 6% MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1586	537	codIncPisPasep	0	00	DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1587	566	codIncPisPasep	0	00	DESC. I.N.S.S.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1588	1069	codIncPisPasep	0	00	HORAS EXTRAS 50% - NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1589	400	codIncPisPasep	0	00	COMPLEMENTO FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1590	1002	codIncPisPasep	0	00	PARCELAMENTO 5	automatico	pendente	2026-03-28 03:16:48.023178	\N
1591	891	codIncPisPasep	0	00	REEMB VALE LANCHE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1592	134	codIncPisPasep	0	00	HORAS EXTRAS 175%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1593	118	codIncPisPasep	0	00	HORAS EXTRAS 65% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1594	575	codIncPisPasep	0	00	DESC. CONTRIB. ASSISTENCIAL - SINDMAN	automatico	pendente	2026-03-28 03:16:48.023178	\N
1595	208	codIncPisPasep	0	00	DIF. SALARIO 06/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
1596	166	codIncPisPasep	0	00	D.S.R. COMPETENCIA 10/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
1597	224	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 10/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
1598	817	codIncPisPasep	0	00	DEMONSTRATIVO PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1599	667	codIncPisPasep	0	00	DESC. MENS. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1600	16	codIncPisPasep	0	00	SALARIO MES	automatico	pendente	2026-03-28 03:16:48.023178	\N
1601	163	codIncPisPasep	0	00	D.S.R. S/FERIADO - HS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1602	351	codIncPisPasep	0	00	1/3 FERIAS NORMAIS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1603	245	codIncPisPasep	0	00	HORAS EXTRAS 50% - 07/2016	automatico	pendente	2026-03-28 03:16:48.023178	\N
1604	379	codIncPisPasep	0	00	REEMB VALE REFEICAO/ ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1605	73	codIncPisPasep	0	00	ADIC. NOTURNO - 01/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
1606	947	codIncPisPasep	0	00	MAO DE OBRA - COPEIRO E COPEIRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1607	809	codIncPisPasep	0	00	DESC ADIC. PERICULOSIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1608	1001	codIncPisPasep	0	00	PARCELAMENTO 4	automatico	pendente	2026-03-28 03:16:48.023178	\N
1609	547	codIncPisPasep	0	00	DESC. ESTACIONAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1610	942	codIncPisPasep	0	00	PAGTO. V. T - NAO LIQUIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1611	433	codIncPisPasep	0	00	DEVOLUCAO UNIFORMES	automatico	pendente	2026-03-28 03:16:48.023178	\N
1612	1113	codIncPisPasep	0	00	TAXA SINDICAL - SINTEAC MG	automatico	pendente	2026-03-28 03:16:48.023178	\N
1613	440	codIncPisPasep	0	00	HORAS EXTRAS 140%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1614	179	codIncPisPasep	0	00	ATESTADO MEDICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1615	914	codIncPisPasep	0	00	FATURAMENTO DE VA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1616	757	codIncPisPasep	0	00	DESC. CONTRIB. DE NATUREZA PREVIDENCIARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1617	23	codIncPisPasep	0	00	DIF. CCT - 2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
1618	868	codIncPisPasep	0	00	DEV. FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1619	659	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA ACORDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1620	498	codIncPisPasep	0	00	ENCARGOS S/FOLHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1621	971	codIncPisPasep	0	00	DESC.CESTA BASICA SOCIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1622	983	codIncPisPasep	0	00	DIFERENCA FERIAS (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1623	24	codIncPisPasep	0	00	PREMIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1624	316	codIncPisPasep	0	00	DIF. VALE REFEICAO ANCINE 08/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
1625	705	codIncPisPasep	0	00	2ª VIA CARTEIRINHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1626	71	codIncPisPasep	0	00	AJUD FILHO DEFICIENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1627	470	codIncPisPasep	0	00	13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1628	447	codIncPisPasep	0	00	GRATIFICACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1629	158	codIncPisPasep	0	00	D.S.R. S/PREMIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1630	839	codIncPisPasep	0	00	DESC. FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1631	1093	codIncPisPasep	0	00	HORAS EXTRAS 100% OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1632	1031	codIncPisPasep	0	00	DIF. MULTA POR ATRASO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1633	365	codIncPisPasep	0	00	ABONO APOSENTADORIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1634	402	codIncPisPasep	0	00	PREMIO TEMPO DE SERVICO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1635	736	codIncPisPasep	0	00	DESC. VALE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1636	56	codIncPisPasep	0	00	ADIC. NOTURNO C/30%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1637	45	codIncPisPasep	0	00	DIF. DISSIDIO - 10/2008	automatico	pendente	2026-03-28 03:16:48.023178	\N
1638	25	codIncPisPasep	0	00	PREMIO CONSIGNADO - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
1639	1062	codIncPisPasep	0	00	HORAS EXTRAS 50% - ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1640	200	codIncPisPasep	0	00	ADIC. SALARIO COMP 04/2018	automatico	pendente	2026-03-28 03:16:48.023178	\N
1641	625	codIncPisPasep	0	00	DESPESAS POSTAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1642	456	codIncPisPasep	0	00	DIF. CCT - 2020	automatico	pendente	2026-03-28 03:16:48.023178	\N
1643	216	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 01/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
1644	950	codIncPisPasep	0	00	DIF. ASSISTENCIA MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1645	265	codIncPisPasep	0	00	REEMB. EMPRESTIMO CONSIGNADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1646	44	codIncPisPasep	0	00	DIF. DISSIDIO - 09/2009	automatico	pendente	2026-03-28 03:16:48.023178	\N
1647	301	codIncPisPasep	0	00	ACORDO JUDICIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1648	272	codIncPisPasep	0	00	TRANSPORTE OUTUBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1649	645	codIncPisPasep	0	00	DESCONTO DE 2 VIA VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1650	480	codIncPisPasep	0	00	ADIC. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1651	681	codIncPisPasep	0	00	SOBRE AVISO 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1652	385	codIncPisPasep	0	00	FERIAS COMPLEMENTARES (VLR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1653	294	codIncPisPasep	0	00	DESP DE VIAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1654	4	codIncPisPasep	0	00	COMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1655	943	codIncPisPasep	0	00	MULTA CCT CLÁSULA 6ª - 04/2024	automatico	pendente	2026-03-28 03:16:48.023178	\N
1656	295	codIncPisPasep	0	00	REEMB. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1657	119	codIncPisPasep	0	00	HORAS EXTRAS 70%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1658	410	codIncPisPasep	0	00	FERIAS MES SEGUINTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1659	192	codIncPisPasep	0	00	DECLARAÇÃO JUDICIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1661	889	codIncPisPasep	0	00	AUX. DOENÇA MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1662	240	codIncPisPasep	0	00	REEMB. SALARIO FAMILIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1663	125	codIncPisPasep	0	00	HORAS EXTRAS 100% - 09/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
1664	617	codIncPisPasep	0	00	DESC. ASS. MÉDICA FIOCRUZ	automatico	pendente	2026-03-28 03:16:48.023178	\N
1665	9286	codIncPisPasep	0	00	BENEFICIO INFORMADO (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1666	779	codIncPisPasep	0	00	DESC. ASSIST. MEDICA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1667	616	codIncPisPasep	0	00	DESC. CONTRIB. ASSISTENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1668	235	codIncPisPasep	0	00	TERCO CONSTIT FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1669	189	codIncPisPasep	0	00	QUEBRA DE CAIXA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1670	259	codIncPisPasep	0	00	GRATIFICAÇÃO - BILINGUE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1671	113	codIncPisPasep	0	00	HORAS EXTRAS 60% - 04/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
1672	243	codIncPisPasep	0	00	REEMB. CONTRIB. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1673	724	codIncPisPasep	0	00	DESC. MULTA DE TRANSITO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1674	1116	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1675	226	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 12/12	automatico	pendente	2026-03-28 03:16:48.023178	\N
1676	193	codIncPisPasep	0	00	F.G.T.S. PAGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1677	55	codIncPisPasep	0	00	PRO-LABORE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1678	777	codIncPisPasep	0	00	DESC. OUTROS BENEFICIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1679	91	codIncPisPasep	0	00	HORAS A DESC. FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1680	726	codIncPisPasep	0	00	DESC. PREJUIZO CAUSADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1681	1117	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1682	5	codIncPisPasep	0	00	PARTICIPACAO LUCROS/RESULTADOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1683	730	codIncPisPasep	0	00	DESC. SMARTPHONE NAO DEVOLVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1684	965	codIncPisPasep	0	00	DESCONTO REF. FALTAS - GARCON E GARCONETE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1685	964	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1686	1132	codIncPisPasep	0	00	DESC. CONTRIB. SOCIO-ASSISTENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1687	642	codIncPisPasep	0	00	DESC INSALUBRIDADE INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1688	632	codIncPisPasep	0	00	DESC. CONT.. COLAB. LAB. CABINEIROS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1689	227	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 12/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
1690	589	codIncPisPasep	0	00	DESC. CONTRIB. CONFEDERATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1691	282	codIncPisPasep	0	00	ADIANTAMENTO NORMAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1692	539	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1693	1079	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1694	31	codIncPisPasep	0	00	PREMIO MOVEIS - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
1695	822	codIncPisPasep	0	00	D.S.R. S/FERIADO - HS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1696	287	codIncPisPasep	0	00	REEMB. CONTRIB. COL. LAB. SIEEACON	automatico	pendente	2026-03-28 03:16:48.023178	\N
1697	141	codIncPisPasep	0	00	H E 100% - SUMULA 444	automatico	pendente	2026-03-28 03:16:48.023178	\N
1698	793	codIncPisPasep	0	00	PREMIO ASSIDUIDADE (SEM INCIDENCIA) MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1699	448	codIncPisPasep	0	00	GRATIFICACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1700	251	codIncPisPasep	0	00	HORAS EXTRAS 80%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1701	879	codIncPisPasep	0	00	ADIC. SALARIO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1702	993	codIncPisPasep	0	00	ADICIONAL DE ESTIMULO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1703	503	codIncPisPasep	0	00	DESC. D.S.R. S/FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1704	974	codIncPisPasep	0	00	1/3 FERIAS (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1705	790	codIncPisPasep	0	00	DESC. SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1706	347	codIncPisPasep	0	00	FERIAS VENCIDAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1707	120	codIncPisPasep	0	00	HORAS EXTRAS 70% - ART. 71	automatico	pendente	2026-03-28 03:16:48.023178	\N
1708	841	codIncPisPasep	0	00	DESC. ATRASOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1709	644	codIncPisPasep	0	00	DESC. CONTRIB. ASSISTENCIAL 13 SAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1710	701	codIncPisPasep	0	00	DESC. 2ª VIA CARTAO ALELO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1711	463	codIncPisPasep	0	00	FERIAS A COMPENSAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1712	948	codIncPisPasep	0	00	MULTA POR ATRASO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1713	454	codIncPisPasep	0	00	DESC. AVARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1714	1078	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1715	450	codIncPisPasep	0	00	FERIAS MES A MES INDENIZADA  (TEMP)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1716	41	codIncPisPasep	0	00	DIF. DISSIDIO - 03/2012	automatico	pendente	2026-03-28 03:16:48.023178	\N
1717	281	codIncPisPasep	0	00	PAGTO. ASSIST. ODONTOLOGICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1718	655	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1719	42	codIncPisPasep	0	00	DIF. DISSIDIO - 04/2010	automatico	pendente	2026-03-28 03:16:48.023178	\N
1720	497	codIncPisPasep	0	00	ENCARGOS S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1721	602	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1722	898	codIncPisPasep	0	00	MULTA CCT CLÁSULA 6ª - 03/2024	automatico	pendente	2026-03-28 03:16:48.023178	\N
1723	565	codIncPisPasep	0	00	DESC. H E 60% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1724	1089	codIncPisPasep	0	00	HORAS EXTRAS 100% JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1725	1088	codIncPisPasep	0	00	HORAS EXTRAS 100% MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1726	1042	codIncPisPasep	0	00	REEMBOLSO CO PARTICIPACAO A.M.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1727	600	codIncPisPasep	0	00	DESC. ACIDENTE DE TRABALHO (F.G.T.S.)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1728	217	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 02/12	automatico	pendente	2026-03-28 03:16:48.023178	\N
1729	1050	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1730	393	codIncPisPasep	0	00	F.G.T.S. S/AVISO PREVIO (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1731	554	codIncPisPasep	0	00	DESC. 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1732	1014	codIncPisPasep	0	00	DIF MEDIAS FERIAS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1733	918	codIncPisPasep	0	00	FATURAMENTO DE RESCISÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1734	661	codIncPisPasep	0	00	REEMB. VT-SALVADORCARD	automatico	pendente	2026-03-28 03:16:48.023178	\N
1735	9281	codIncPisPasep	0	00	ASSISTENCIA ODONTOLOGICA (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1736	20	codIncPisPasep	0	00	QUINQUENIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1737	975	codIncPisPasep	0	00	DESCONTO REF. FALTAS - COPEIRO E COPEIRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1738	140	codIncPisPasep	0	00	MULTA CLAUSULA QUINTA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1739	53	codIncPisPasep	0	00	REEMB. I.R.F.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1740	697	codIncPisPasep	0	00	ADIC. NOTURNO C/39% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1741	87	codIncPisPasep	0	00	HORA FICTA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1742	51	codIncPisPasep	0	00	ADIC. NOT. COMPLEMENTAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1743	990	codIncPisPasep	0	00	REEMB. FALTAS (HORAS) - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1744	744	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1745	112	codIncPisPasep	0	00	HORAS EXTRAS 60%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1746	15	codIncPisPasep	0	00	GRATIFICAÇÃO - EXECUTIVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1747	508	codIncPisPasep	0	00	DESC. D.S.R. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1748	458	codIncPisPasep	0	00	HORAS EXTRAS 70% MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1749	676	codIncPisPasep	0	00	DESC. ADIANT. VALE-TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1750	915	codIncPisPasep	0	00	FATURAMENTO DE SEGURO DE VIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1751	920	codIncPisPasep	0	00	FATURAMENTO DE PAF	automatico	pendente	2026-03-28 03:16:48.023178	\N
1752	786	codIncPisPasep	0	00	ADIANTAMENTO - (PGTO FÉRIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1753	336	codIncPisPasep	0	00	AVISO PREVIO INDENIZADO - S/VA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1754	855	codIncPisPasep	0	00	ADIANTAMENTO DE SALARIOS COM INCIDÊNCIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1755	851	codIncPisPasep	0	00	REEMB. I.N.S.S.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1756	614	codIncPisPasep	0	00	DESC. EMPRESTIMO BV	automatico	pendente	2026-03-28 03:16:48.023178	\N
1757	386	codIncPisPasep	0	00	FERIAS PROPORCIONAIS - S/VAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1758	1063	codIncPisPasep	0	00	HORAS EXTRAS 50% - MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1759	7	codIncPisPasep	0	00	COMISSAO MOVEIS - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
1760	110	codIncPisPasep	0	00	HORAS EXTRAS 50% + ADIC. NOT. 35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1761	906	codIncPisPasep	0	00	REPOSIÇÃO PROFISSIONAL AUSENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1762	237	codIncPisPasep	0	00	REEMB. SERVICOS EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1763	952	codIncPisPasep	0	00	DESCONTO REF. RECESSO FORENSE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1764	510	codIncPisPasep	0	00	DESC. DEVOL.PAGTO A MAIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1765	899	codIncPisPasep	0	00	DESC. PAGTO. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1766	838	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA EM FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1767	638	codIncPisPasep	0	00	DESC. ASSIST. ODONT. DEP. SINTACLUNS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1768	1076	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - MAIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1769	276	codIncPisPasep	0	00	PAGTO. VALE-TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1770	1102	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1771	515	codIncPisPasep	0	00	DESC. SAIDA ANTECIPADA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1772	894	codIncPisPasep	0	00	DESC. ASSIST. ODONTOLOGICA MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1773	702	codIncPisPasep	0	00	DESC. 2ª VIA CARTAO REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1774	115	codIncPisPasep	0	00	HORAS EXTRAS 60% - 09/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
1775	1018	codIncPisPasep	0	00	DESC. VALE REFEICAO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1776	494	codIncPisPasep	0	00	F.G.T.S. S/13º SALARIO DEPOSITADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1777	1080	codIncPisPasep	0	00	H EXTRAS 50% NOT22,50 - SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1778	103	codIncPisPasep	0	00	HORAS EXTRAS 44%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1779	1123	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1780	699	codIncPisPasep	0	00	DESC. ADIANT. DESPESAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1781	185	codIncPisPasep	0	00	INDENIZACAO LEI Nº 7.238/84	automatico	pendente	2026-03-28 03:16:48.023178	\N
1782	340	codIncPisPasep	0	00	DIF. ADICIONAL NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1783	518	codIncPisPasep	0	00	ESTORNO DE PAGAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1784	574	codIncPisPasep	0	00	DESC. DIF. I.R.F.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1785	569	codIncPisPasep	0	00	DESC. I.R.F. S/ PARTICIPACAO NOS LUCROS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1786	594	codIncPisPasep	0	00	DESC. CONTRIB. SOC. LABORAL ANCINE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1787	389	codIncPisPasep	0	00	HORA EXTRA NOTURNA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1788	298	codIncPisPasep	0	00	ADIANT. COMPLEMENTAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1789	204	codIncPisPasep	0	00	DIF. SALARIO 01/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
1790	186	codIncPisPasep	0	00	LOCACAO MOTO/AUTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1791	461	codIncPisPasep	0	00	DESC. FERIAS PARA ABATER DESCONTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1792	488	codIncPisPasep	0	00	DIF. VALE REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1793	366	codIncPisPasep	0	00	DEVOL. I.N.S.S.- FOLHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1794	268	codIncPisPasep	0	00	DIF GRATIFICACAO MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1795	885	codIncPisPasep	0	00	PREMIO ASSIDUIDADE MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1796	1011	codIncPisPasep	0	00	PARTICIPACAO LUCROS/RESULTADOS - 2023	automatico	pendente	2026-03-28 03:16:48.023178	\N
1797	945	codIncPisPasep	0	00	MAO DE OBRA - GARCON  E GARCONETE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1798	958	codIncPisPasep	0	00	DESCONTO HORAS REDUZIDAS ADIC. NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1799	563	codIncPisPasep	0	00	LIQUIDO EM INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1800	405	codIncPisPasep	0	00	MEDIAS FERIAS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1801	1111	codIncPisPasep	0	00	ADIC. INSALUBRIDADE 01/2021 a 08/2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
1802	587	codIncPisPasep	0	00	DESC. CONTRIB. CONFEDERATIVA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1803	900	codIncPisPasep	0	00	VALE LANCHE NAO UTILIZADO MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1804	343	codIncPisPasep	0	00	DIF. VALE REFEICAO CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1805	360	codIncPisPasep	0	00	1/3 ADIC. FERIAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1806	976	codIncPisPasep	0	00	DESCONTO RECESSO FORENSE - GARCON E GARCONETE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1807	640	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1808	910	codIncPisPasep	0	00	MAO DE OBRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1809	205	codIncPisPasep	0	00	DIF. SALARIO 08/2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
1810	985	codIncPisPasep	0	00	HORA CORRIDA REFEICAO 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1811	421	codIncPisPasep	0	00	AJUDA DE CUSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1812	332	codIncPisPasep	0	00	AUXILIO UNIFORME	automatico	pendente	2026-03-28 03:16:48.023178	\N
1813	986	codIncPisPasep	0	00	DIFERENCA ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1814	238	codIncPisPasep	0	00	REEMB. VALE GUELTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1815	639	codIncPisPasep	0	00	ESTORNO DE PAGAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1816	1114	codIncPisPasep	0	00	MULTA POR ATRASO DE SALARIO 2024	automatico	pendente	2026-03-28 03:16:48.023178	\N
1817	394	codIncPisPasep	0	00	DESC. PROGAM.QUALIFI.PROFISSIONAL - PQM	automatico	pendente	2026-03-28 03:16:48.023178	\N
1818	383	codIncPisPasep	0	00	Diferenca Dissidio 2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1819	570	codIncPisPasep	0	00	DESC. I.R.F.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1820	772	codIncPisPasep	0	00	DESC. CESTA BASICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1821	330	codIncPisPasep	0	00	AJUSTE AVISO PREVIO CLAUSULA 28° CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1822	734	codIncPisPasep	0	00	DESC. USO CELULAR DANIFICADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1823	1098	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 MARCO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1824	331	codIncPisPasep	0	00	AUXILIO FILHO EXCEPCIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1825	154	codIncPisPasep	0	00	HORAS REDUZIDAS ADIC. NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1826	202	codIncPisPasep	0	00	ADIC. SALARIO REF. 09/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1827	995	codIncPisPasep	0	00	LICENCA REMUNERADA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1828	864	codIncPisPasep	0	00	ADIC. INSALUBRIDADE SOBRE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1829	853	codIncPisPasep	0	00	HORAS EXTRAS 100% C/ INSALUBRIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1830	104	codIncPisPasep	0	00	HORAS EXTRAS 45%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1831	162	codIncPisPasep	0	00	D.S.R. S/FERIADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1832	732	codIncPisPasep	0	00	DESC. TAXA ADESAO PROMED MG	automatico	pendente	2026-03-28 03:16:48.023178	\N
1833	33	codIncPisPasep	0	00	PREMIO SEGUROS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1834	540	codIncPisPasep	0	00	DESC. SALDO NEGATIVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1835	1115	codIncPisPasep	0	00	MULTA POR ATRASO DE SALARIO 2025	automatico	pendente	2026-03-28 03:16:48.023178	\N
1836	271	codIncPisPasep	0	00	TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1837	818	codIncPisPasep	0	00	DESC. FERIAS PAGAS A MAIS CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1838	1000	codIncPisPasep	0	00	ADIC. NOTURNO C/20% - (HORA EXTRA 100%)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1839	428	codIncPisPasep	0	00	REEMBOLSO DESC. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1840	709	codIncPisPasep	0	00	DESC. AJUSTE DESP DE VIAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1841	356	codIncPisPasep	0	00	BOLSA AUXILIO (ESTAGIARIO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1842	2	codIncPisPasep	0	00	SALARIO MES	automatico	pendente	2026-03-28 03:16:48.023178	\N
1843	812	codIncPisPasep	0	00	REEMBOLSO DE HORAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1844	354	codIncPisPasep	0	00	MEDIAS S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1845	1023	codIncPisPasep	0	00	DIF ADIC. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1846	703	codIncPisPasep	0	00	DESC. 2ª VIA CARTAO RIO CARD	automatico	pendente	2026-03-28 03:16:48.023178	\N
1847	180	codIncPisPasep	0	00	LICENCA PATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1848	562	codIncPisPasep	0	00	DESC. EXTRAVIO CELULAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1849	994	codIncPisPasep	0	00	PARCELAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1850	1035	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1851	1108	codIncPisPasep	0	00	1/3 MEDIAS FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1852	877	codIncPisPasep	0	00	DIF H.E. 100% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1853	936	codIncPisPasep	0	00	MAO DE OBRA - 1/2 OFICIAL ELETRICISTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1854	378	codIncPisPasep	0	00	REEMBOLSO DE UNIFORMES	automatico	pendente	2026-03-28 03:16:48.023178	\N
1856	560	codIncPisPasep	0	00	DESC. FERIAS PAGAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1857	723	codIncPisPasep	0	00	DESC. MAU USO MATERIAL EMPRESA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1858	834	codIncPisPasep	0	00	HORAS EXTRAS 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1859	1033	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1860	712	codIncPisPasep	0	00	DESC. BENEFICIO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1861	1129	codIncPisPasep	0	00	DESC. ATRASOS REF MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1862	1045	codIncPisPasep	0	00	D.S.R. S/SALARIO AULA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1863	164	codIncPisPasep	0	00	D.S.R. COMPETENCIA 08/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
1864	973	codIncPisPasep	0	00	FERIAS (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1865	1020	codIncPisPasep	0	00	DIFERENCA CCT - 05/24 a 07/24	automatico	pendente	2026-03-28 03:16:48.023178	\N
1866	713	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1867	552	codIncPisPasep	0	00	DESC. CONTRIB. ASSISTENCIAL LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1868	397	codIncPisPasep	0	00	DIF - DESP DE VIAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1869	561	codIncPisPasep	0	00	DESC. ANTECIPACAO 13º SALARIO (FERIAS) PARA ABATER	automatico	pendente	2026-03-28 03:16:48.023178	\N
1870	533	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1871	507	codIncPisPasep	0	00	DESC. D.S.R. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1872	1027	codIncPisPasep	0	00	DESCONTO DE NÃO DEV. DO MATERIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1873	9284	codIncPisPasep	0	00	VALE ALIMENTACAO (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1874	542	codIncPisPasep	0	00	DESC. ADIANT. NORMAL(DENTRO DO MES)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1875	735	codIncPisPasep	0	00	HORAS EXTRAS INSAL 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1876	622	codIncPisPasep	0	00	DESC. VT NAO UTILIZADO MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1877	1065	codIncPisPasep	0	00	HORAS EXTRAS 50% - JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1878	718	codIncPisPasep	0	00	DESC. CONVENIO FARMACIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1879	9278	codIncPisPasep	0	00	CESTA BASICA (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1880	1092	codIncPisPasep	0	00	HORAS EXTRAS 100% SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1881	257	codIncPisPasep	0	00	ABONO DE FERIAS ARTº 143 (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1882	751	codIncPisPasep	0	00	DESC. CESTA BASICA NAO UTILIZADA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1883	596	codIncPisPasep	0	00	DESC. I.N.S.S. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1884	692	codIncPisPasep	0	00	DESC. 2 VIA CARTAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1885	789	codIncPisPasep	0	00	DESC. CARTAO SALARIO - DEMISSAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1886	36	codIncPisPasep	0	00	DIF.CONV COLETIVA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1887	196	codIncPisPasep	0	00	HORAS DOBRADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1888	1127	codIncPisPasep	0	00	DEVOLUCAO PROVISAO DESC EMPREST ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1889	636	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1890	384	codIncPisPasep	0	00	EMPRESTIMO FOLHA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1891	573	codIncPisPasep	0	00	DESC. I.R.F. S/ PARTICIPACAO NOS LUCROS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1892	338	codIncPisPasep	0	00	D.S.R. SOBRE HORAS EXTRAS / AD. NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1893	323	codIncPisPasep	0	00	HORA FICTA SEAC	automatico	pendente	2026-03-28 03:16:48.023178	\N
1894	768	codIncPisPasep	0	00	ADIC. 13º SALARIO S/AVISO PREVIO (Lei 12.506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1895	30	codIncPisPasep	0	00	PREMIO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1896	3	codIncPisPasep	0	00	BOLSA AUXILIO (ESTAGIARIO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1897	776	codIncPisPasep	0	00	DESC. VALE ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1898	9279	codIncPisPasep	0	00	ASSISTENCIA MEDICA (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1899	94	codIncPisPasep	0	00	H EXTRAS DIF 50% X 60%- MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1900	90	codIncPisPasep	0	00	HORAS A COMPENSAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1901	748	codIncPisPasep	0	00	DESC. JUDICIAL - 2	automatico	pendente	2026-03-28 03:16:48.023178	\N
1902	937	codIncPisPasep	0	00	DEMONSTRATIVO DE HORAS EXTRAS 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1903	129	codIncPisPasep	0	00	HORAS EXTRAS 110%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1904	755	codIncPisPasep	0	00	REEMB. VALE TRANSPORTE - HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1905	248	codIncPisPasep	0	00	REEMB  CONTRIB. ASSIST	automatico	pendente	2026-03-28 03:16:48.023178	\N
1906	597	codIncPisPasep	0	00	DESC. D.S.R. S/FALTAS (DIAS) MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1907	747	codIncPisPasep	0	00	DIF. ADIC. INSALUBRIDADE CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1908	930	codIncPisPasep	0	00	REPACTUAÇÃO DE CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1909	66	codIncPisPasep	0	00	ADIC. NOTURNO MES ANT 20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1910	858	codIncPisPasep	0	00	HORAS NORMAIS MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1911	102	codIncPisPasep	0	00	HORAS EXTRAS 60%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1912	648	codIncPisPasep	0	00	DESC. CONTRIB. SOCIAL SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1913	147	codIncPisPasep	0	00	REEMB. DESC. V REFEIC N UTILIZ	automatico	pendente	2026-03-28 03:16:48.023178	\N
1914	69	codIncPisPasep	0	00	ADIC. PERICULOSIDADE MES ANTER	automatico	pendente	2026-03-28 03:16:48.023178	\N
1915	652	codIncPisPasep	0	00	REDUCAO JORNADA COVID - 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1916	1106	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1917	815	codIncPisPasep	0	00	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1918	439	codIncPisPasep	0	00	HORAS EXTRAS 100% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1919	695	codIncPisPasep	0	00	DESC. HORAS NORMAIS DEBITO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1920	9	codIncPisPasep	0	00	SALARIO NORMATIVO -VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
1921	532	codIncPisPasep	0	00	DESC. CONTRIB. COFEDERATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1922	959	codIncPisPasep	0	00	DESCONTO DE DIFERENÇA DE REPACTUAÇÃO DE VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1923	275	codIncPisPasep	0	00	VALE REFEIÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1924	957	codIncPisPasep	0	00	DESCONTO DE 7 DIAS REF. REAJUSTE CONTRATUAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1925	173	codIncPisPasep	0	00	ACIDENTE DE TRABALHO (F.G.T.S.)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1926	335	codIncPisPasep	0	00	AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1927	133	codIncPisPasep	0	00	HORAS EXTRAS 150%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1928	325	codIncPisPasep	0	00	HORA FICTA SEAC - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1929	629	codIncPisPasep	0	00	DESC HE 100 - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1930	827	codIncPisPasep	0	00	DESCONTO JUDICIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1931	618	codIncPisPasep	0	00	DESC. ASS. MÉDICA MES ANT FIOCRUZ	automatico	pendente	2026-03-28 03:16:48.023178	\N
1932	1135	codIncPisPasep	0	00	ADIC. PERICULOSIDADE MES 01/2026	automatico	pendente	2026-03-28 03:16:48.023178	\N
1933	469	codIncPisPasep	0	00	13º SALARIO S/SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1934	582	codIncPisPasep	0	00	DESC. CONTRIB. COL. LAB. SINTACLUNS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1935	491	codIncPisPasep	0	00	FERIAS (FATURAMENTO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1936	398	codIncPisPasep	0	00	DIF-DESC. AJUSTE DESP DE VIAGENS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1937	117	codIncPisPasep	0	00	HORAS EXTRAS 65%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1938	924	codIncPisPasep	0	00	FATURAMENTO DE 13º SALARIO 2º PARCELA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1939	264	codIncPisPasep	0	00	MULTA VIGESIMA SETIMA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1940	209	codIncPisPasep	0	00	DIF. SALARIO 07/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
1941	624	codIncPisPasep	0	00	DESC. VALE REFEIÇÃO - CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1942	348	codIncPisPasep	0	00	1/3 FERIAS VENCIDAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1943	194	codIncPisPasep	0	00	F.G.T.S. MES ANTERIOR (TEMP)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1944	135	codIncPisPasep	0	00	D.S.R. S/HORA EXTRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1945	842	codIncPisPasep	0	00	DESC. CONTRIB. NEGOCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1946	261	codIncPisPasep	0	00	REEMB. CONTRIBUICOES	automatico	pendente	2026-03-28 03:16:48.023178	\N
1947	637	codIncPisPasep	0	00	DESC. CONTRIB. COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1948	371	codIncPisPasep	0	00	13º SALARIO PROP. S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1949	938	codIncPisPasep	0	00	DIFERENCA DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1950	473	codIncPisPasep	0	00	ARTIGO 071	automatico	pendente	2026-03-28 03:16:48.023178	\N
1951	48	codIncPisPasep	0	00	DIF. DISSIDIO - 11/2008	automatico	pendente	2026-03-28 03:16:48.023178	\N
1952	771	codIncPisPasep	0	00	DESC. VALE REFEICAO NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1953	807	codIncPisPasep	0	00	DESC. FERIAS PAGAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1954	932	codIncPisPasep	0	00	MAO DE OBRA - 1/2 OFICIAL BORRACHEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1955	128	codIncPisPasep	0	00	HORAS EXTRAS 100% + ADIC. NOT. 35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1956	37	codIncPisPasep	0	00	DIF. DISSIDIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1957	826	codIncPisPasep	0	00	INDENIZACAO ARTº 480	automatico	pendente	2026-03-28 03:16:48.023178	\N
1958	671	codIncPisPasep	0	00	DESC. VALE-TRANSPORTE NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1959	156	codIncPisPasep	0	00	DIF. FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1960	969	codIncPisPasep	0	00	DESCONTO REF. RECESSO FORENSE	automatico	pendente	2026-03-28 03:16:48.023178	\N
1961	797	codIncPisPasep	0	00	ADIANTAMENTO - (PGTO FÉRIAS - COM INCIDENCIA)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1962	99	codIncPisPasep	0	00	HORAS EXTRAS 10/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1963	1037	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1964	1109	codIncPisPasep	0	00	ADIC. NOTURNO C/25%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1965	1041	codIncPisPasep	0	00	PAGTO. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
1966	22	codIncPisPasep	0	00	DIF. CCT - 2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1967	875	codIncPisPasep	0	00	DEV. D.S.R FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1968	14	codIncPisPasep	0	00	REEMB. CONTRIBUICAO COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1969	191	codIncPisPasep	0	00	REINTEGRAÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1970	836	codIncPisPasep	0	00	ADIC. NOTURNO C/20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1971	29	codIncPisPasep	0	00	PREMIO L.B. VENDAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1972	464	codIncPisPasep	0	00	DIF. 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1973	585	codIncPisPasep	0	00	DESC. MENS. SINDICAL MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1974	1060	codIncPisPasep	0	00	HORAS EXTRAS 50% - FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1975	137	codIncPisPasep	0	00	REEMB. EXAME ADMISSIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
1976	556	codIncPisPasep	0	00	DESC. MEDIAS ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1977	80	codIncPisPasep	0	00	HORAS NOTURNAS REDUZIDAS 35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1978	912	codIncPisPasep	0	00	SUBSTITUICAO DE FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1979	28	codIncPisPasep	0	00	PREMIO GAR EXTEN MOVEIS - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
1980	598	codIncPisPasep	0	00	DESC PAGTO A MAIOR AD NOT	automatico	pendente	2026-03-28 03:16:48.023178	\N
1981	1007	codIncPisPasep	0	00	DESC. MULTA 40% - REITEGRAÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1982	984	codIncPisPasep	0	00	HORA CORRIDA REFEICAO 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
1983	431	codIncPisPasep	0	00	DEVOLUCAO DESC. MULTAS TRANSITO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1984	897	codIncPisPasep	0	00	DESC. ANTECIPACAO VA E VR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1985	1029	codIncPisPasep	0	00	ADIC. NOTURNO C/20% - MES ANTERIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
1986	223	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 09/11	automatico	pendente	2026-03-28 03:16:48.023178	\N
1987	967	codIncPisPasep	0	00	HORAS EXTRAS 30% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1988	861	codIncPisPasep	0	00	DESC. D.S.R. S/FALTAS (HORAS) MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
1989	1	codIncPisPasep	0	00	HORAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1991	422	codIncPisPasep	0	00	ANTECIPACAO DE PGTO.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1992	528	codIncPisPasep	0	00	DESC. QUEBRA CAIXA (FALTA DE  CAIXA)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1993	369	codIncPisPasep	0	00	1/3 FERIAS S/AVISO PREVIO INDENIZADO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1994	495	codIncPisPasep	0	00	COMPLEMENTO D.S.	automatico	pendente	2026-03-28 03:16:48.023178	\N
1995	1032	codIncPisPasep	0	00	D.S.R (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
1996	26	codIncPisPasep	0	00	PREMIO DOMINGOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
1997	478	codIncPisPasep	0	00	ARTIGO 477	automatico	pendente	2026-03-28 03:16:48.023178	\N
1998	201	codIncPisPasep	0	00	ADIC. SALARIO REF. 08/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
1999	85	codIncPisPasep	0	00	HORAS EXTRAS REF.DIF 50 x100	automatico	pendente	2026-03-28 03:16:48.023178	\N
2000	660	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA MES ANTERIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2001	738	codIncPisPasep	0	00	ADIC.INSALUB.ACORDO TRAB	automatico	pendente	2026-03-28 03:16:48.023178	\N
2002	247	codIncPisPasep	0	00	DIF. SALARIO FAMILIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2003	580	codIncPisPasep	0	00	INDENIZACAO ARTº 480	automatico	pendente	2026-03-28 03:16:48.023178	\N
2004	84	codIncPisPasep	0	00	NONA HORA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2005	690	codIncPisPasep	0	00	DESC. VA E VR DIF CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2006	1101	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2007	146	codIncPisPasep	0	00	DEV. D.S.R. S/FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2008	658	codIncPisPasep	0	00	DESC. PENSAO ALIM S/ Férias	automatico	pendente	2026-03-28 03:16:48.023178	\N
2009	683	codIncPisPasep	0	00	DIF CCT 2021 - FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2010	418	codIncPisPasep	0	00	1/3 S/ADIC. ABONO FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2011	303	codIncPisPasep	0	00	REEMB. DESC. FALTAS E ATRASOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2012	111	codIncPisPasep	0	00	HORAS EXTRAS 55%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2013	406	codIncPisPasep	0	00	1/3 MEDIAS FERIAS (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2014	105	codIncPisPasep	0	00	HORAS EXTRAS 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2015	922	codIncPisPasep	0	00	FATURAMENTO DE REEMBOLSO DE ATESTADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2016	1064	codIncPisPasep	0	00	HORAS EXTRAS 50% - JUNHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2017	152	codIncPisPasep	0	00	DIF. AD. INSALUBRIDADE REF. 12/2014 A 09/2015	automatico	pendente	2026-03-28 03:16:48.023178	\N
2018	578	codIncPisPasep	0	00	DESC. VALE LANCHE NAO UTILIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2019	665	codIncPisPasep	0	00	DIF CCT COMPUS MP936	automatico	pendente	2026-03-28 03:16:48.023178	\N
2020	871	codIncPisPasep	0	00	H.EXTRA  NOTURNO C/100% MÊS ANT.	automatico	pendente	2026-03-28 03:16:48.023178	\N
2021	621	codIncPisPasep	0	00	DESC. BB DETAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2022	656	codIncPisPasep	0	00	DESC. PENSAO ALIMENTICIA S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2023	557	codIncPisPasep	0	00	DESC. ADIC. PERICULOSIDADE S/1ª PARCEL 13ª SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2024	991	codIncPisPasep	0	00	REEMB. FALTAS D.S.R (HORAS) - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2025	254	codIncPisPasep	0	00	REEMB. MENSALIDADE. SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2026	373	codIncPisPasep	0	00	1/3 FERIAS S/AVISO PREVIO INDENIZADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2027	344	codIncPisPasep	0	00	DIFERENCA DE DISSIDIO 07 2012	automatico	pendente	2026-03-28 03:16:48.023178	\N
2028	1038	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2029	362	codIncPisPasep	0	00	ADIC. INSALUBRIDADE S/FERIAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2030	388	codIncPisPasep	0	00	FERIAS VENCIDAS INDENIZ. S/VAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2031	696	codIncPisPasep	0	00	ABONO PECUNIARIO RODOVIARIOS 2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
2032	70	codIncPisPasep	0	00	ADIC. PERICULOSIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2033	970	codIncPisPasep	0	00	PARTICIPACAO LUCROS/RESULTADOS SÓCIOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2034	746	codIncPisPasep	0	00	DIFERENCA CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2035	38	codIncPisPasep	0	00	DIF. DISSIDIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2036	9285	codIncPisPasep	0	00	BENEFICIO OUTROS (INFORMATIIVO ESOCIAL)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2037	698	codIncPisPasep	0	00	DESC. ADIANT. COMISSOES	automatico	pendente	2026-03-28 03:16:48.023178	\N
2038	988	codIncPisPasep	0	00	*** BASE IRRF ***	automatico	pendente	2026-03-28 03:16:48.023178	\N
2039	603	codIncPisPasep	0	00	DESC. ASS. MÉDICA BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
2040	888	codIncPisPasep	0	00	DESC. D.S.R. S/FALTAS (Horas)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2041	98	codIncPisPasep	0	00	HORAS EXTRAS 09/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
2042	999	codIncPisPasep	0	00	PARCELAMENTO 3	automatico	pendente	2026-03-28 03:16:48.023178	\N
2043	262	codIncPisPasep	0	00	HORAS EXTRAS 60% - MES 04-2017	automatico	pendente	2026-03-28 03:16:48.023178	\N
2044	811	codIncPisPasep	0	00	ACUMULO DE FUNCAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2045	409	codIncPisPasep	0	00	FERIAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2046	896	codIncPisPasep	0	00	DESC. CO PARTICIPACAO A.M. Mês Anterior	automatico	pendente	2026-03-28 03:16:48.023178	\N
2047	840	codIncPisPasep	0	00	ADIC. PERICULOSIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2048	122	codIncPisPasep	0	00	HORAS EXTRAS 75%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2049	57	codIncPisPasep	0	00	ADIC. NOTURNO C/35%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2050	685	codIncPisPasep	0	00	DESC. ADIANTAMENTO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2051	215	codIncPisPasep	0	00	HORAS DOBRADAS - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2052	1016	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2053	794	codIncPisPasep	0	00	REEMBOLSO SEGURO DE VIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2054	424	codIncPisPasep	0	00	AUXILIO FUNERAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2055	576	codIncPisPasep	0	00	DESC. VALE TRANSP. NAO UTILIZADO PROX MES	automatico	pendente	2026-03-28 03:16:48.023178	\N
2056	1049	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - MARCO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2057	814	codIncPisPasep	0	00	ADIC. INSALUBRIDADE SOBRE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2058	1057	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2059	404	codIncPisPasep	0	00	DIF. FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2060	610	codIncPisPasep	0	00	DESC. VT NAO UTILIZADO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2061	998	codIncPisPasep	0	00	PARCELAMENTO 2	automatico	pendente	2026-03-28 03:16:48.023178	\N
2062	132	codIncPisPasep	0	00	HORAS EXTRAS 130%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2063	630	codIncPisPasep	0	00	DESC H EXTRAS 60% - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2064	81	codIncPisPasep	0	00	HORAS REDUZIDAS ADIC. NOT MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2065	604	codIncPisPasep	0	00	DESC BASE SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2066	524	codIncPisPasep	0	00	DESC. DIF. SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2067	1084	codIncPisPasep	0	00	HORAS EXTRAS 100% - JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2068	244	codIncPisPasep	0	00	HORAS EXTRAS 50% - 04/2017	automatico	pendente	2026-03-28 03:16:48.023178	\N
2069	577	codIncPisPasep	0	00	DESC. VA NAO UTILIZADO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2070	756	codIncPisPasep	0	00	DIF 1/3 S/ABONO FERIAS ARTº 143 (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2071	62	codIncPisPasep	0	00	ADIC. INSALUBRIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2072	312	codIncPisPasep	0	00	COMPLEMENTO PGTO.	automatico	pendente	2026-03-28 03:16:48.023178	\N
2073	804	codIncPisPasep	0	00	SOBRE AVISO- MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2074	878	codIncPisPasep	0	00	DESC. ATRASOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2075	551	codIncPisPasep	0	00	DESC. ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2076	289	codIncPisPasep	0	00	MEDIAS ANTECIPACAO 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2077	43	codIncPisPasep	0	00	DIF. DISSIDIO - 04/2012	automatico	pendente	2026-03-28 03:16:48.023178	\N
2078	798	codIncPisPasep	0	00	ADIC. PERIC. S/AVISO PREVIO INDENIZADO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2079	308	codIncPisPasep	0	00	BENEFICIOS GERENTES	automatico	pendente	2026-03-28 03:16:48.023178	\N
2080	83	codIncPisPasep	0	00	HORAS REDUZIDAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2081	32	codIncPisPasep	0	00	PREMIO PRODUTIVIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2082	314	codIncPisPasep	0	00	DIF. CESTA BASICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2083	620	codIncPisPasep	0	00	DESC. ASS. MÉDICA DEP. MES ANT FIOCRUZ	automatico	pendente	2026-03-28 03:16:48.023178	\N
2084	252	codIncPisPasep	0	00	AJUDA CRECHE CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2085	921	codIncPisPasep	0	00	FATURAMENTO DE MATERIAL DE LIMPEZA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2086	12	codIncPisPasep	0	00	DIF. SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2087	1026	codIncPisPasep	0	00	PAGTO. VT E VA - REF FERIADOS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2088	813	codIncPisPasep	0	00	DIF. SALARIO MATERNIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2089	329	codIncPisPasep	0	00	ABONO 50% - clausula 32 item V CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2090	229	codIncPisPasep	0	00	REEMB. CESTA PREMIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2091	742	codIncPisPasep	0	00	DIF. CCT 2022	automatico	pendente	2026-03-28 03:16:48.023178	\N
2092	46	codIncPisPasep	0	00	DIF. DISSIDIO - 10/2009	automatico	pendente	2026-03-28 03:16:48.023178	\N
2093	1107	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 DEZEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2094	765	codIncPisPasep	0	00	DESC. ASSIST. ODONT. MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2095	396	codIncPisPasep	0	00	DEVOL. I.N.S.S. - 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2096	762	codIncPisPasep	0	00	DESC. MENSALIDADE SINDICAL - BA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2097	749	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2098	1066	codIncPisPasep	0	00	HORAS EXTRAS 50% - AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2099	917	codIncPisPasep	0	00	REAJUSTE CONFORME CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2100	882	codIncPisPasep	0	00	REEMB. DESC. VALE REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2101	50	codIncPisPasep	0	00	SALARIO AUTONOMO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2102	662	codIncPisPasep	0	00	PENSAO INDENIZATORIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2103	481	codIncPisPasep	0	00	ADIC. 13º SALARIO S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2104	641	codIncPisPasep	0	00	DESC. I.N.S.S. (FÉRIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2105	138	codIncPisPasep	0	00	DIA DO RODOVIARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2106	72	codIncPisPasep	0	00	DIF - AJUD FILHO DEFICIENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2107	833	codIncPisPasep	0	00	DESC. HORAS PAGAS A MAIS NO MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2108	149	codIncPisPasep	0	00	REEMB D.S.R MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2109	633	codIncPisPasep	0	00	DESC H EXTRAS 100% - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2110	1090	codIncPisPasep	0	00	HORAS EXTRAS 100% JULHO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2111	341	codIncPisPasep	0	00	DIF. CCT/2019	automatico	pendente	2026-03-28 03:16:48.023178	\N
2112	916	codIncPisPasep	0	00	DISSIDIO CONFORME CONTRATO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2113	274	codIncPisPasep	0	00	TRANSPORTE SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2114	731	codIncPisPasep	0	00	DESC. TARIFA BANCARIA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2115	654	codIncPisPasep	0	00	FATURAMENTO DE SUSPENSAO - GARCOM/GARCONETE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2116	286	codIncPisPasep	0	00	REEMB. VALE TRANSP. TREINAMENTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2117	114	codIncPisPasep	0	00	HORAS EXTRAS 60% - 05/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
2118	1005	codIncPisPasep	0	00	REEMBOLSO DESC. INDEVIDO - HORA EXTRA + DSR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2119	150	codIncPisPasep	0	00	H E 100% - SUMULA 444 - MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2120	256	codIncPisPasep	0	00	REEMB. DESC. REFEICAO (PAT)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2121	687	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2122	190	codIncPisPasep	0	00	REEMB. FALTAS DESC. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2123	67	codIncPisPasep	0	00	DIF. ADIC. INSALUBRIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2124	968	codIncPisPasep	0	00	DESCONTO REF. FALTAS - 1/2 OFICIAL ELETRICISTA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2125	79	codIncPisPasep	0	00	HORAS NOTURNAS REDUZIDAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2126	550	codIncPisPasep	0	00	DESC. PAGTO. INDEVIDO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2127	857	codIncPisPasep	0	00	DESC. ATRASO/FALTA HORAS MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2128	455	codIncPisPasep	0	00	ADIC. INSAL 12092018 27022019	automatico	pendente	2026-03-28 03:16:48.023178	\N
2129	664	codIncPisPasep	0	00	DESC. VALE ALIMENTACAO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2130	232	codIncPisPasep	0	00	REEMB. EXAME DEMISSIONAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2131	228	codIncPisPasep	0	00	REEMB. DESC. ASSIST. MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2132	1040	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2133	58	codIncPisPasep	0	00	ADIC. NOTURNO C/40%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2134	911	codIncPisPasep	0	00	FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2135	1054	codIncPisPasep	0	00	ADIC. NOTURNO 22,50% - AGOSTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2136	1130	codIncPisPasep	0	00	DESC. ASS. MÉDICA DEP. MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2137	770	codIncPisPasep	0	00	DESC. ADIANT. VALE REFEIÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2138	852	codIncPisPasep	0	00	HORAS EXTRAS 50% C/ INSALUBRIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2139	106	codIncPisPasep	0	00	HORAS EXTRAS 50% - 08/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
2140	352	codIncPisPasep	0	00	ADIC. PERICULOSIDADE S/FERIAS NORMAIS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2141	211	codIncPisPasep	0	00	DIF. SALARIO 09/2014 TEOFILO OTONI	automatico	pendente	2026-03-28 03:16:48.023178	\N
2142	1071	codIncPisPasep	0	00	MEDIAS FERIAS EM DOBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2143	432	codIncPisPasep	0	00	DEVOLUCAO PENDEN PREST CONTAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2144	940	codIncPisPasep	0	00	GRATIFICAÇÃO MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2145	52	codIncPisPasep	0	00	ADIC. NOTURNO C/20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2146	499	codIncPisPasep	0	00	DIF. VALE-TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2147	590	codIncPisPasep	0	00	DESC. CONTRIB. ASSISTENCIAL MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2148	785	codIncPisPasep	0	00	ABONO PECUNIARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2149	401	codIncPisPasep	0	00	PREMIO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2150	782	codIncPisPasep	0	00	1/3 ADIC. FERIAS S/AVISO PREVIO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2151	737	codIncPisPasep	0	00	DESC. VALE COMPRA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2152	905	codIncPisPasep	0	00	MAO DE OBRA AUXILIAR OPER BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
2153	766	codIncPisPasep	0	00	DESC. ASSIST. ODONT. DEP. MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2154	1036	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2155	567	codIncPisPasep	0	00	LIQ EM DUPLIC 07-2015 13ºSAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2156	714	codIncPisPasep	0	00	DESC. BENEFÍCIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2157	65	codIncPisPasep	0	00	ADIC. NOTURNO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2158	446	codIncPisPasep	0	00	GRATIFICACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2159	829	codIncPisPasep	0	00	PROCESSO TRAB	automatico	pendente	2026-03-28 03:16:48.023178	\N
2160	972	codIncPisPasep	0	00	SALARIO DIA (INTERMITENTE) MES ANT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2161	1094	codIncPisPasep	0	00	HORAS EXTRAS 100% NOVEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2162	258	codIncPisPasep	0	00	1/3 S/ABONO FERIAS ARTº 143 (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2163	784	codIncPisPasep	0	00	DESC. VT DIF SAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2164	953	codIncPisPasep	0	00	DESCONTO DE VR REF. RECESSO FORENSE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2165	903	codIncPisPasep	0	00	MAO DE OBRA ENCARREGADO BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
2166	1010	codIncPisPasep	0	00	ADIC. INSALUBRIDADE SOBRE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2167	493	codIncPisPasep	0	00	13º SALARIO (FATURAMENTO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2168	500	codIncPisPasep	0	00	DESC. FALTAS (DIAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2169	823	codIncPisPasep	0	00	FERIAS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2170	483	codIncPisPasep	0	00	F.G.T.S. MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2171	1025	codIncPisPasep	0	00	LICENCA GESTANTE POR ABORTO NAO CRIMINOSO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2172	608	codIncPisPasep	0	00	DESC. CONTRIB. COLABORATIVA LABORAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2173	846	codIncPisPasep	0	00	DESC. ADIANT. DESPESAS - INVISIVEL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2174	767	codIncPisPasep	0	00	DESC. PAGTO. SALARIO INDEV.	automatico	pendente	2026-03-28 03:16:48.023178	\N
2175	460	codIncPisPasep	0	00	FERIAS PARA ABATER DESCONTO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2176	850	codIncPisPasep	0	00	ADIC. NOTURNO C/100% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2177	349	codIncPisPasep	0	00	AVISO PREVIO INDENIZADO (Lei 12506)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2178	241	codIncPisPasep	0	00	SALÁRIO FAMILIA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2179	996	codIncPisPasep	0	00	F.G.T.S. PAGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2180	382	codIncPisPasep	0	00	BOLSA AUXILIO (ESTAGIARIO)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2181	485	codIncPisPasep	0	00	DIF. ASSISTENCIA ODONTOLOGICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2182	890	codIncPisPasep	0	00	DESC. PAGTO. SALARIO INDEV. MÊS ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2183	678	codIncPisPasep	0	00	DESC. VALE-TRANSPORTE 06% - 02/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
2184	326	codIncPisPasep	0	00	1/3 FERIAS COMPLEMENTARES(VLR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2185	1046	codIncPisPasep	0	00	ADICIONAL EXTRACLASSE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2186	408	codIncPisPasep	0	00	1/3 MEDIAS FERIAS S/ABONO (Ferias)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2187	423	codIncPisPasep	0	00	AUXILIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2188	830	codIncPisPasep	0	00	DESC. ADTO (PGTO FÉRIAS - COM INCIDENCIA)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2189	444	codIncPisPasep	0	00	DIF. VA E VR - CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2190	76	codIncPisPasep	0	00	DIF. HORAS EXTRAS DISSIDIO 04/2010	automatico	pendente	2026-03-28 03:16:48.023178	\N
2191	605	codIncPisPasep	0	00	DESC. ASSIST. ODONTO. DEPENDENTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2192	363	codIncPisPasep	0	00	EMPRESTIMO SALDO NEGATIVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2193	700	codIncPisPasep	0	00	DESC. F.G.T.S. DEPOSITO RESCISAO - G.R.F.C.	automatico	pendente	2026-03-28 03:16:48.023178	\N
2194	844	codIncPisPasep	0	00	FGTS COMPLEMENTAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2195	306	codIncPisPasep	0	00	REEMB. VALE-TRANSPORTE REF. EXTRAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2196	601	codIncPisPasep	0	00	DESC. AUXILIO DOENCA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2197	297	codIncPisPasep	0	00	COMPLEMENTO PREVIDENCIARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2198	426	codIncPisPasep	0	00	COMBUSTIVEL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2199	457	codIncPisPasep	0	00	ADIC. NOTURNO C/20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2200	1350	codIncPisPasep	0	00	FERIAS (ANTECIPAÇÃO) - ESOCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2201	792	codIncPisPasep	0	00	PREMIO ASSIDUIDADE (SEM INCIDENCIA)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2202	277	codIncPisPasep	0	00	PAGTO. VALE REFEICAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2203	710	codIncPisPasep	0	00	DESC. ALIMENTACAO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2204	302	codIncPisPasep	0	00	REEMB. DESC.VALE TRANSPORTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2205	109	codIncPisPasep	0	00	HORAS EXTRAS 50% + ADIC NOT 20	automatico	pendente	2026-03-28 03:16:48.023178	\N
2206	21	codIncPisPasep	0	00	SALARIO SUBSTITUTO MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2207	100	codIncPisPasep	0	00	HORAS EXTRAS 20%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2208	928	codIncPisPasep	0	00	REPACTUACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2209	375	codIncPisPasep	0	00	ADIC. 13º SALARIO S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2210	534	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2211	763	codIncPisPasep	0	00	DESC. MENSALIDADE SINDICAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2212	213	codIncPisPasep	0	00	ABONO DE SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2213	230	codIncPisPasep	0	00	REEMB. DESC. CONF./ASSI	automatico	pendente	2026-03-28 03:16:48.023178	\N
2214	1013	codIncPisPasep	0	00	REEMB. DESC. PENSAO ALIMENTICIA SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2215	884	codIncPisPasep	0	00	ABONO - SEERC	automatico	pendente	2026-03-28 03:16:48.023178	\N
2216	27	codIncPisPasep	0	00	PREMIO GAR EXTEN ELETRO - VEND	automatico	pendente	2026-03-28 03:16:48.023178	\N
2217	825	codIncPisPasep	0	00	13º SALÁRIO (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2218	452	codIncPisPasep	0	00	DESC GRAT - EXECUTIVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2219	927	codIncPisPasep	0	00	MOTORISTA EVENTUAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2220	89	codIncPisPasep	0	00	HORA REDUZIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2221	666	codIncPisPasep	0	00	COMPL AJ COMPUSORIA MP936	automatico	pendente	2026-03-28 03:16:48.023178	\N
2222	412	codIncPisPasep	0	00	1/3 ADIC. FERIAS MES SEGUINTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2223	599	codIncPisPasep	0	00	DESC H.E PAGO MAIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2224	538	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2225	167	codIncPisPasep	0	00	D.S.R. COMPETENCIA 11/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
2226	1128	codIncPisPasep	0	00	DIF ADIC. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2227	1126	codIncPisPasep	0	00	PROVISAO DESC EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2228	553	codIncPisPasep	0	00	DESC. 13º SALARIO PAGO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2229	824	codIncPisPasep	0	00	1/3 FERIAS (INTERMITENTE)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2230	293	codIncPisPasep	0	00	F.G.T.S. S/13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2231	512	codIncPisPasep	0	00	DESC. FALTAS HORAS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2232	490	codIncPisPasep	0	00	DIF. ASSISTENCIA MEDICA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2233	1015	codIncPisPasep	0	00	REEMBOLSO DE GRATIFICACAO ASSIDUIDADE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2234	175	codIncPisPasep	0	00	SAIDAS ABONADAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2235	322	codIncPisPasep	0	00	TEMPO DE ESPERA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2236	78	codIncPisPasep	0	00	HORAS NOTURNAS 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2237	123	codIncPisPasep	0	00	HORAS EXTRAS 100%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2238	887	codIncPisPasep	0	00	DESC. FALTAS (Horas)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2239	674	codIncPisPasep	0	00	DESC. DEV VT RED TARIFA TRANSPORTES	automatico	pendente	2026-03-28 03:16:48.023178	\N
2240	318	codIncPisPasep	0	00	DIF. VENDA MOVEIS MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2241	982	codIncPisPasep	0	00	DESCONTO REF. FALTAS AUXILIAR OPER BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
2242	127	codIncPisPasep	0	00	HORAS EXTRAS 100% - MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2243	816	codIncPisPasep	0	00	DESC. 1/3 FERIAS PAGAS A MAIS CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2244	981	codIncPisPasep	0	00	DESCONTO REF. FALTAS ALMOXARIFE BACEN	automatico	pendente	2026-03-28 03:16:48.023178	\N
2245	1125	codIncPisPasep	0	00	DESC. HORAS A COMPENSAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2246	206	codIncPisPasep	0	00	DIF. SALARIO 09/2021	automatico	pendente	2026-03-28 03:16:48.023178	\N
2247	468	codIncPisPasep	0	00	CLAUSULA 22ª CCT TRT SP 08/13	automatico	pendente	2026-03-28 03:16:48.023178	\N
2248	10	codIncPisPasep	0	00	GRATIFICAÇÃO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2249	832	codIncPisPasep	0	00	DIF. VALE ALIMENTACAO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2250	475	codIncPisPasep	0	00	ARTIGO 071 TRT EMERGENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2251	34	codIncPisPasep	0	00	PREMIO SEGUROS GER	automatico	pendente	2026-03-28 03:16:48.023178	\N
2252	862	codIncPisPasep	0	00	ADIC. NOTURNO C/20% MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2253	142	codIncPisPasep	0	00	ADIC. NOTURNO C/34%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2254	435	codIncPisPasep	0	00	ADIC. FERIAS MES SEGUINTE	automatico	pendente	2026-03-28 03:16:48.023178	\N
2255	1067	codIncPisPasep	0	00	HORAS EXTRAS 50% - SETEMBRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2256	477	codIncPisPasep	0	00	TRIBUTO S/BENEFICIO (NÃO UTILIZAR)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2257	290	codIncPisPasep	0	00	ADIC. PERICULOSIDADE S/1ª PARCELA 13º SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2258	913	codIncPisPasep	0	00	FATURAMENTO DE VT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2259	1121	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2260	715	codIncPisPasep	0	00	DESC. PAGOS ANTECIPADO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2261	536	codIncPisPasep	0	00	DESC. BENEFICIO SOCIAL FAMILIAR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2262	854	codIncPisPasep	0	00	DESC. CREDENCIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2263	280	codIncPisPasep	0	00	DIF. AJUDA CRECHE CCT	automatico	pendente	2026-03-28 03:16:48.023178	\N
2264	486	codIncPisPasep	0	00	F.G.T.S. 13º  FATURADO 1 AVO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2265	82	codIncPisPasep	0	00	HORAS REDUZIDAS ADIC. NOTURNO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2266	437	codIncPisPasep	0	00	ADIC. S/ABONO FERIAS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2267	514	codIncPisPasep	0	00	DESC. FALTA DEVOLUCAO MATERIAL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2268	1097	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 FEVEREIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2269	1099	codIncPisPasep	0	00	H EXTRAS 100% NOT 22,50 ABRIL	automatico	pendente	2026-03-28 03:16:48.023178	\N
2270	392	codIncPisPasep	0	00	HORAS INTERJORN 50%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2271	870	codIncPisPasep	0	00	ADICIONAL DE ESTIMULO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2272	1039	codIncPisPasep	0	00	DESC. EMPRESTIMO ECONSIGNADO FGTS	automatico	pendente	2026-03-28 03:16:48.023178	\N
2273	203	codIncPisPasep	0	00	ADIC. SALARIO REF. 10/2014	automatico	pendente	2026-03-28 03:16:48.023178	\N
2274	124	codIncPisPasep	0	00	HORAS EXTRAS 100% - DIF	automatico	pendente	2026-03-28 03:16:48.023178	\N
2275	168	codIncPisPasep	0	00	D.S.R. COMPETENCIA 12/2011	automatico	pendente	2026-03-28 03:16:48.023178	\N
2276	359	codIncPisPasep	0	00	ADIC. FERIAS INDENIZADAS (Rescisao)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2277	219	codIncPisPasep	0	00	REEMB. HORAS EXTRAS 03/14	automatico	pendente	2026-03-28 03:16:48.023178	\N
2278	803	codIncPisPasep	0	00	ADIC. PERIC. S/13º SALARIO PROP. S/AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2279	501	codIncPisPasep	0	00	DESC. FALTAS (HORAS)	automatico	pendente	2026-03-28 03:16:48.023178	\N
2280	558	codIncPisPasep	0	00	DESC. ANTEC. ADIC. INSALUBRIDADE S/13º 1ª PARCELA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2281	438	codIncPisPasep	0	00	HORA EXTRA NOTURNA MES ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2282	60	codIncPisPasep	0	00	ADIC. INSALUBRIDADE 07/2019	automatico	pendente	2026-03-28 03:16:48.023178	\N
2283	669	codIncPisPasep	0	00	ADIC. NOTURNO C/39%	automatico	pendente	2026-03-28 03:16:48.023178	\N
2284	415	codIncPisPasep	0	00	1/3 FERIAS S/AVISO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2285	521	codIncPisPasep	0	00	DESC. AVISO PREVIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2286	1059	codIncPisPasep	0	00	HORAS EXTRAS 50% - JANEIRO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2287	517	codIncPisPasep	0	00	Desc Art 480	automatico	pendente	2026-03-28 03:16:48.023178	\N
2288	693	codIncPisPasep	0	00	DESC. EMPRESTIMO FOLHA PGTO ANTERIOR	automatico	pendente	2026-03-28 03:16:48.023178	\N
2289	729	codIncPisPasep	0	00	DESC. SEGURO DE VIDA	automatico	pendente	2026-03-28 03:16:48.023178	\N
2290	459	codIncPisPasep	0	00	13 SALARIO	automatico	pendente	2026-03-28 03:16:48.023178	\N
2292	243	natRubr	2920-Reembolsos diversos	6129	REEMB. CONTRIB. SINDICAL	staging	pendente	2026-03-28 03:16:48.023178	\N
2293	265	natRubr	9254-Empréstimos consignados – desconto	6129	REEMB. EMPRESTIMO CONSIGNADO	staging	pendente	2026-03-28 03:16:48.023178	\N
2294	342	natRubr	2920-Reembolsos diversos	9243	DIF. CESTA BASICA CCT	staging	pendente	2026-03-28 03:16:48.023178	\N
2295	403	natRubr	1020-Férias – gozadas	1016	COMPLEMENTO FERIAS (DISSIDIO)	staging	pendente	2026-03-28 03:16:48.023178	\N
2296	405	natRubr	1020-Férias – gozadas	1016	MEDIAS FERIAS (Ferias)	staging	pendente	2026-03-28 03:16:48.023178	\N
2297	407	natRubr	1017-Terço constitucional de férias	1023	MEDIAS FERIAS S/ABONO (Ferias)	staging	pendente	2026-03-28 03:16:48.023178	\N
2298	408	natRubr	1021-Férias - abono ou gratificação de férias superior a 20 dias	1023	1/3 MEDIAS FERIAS S/ABONO (Ferias)	staging	pendente	2026-03-28 03:16:48.023178	\N
2299	421	natRubr	1211-Gratificações	1603	AJUDA DE CUSTO	staging	pendente	2026-03-28 03:16:48.023178	\N
2300	503	natRubr	9210-DSR s/faltas e atrasos	9211	DESC. D.S.R. S/FALTAS (DIAS)	staging	pendente	2026-03-28 03:16:48.023178	\N
2301	504	natRubr	9210-DSR s/faltas e atrasos	9210	DESC. D.S.R. S/FALTAS (HORAS)	staging	pendente	2026-03-28 03:16:48.023178	\N
2302	516	natRubr	9299-Outros descontos	9219	DESC. ASSIST. ODONTOLOGICA DEPENDENTE	staging	pendente	2026-03-28 03:16:48.023178	\N
2303	752	natRubr	1020-Férias – gozadas	1016	DIF. 1/3 DAS FERIAS	staging	pendente	2026-03-28 03:16:48.023178	\N
2304	430	natRubr	2920-Reembolsos diversos	1629	DEVOLUCAO DESC. VT	staging	pendente	2026-03-28 03:16:48.023178	\N
2305	501	natRubr	9209-Faltas ou atrados	9209	DESC. FALTAS (HORAS)	staging	pendente	2026-03-28 03:16:48.023178	\N
2306	509	natRubr	9210-DSR s/faltas e atrasos	9299	DESC. DEV. HE/A.N./DSR - MES ANT	staging	pendente	2026-03-28 03:16:48.023178	\N
2307	328	natRubr	0-Não Informado	0	ADIANTAMENTO DE SALARIO	staging	pendente	2026-03-28 03:16:48.023178	\N
2308	512	natRubr	9290-Desconto de pagamento indevido em meses anteriores	9209	DESC. FALTAS HORAS MES ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2309	524	natRubr	9290-Desconto de pagamento indevido em meses anteriores	9299	DESC. DIF. SALARIO	staging	pendente	2026-03-28 03:16:48.023178	\N
2310	522	natRubr	9299-Outros descontos	9219	DESC. CO PARTICIPACAO A.M.	staging	pendente	2026-03-28 03:16:48.023178	\N
2311	537	natRubr	9299-Outros descontos	9219	DESC. ASSIST. MEDICA	staging	pendente	2026-03-28 03:16:48.023178	\N
2312	605	natRubr	9299-Outros descontos	9219	DESC. ASSIST. ODONTO. DEPENDENTE	staging	pendente	2026-03-28 03:16:48.023178	\N
2313	606	natRubr	9299-Outros descontos	9219	DESC. ASSIST. ODONTO. DEPENDENTE	staging	pendente	2026-03-28 03:16:48.023178	\N
2314	619	natRubr	9299-Outros descontos	9219	DESC. ASS. MÉDICA DEP.	staging	pendente	2026-03-28 03:16:48.023178	\N
2315	631	natRubr	9299-Outros descontos	9219	DESC. ASSIST. ODONT. SINTACLUNS	staging	pendente	2026-03-28 03:16:48.023178	\N
2316	638	natRubr	9299-Outros descontos	9219	DESC. ASSIST. ODONT. DEP. SINTACLUNS	staging	pendente	2026-03-28 03:16:48.023178	\N
2317	404	natRubr	1020-Férias – gozadas	1016	DIF. FERIAS	staging	pendente	2026-03-28 03:16:48.023178	\N
2318	428	natRubr	1299-Outros Adicionais	1629	REEMBOLSO DESC. INDEVIDO	staging	pendente	2026-03-28 03:16:48.023178	\N
2319	899	natRubr	9209-Faltas ou atrados	9299	DESC. PAGTO. INDEVIDO	staging	pendente	2026-03-28 03:16:48.023178	\N
2320	645	natRubr	0-Não Informado	0	DESCONTO DE 2 VIA VT	staging	pendente	2026-03-28 03:16:48.023178	\N
2321	621	natRubr	9299-Outros descontos	9219	DESC. BB DETAL	staging	pendente	2026-03-28 03:16:48.023178	\N
2322	994	natRubr	0-Não Informado	0	PARCELAMENTO	staging	pendente	2026-03-28 03:16:48.023178	\N
2323	526	natRubr	9200-Desconto de Adiantamentos	9232	DESC. PLR	staging	pendente	2026-03-28 03:16:48.023178	\N
2324	320	natRubr	1003-Horas extraordinárias	1011	SOBRE AVISO	staging	pendente	2026-03-28 03:16:48.023178	\N
2325	577	natRubr	9243-Cesta básica ou refeição, vinculada ao PAT - Desconto	9299	DESC. VA NAO UTILIZADO MES ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2326	664	natRubr	9243-Cesta básica ou refeição, vinculada ao PAT - Desconto	9241	DESC. VALE ALIMENTACAO MES ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2327	685	natRubr	0-Não Informado	0	DESC. ADIANTAMENTO DE SALARIO	staging	pendente	2026-03-28 03:16:48.023178	\N
2328	757	natRubr	9232-Contribuição Sindical – Assistencial	9232	DESC. CONTRIB. DE NATUREZA PREVIDENCIARIA	staging	pendente	2026-03-28 03:16:48.023178	\N
2329	767	natRubr	9209-Faltas ou atrados	9299	DESC. PAGTO. SALARIO INDEV.	staging	pendente	2026-03-28 03:16:48.023178	\N
2330	776	natRubr	9243-Cesta básica ou refeição, vinculada ao PAT - Desconto	9241	DESC. VALE ALIMENTACAO	staging	pendente	2026-03-28 03:16:48.023178	\N
2331	146	natRubr	1002-Descanso semanal remunerado - DSR	1002	DEV. D.S.R. S/FALTAS (DIAS)	staging	pendente	2026-03-28 03:16:48.023178	\N
2332	869	natRubr	1299-Outros Adicionais	1629	REEMBOLSO DESC. INDEVIDO	staging	pendente	2026-03-28 03:16:48.023178	\N
2333	35	natRubr	1002-Descanso semanal remunerado - DSR	1002	DIF. D.S.R.	staging	pendente	2026-03-28 03:16:48.023178	\N
2334	136	natRubr	1002-Descanso semanal remunerado - DSR	1002	D.S.R. S/ADICIONAL	staging	pendente	2026-03-28 03:16:48.023178	\N
2335	159	natRubr	1002-Descanso semanal remunerado - DSR	1002	D.S.R. S/ADICIONAL	staging	pendente	2026-03-28 03:16:48.023178	\N
2336	160	natRubr	1002-Descanso semanal remunerado - DSR	1002	D.S.R. S/HORA EXTRA	staging	pendente	2026-03-28 03:16:48.023178	\N
2337	163	natRubr	1002-Descanso semanal remunerado - DSR	1012	D.S.R. S/FERIADO - HS	staging	pendente	2026-03-28 03:16:48.023178	\N
2338	170	natRubr	1002-Descanso semanal remunerado - DSR	1012	D.S.R. S/COMISSAO	staging	pendente	2026-03-28 03:16:48.023178	\N
2339	234	natRubr	1299-Outros Adicionais	6129	REEMB. EXAMES MÉDICOS	staging	pendente	2026-03-28 03:16:48.023178	\N
2340	560	natRubr	9299-Outros descontos	9221	DESC. FERIAS PAGAS	staging	pendente	2026-03-28 03:16:48.023178	\N
2341	579	natRubr	9209-Faltas ou atrados	9207	DESC. FALTAS (DIAS) MES ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2342	586	natRubr	9230-Contribuição Sindical – Compulsória	9230	DESC. CONTRIB. SINDICAL	staging	pendente	2026-03-28 03:16:48.023178	\N
2343	597	natRubr	1002-Descanso semanal remunerado - DSR	9210	DESC. D.S.R. S/FALTAS (DIAS) MES ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2344	686	natRubr	0-Não Informado	6901	DESC. AVISO PREVIO NAO TRABALHADO	staging	pendente	2026-03-28 03:16:48.023178	\N
2345	692	natRubr	0-Não Informado	0	DESC. 2 VIA CARTAO	staging	pendente	2026-03-28 03:16:48.023178	\N
2346	693	natRubr	0-Não Informado	0	DESC. EMPRESTIMO FOLHA PGTO ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2347	710	natRubr	9243-Cesta básica ou refeição, vinculada ao PAT - Desconto	9241	DESC. ALIMENTACAO MES ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2348	724	natRubr	9299-Outros descontos	9270	DESC. MULTA DE TRANSITO	staging	pendente	2026-03-28 03:16:48.023178	\N
2349	778	natRubr	9243-Cesta básica ou refeição, vinculada ao PAT - Desconto	9299	DESC. VALE ALIMENTACAO NAO UTILIZADO	staging	pendente	2026-03-28 03:16:48.023178	\N
2350	837	natRubr	9209-Faltas ou atrados	9207	DESC. FALTAS (DIAS)	staging	pendente	2026-03-28 03:16:48.023178	\N
2351	861	natRubr	9210-DSR s/faltas e atrasos	9210	DESC. D.S.R. S/FALTAS (HORAS) MÊS ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2352	897	natRubr	0-Não Informado	0	DESC. ANTECIPACAO VA E VR	staging	pendente	2026-03-28 03:16:48.023178	\N
2353	151	natRubr	9989-Outros valores informativos	1810	REEMB. VALE TRANSPORTE MÊS ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2354	18	natRubr	1211-Gratificações	1000	ADICIONAL DE SALARIO	staging	pendente	2026-03-28 03:16:48.023178	\N
2356	135	natRubr	9299-Outros descontos	1002	D.S.R. S/HORA EXTRA	staging	pendente	2026-03-28 03:16:48.023178	\N
2357	774	natRubr	9299-Outros descontos	9219	DESC. ASSIST. MEDICA	staging	pendente	2026-03-28 03:16:48.023178	\N
2358	775	natRubr	9299-Outros descontos	9219	DESC. ASSIST. ODONTOLOGICA	staging	pendente	2026-03-28 03:16:48.023178	\N
2359	811	natRubr	1211-Gratificações	1201	ACUMULO DE FUNCAO	staging	pendente	2026-03-28 03:16:48.023178	\N
2360	822	natRubr	1002-Descanso semanal remunerado - DSR	1012	D.S.R. S/FERIADO - HS (INTERMITENTE)	staging	pendente	2026-03-28 03:16:48.023178	\N
2361	892	natRubr	1299-Outros Adicionais	6129	REEMB. EXAME RETORNO AO TRABALHO	staging	pendente	2026-03-28 03:16:48.023178	\N
2362	895	natRubr	9299-Outros descontos	9219	DESC. ASSIST. ODONTO. DEPENDENTE MES ANT	staging	pendente	2026-03-28 03:16:48.023178	\N
2363	1017	natRubr	1299-Outros Adicionais	6129	REEMB. EXAME TROCA DE FUNCAO	staging	pendente	2026-03-28 03:16:48.023178	\N
2364	149	natRubr	1002-Descanso semanal remunerado - DSR	1002	REEMB D.S.R MES ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2365	161	natRubr	1002-Descanso semanal remunerado - DSR	1002	D.S.R. MES ANTERIOR	staging	pendente	2026-03-28 03:16:48.023178	\N
2366	294	natRubr	2920-Reembolsos diversos	1621	DESP DE VIAGENS	staging	pendente	2026-03-28 03:16:48.023178	\N
2367	500	natRubr	9209-Faltas ou atrados	9207	DESC. FALTAS (DIAS)	staging	pendente	2026-03-28 03:16:48.023178	\N
2368	156	natRubr	6006-Férias proporcionais	1016	DIF. FERIAS	staging	pendente	2026-03-28 03:16:48.023178	\N
2369	520	natRubr	9299-Outros descontos	9270	DESC. AVARIA	staging	pendente	2026-03-28 03:16:48.023178	\N
2370	716	natRubr	9299-Outros descontos	9270	DESC. CELULAR NAO DEVOLVIDO	staging	pendente	2026-03-28 03:16:48.023178	\N
2371	730	natRubr	9299-Outros descontos	9270	DESC. SMARTPHONE NAO DEVOLVIDO	staging	pendente	2026-03-28 03:16:48.023178	\N
2372	228	natRubr	2920-Reembolsos diversos	6129	REEMB. DESC. ASSIST. MEDICA	staging	pendente	2026-03-28 03:16:48.023178	\N
2373	249	natRubr	2920-Reembolsos diversos	6129	REEMB. DESC. ASS. ODONTOLOGICA	staging	pendente	2026-03-28 03:16:48.023178	\N
2374	339	natRubr	1002-Descanso semanal remunerado - DSR	1000	DEVOLUCAO FALTAS / DSR	staging	pendente	2026-03-28 03:16:48.023178	\N
2375	611	natRubr	9243-Cesta básica ou refeição, vinculada ao PAT - Desconto	9241	DESC. VALE ALIMENTACAO - CCT	staging	pendente	2026-03-28 03:16:48.023178	\N
2376	746	natRubr	1099-Outras verbas salariais	1000	DIFERENCA CCT	staging	pendente	2026-03-28 03:16:48.023178	\N
2377	748	natRubr	9299-Outros descontos	9299	DESC. JUDICIAL - 2	staging	pendente	2026-03-28 03:16:48.023178	\N
2378	755	natRubr	1810-Transporte	1810	REEMB. VALE TRANSPORTE - HORA EXTRA	staging	pendente	2026-03-28 03:16:48.023178	\N
2379	1112	natRubr	9230-Contribuição Sindical – Compulsória	9230	CUSTEIO SOCIAL - SINTEAC MG	staging	pendente	2026-03-28 03:16:48.023178	\N
2380	233	natRubr	1629-Ressarcimento de outras despesas	1801	REEMB. REFEICAO	staging	pendente	2026-03-28 03:16:48.023178	\N
2381	1026	natRubr	1299-Outros Adicionais	1801	PAGTO. VT E VA - REF FERIADOS	staging	pendente	2026-03-28 03:16:48.023178	\N
171	13	tpRubr	Vencimento	1	REEMB. VALE TRANSPORTE	automatico	aplicado	2026-03-28 03:16:48.023178	2026-03-28 03:42:29.33168
1353	13	codIncPisPasep	0	00	REEMB. VALE TRANSPORTE	automatico	aplicado	2026-03-28 03:16:48.023178	2026-03-28 03:42:29.33168
2291	13	natRubr	1629-Ressarcimento de outras despesas	1810	REEMB. VALE TRANSPORTE	staging	aplicado	2026-03-28 03:16:48.023178	2026-03-28 03:42:29.33168
238	19	tpRubr	Vencimento	1	REEMB. EXAME ADMISSIONAL	automatico	aplicado	2026-03-28 03:16:48.023178	2026-03-28 03:45:21.373913
1855	19	codIncPisPasep	0	00	REEMB. EXAME ADMISSIONAL	automatico	aplicado	2026-03-28 03:16:48.023178	2026-03-28 03:45:21.373913
2355	19	natRubr	1299-Outros Adicionais	6129	REEMB. EXAME ADMISSIONAL	staging	aplicado	2026-03-28 03:16:48.023178	2026-03-28 03:45:21.373913
\.


--
-- Name: esocial_depara_id_seq; Type: SEQUENCE SET; Schema: public; Owner: easy_social_user
--

SELECT pg_catalog.setval('public.esocial_depara_id_seq', 2381, true);


--
-- PostgreSQL database dump complete
--

\unrestrict sT8hakOYuTfKNj6Yfxsb7h9Q2wpuscE5cxwxNrKfsXvguWT4TWOrVpo0EbIhZst

