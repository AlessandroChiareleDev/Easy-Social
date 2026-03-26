# Easy Social System

## MENSAGEM FINAL E COMPLETA PARA VS CODE/CLAUDE

### Instruções Detalhadas para o Desenvolvimento do Ponto 1

**25 de março de 2026**

---

## 1. CONFIRMAÇÃO E CONTEXTO

Olá, equipe de desenvolvimento do Easy Social System. Confirmamos que o ambiente está totalmente pronto para a próxima fase do projeto. O relatório de status detalhado que você forneceu indica que todos os componentes essenciais estão operacionais e que as instalações do Prompt 0 foram concluídas com sucesso.

Até o momento, alcançamos a implementação de um backend robusto em Node.js (porta 3333), um frontend funcional em Vue 3 (porta 5173), e um ambiente Python FastAPI (porta 8000) pronto para uso. O banco de dados PostgreSQL está configurado com as 7 tabelas iniciais, sendo que 4 delas (analise_natureza, dinamica, tabela_eventos_gl, tabela_eb) já contêm dados reais processados do arquivo "Relatório DIRF 2025.xlsx". As tabelas base_ficha_financeira e planilha_1 foram estrategicamente excluídas do fluxo atual, mas permanecem no schema para uso futuro.

Agora, estamos prontos para transicionar para o Ponto 1, que envolve a implementação de uma ferramenta crucial para o processamento do arquivo DIRF.xlsx e a validação de rubricas no eSocial. Este documento fornece todas as informações necessárias, incluindo um fluxograma detalhado e referências visuais, para guiar o desenvolvimento.

---

## 2. TAREFA COMPLEXA - PONTO 1: Ferramenta de Upload e Divisão do DIRF.xlsx

O objetivo geral do Ponto 1 é desenvolver uma ferramenta completa para gerenciar o arquivo "Relatório DIRF.xlsx", que possui um tamanho considerável de 124.4MB. Esta ferramenta deve ser capaz de receber o arquivo, processá-lo e dividir seu conteúdo em tabelas normalizadas no banco de dados PostgreSQL.

O arquivo de entrada, "Relatório DIRF.xlsx", contém múltiplas abas que precisam ser tratadas como tabelas independentes. A saída esperada é a divisão e normalização dos dados nas seguintes 6 tabelas alvo no banco de dados easy_social_db:

1. ANALISE NATUREZA
2. Dinamica
3. Base Ficha Financeira 2025
4. Planilha 1
5. Tabela Eventos Gl
6. Tabela EB

É fundamental que o processo inclua validações robustas para garantir a integridade dos dados, tratamento de erros eficaz para lidar com arquivos corrompidos ou formatos inesperados, e medidas de segurança, como a prevenção de path traversal e SQL injection, que já foram iniciadas no Prompt 0.

---

## 3. SVG DO FLUXOGRAMA: Processo de Validação e Correção de Rubricas no eSocial

O fluxograma (cujo SVG será enviado separadamente) detalha o processo de validação e correção de rubricas no eSocial, com base nas informações da Tabela EB. Ele representa visualmente a sequência de ações, decisões e loops necessários para garantir a conformidade dos dados de tributação.

A estrutura visual do fluxograma utiliza:

- **Óvalos**: Para indicar o início e o fim do processo.
- **Retângulos**: Para representar as etapas de processamento ou ações.
- **Losangos**: Para indicar pontos de decisão.

O fluxo segue uma lógica de 14 etapas, começando pela leitura da Tabela EB e terminando com a repetição do processo para a próxima rubrica com divergência. Os pontos críticos de decisão são destacados, especialmente aqueles relacionados à comparação de valores e à validação de buscas no eSocial. O fluxograma também ilustra os loops e retornos necessários para refinar buscas ou re-aplicar correções.

**A regra de ouro que governa este processo é: D/E/F deve ser igual a H/I/J.** Onde H/I/J é sempre a fonte de verdade (o estado correto da rubrica), e D/E/F representa o estado atual no eSocial, que pode conter erros e, portanto, precisa ser corrigido.

---

## 4. RELACIONAMENTO SVG COM OS PRINTS DE REFERÊNCIA

Para facilitar a compreensão e a implementação, o fluxograma faz referência a 4 prints de tela do sistema eSocial. Estes prints fornecem o contexto visual exato para as etapas críticas do processo:

### 4.1. Print 1: Tela de Busca no eSocial

- **Localização no SVG**: Etapa 5 "BUSCAR NO eSocial (Print 1)".
- **O que mostra**: A interface do eSocial onde o código da rubrica é inserido para iniciar a busca.
- **Comportamento Crítico**: A busca no eSocial tem um comportamento semelhante a Regex, ou seja, não é uma busca exata. Ao buscar, por exemplo, o código "11", o sistema pode retornar múltiplos resultados que contêm "11" parcialmente (ex: 11, 110, 111).

### 4.2. Print 2: Resultado da Busca (Validação Regex)

- **Localização no SVG**: Etapa 6 "VALIDAR RETORNO REGEX (Print 2 - Múltiplos resultados)".
- **O que mostra**: A tela de resultados da busca, evidenciando os múltiplos itens retornados devido ao comportamento Regex.
- **Crítico**: É imperativo realizar uma validação dupla obrigatória. Não basta apenas o código ser igual; a descrição da rubrica também deve corresponder exatamente. Se a busca por "11" retornar "11 - Salário" e "110 - Horas Extras", o sistema deve ser capaz de identificar e selecionar apenas o item que corresponde tanto ao código quanto à descrição exata da rubrica que está sendo corrigida.

### 4.3. Print 3: Tela de Edição

- **Localização no SVG**: Etapa 7 "ACESSAR EDIÇÃO (Print 3)".
- **O que mostra**: O formulário de edição de uma rubrica específica no eSocial, onde os campos de incidência tributária (INSS, IRRF, FGTS) são visíveis.
- **Estado Atual**: Estes campos representam os valores D/E/F, que são o estado atual da rubrica e podem conter erros. Por exemplo, pode-se observar INSS=0, IRRF=(vazio), FGTS=0.

### 4.4. Print 4: Valores Corrigidos

- **Localização no SVG**: Etapa 9 "APLICAR CORREÇÃO (Print 4) - Exemplo: 0 / 74 / 0".
- **O que mostra**: A mesma tela de edição do Print 3, mas com os valores de incidência tributária já atualizados para o estado correto (H/I/J).
- **Correção Aplicada**: O exemplo obrigatório no fluxo é a correção de INSS=0, IRRF=(vazio) para INSS=0, IRRF=74, FGTS=0. Após a aplicação da correção, uma validação final deve confirmar que o estado no eSocial agora corresponde a H/I/J.

---

## 5. FLUXO COMPLETO (14 ETAPAS)

A seguir, as 14 etapas do fluxograma, que devem ser implementadas sequencialmente:

1. **INÍCIO - Ler Tabela EB**: Inicia o processo lendo os dados da Tabela EB.
2. **COMPARAR D/E/F vs H/I/J**: Compara o estado atual (D/E/F) com o estado correto (H/I/J) para cada rubrica.
3. **D/E/F = H/I/J? (Decisão)**: Verifica se há divergência. Se forem iguais, o fluxo para para essa rubrica. Se forem diferentes, prossegue para correção.
4. **COLETAR DADOS (Código + Descrição)**: Extrai o código e a descrição da rubrica da Tabela EB para uso na busca.
5. **BUSCAR NO eSocial (Print 1)**: Insere o código da rubrica no campo de busca do eSocial.
6. **VALIDAR RETORNO REGEX (Print 2)**: Analisa os resultados da busca, considerando o comportamento Regex que pode retornar múltiplos itens.
7. **Código + Descrição exatos? (Decisão)**: Valida se o resultado da busca corresponde exatamente ao código E à descrição da rubrica. Se não, retorna para a etapa de busca.
8. **ACESSAR EDIÇÃO (Print 3)**: Abre a tela de edição da rubrica correta no eSocial.
9. **VALIDAR ESTADO ATUAL (INSS/IRRF/FGTS)**: Lê os valores atuais de incidência tributária (D/E/F) na tela de edição.
10. **APLICAR CORREÇÃO (Print 4)**: Substitui os valores D/E/F pelos valores H/I/J na tela de edição (ex: 0 / 74 / 0).
11. **SALVAR ALTERAÇÃO**: Confirma a atualização dos dados no sistema eSocial.
12. **Estado final = H/I/J? (Decisão)**: Realiza uma validação final para confirmar que os valores no eSocial agora correspondem a H/I/J. Se não, retorna para a etapa de aplicação da correção.
13. **LOOP - Próxima rubrica**: Repete o processo para a próxima rubrica com divergência identificada na Tabela EB.
14. **FIM**: O processo é encerrado quando todas as rubricas com divergência forem tratadas.

---

## 6. INSTRUÇÕES PARA DESENVOLVIMENTO

A implementação deve seguir o fluxograma e as descrições fornecidas com a máxima fidelidade. Os prints de referência são cruciais para entender o contexto visual e o comportamento do sistema eSocial. As validações duplas (código + descrição) e o tratamento do comportamento Regex da busca são pontos de atenção críticos.

É essencial que o sistema seja robusto no tratamento de erros em todas as etapas, desde o upload do arquivo até a interação com o eSocial. A segurança deve ser mantida como prioridade, garantindo que todas as interações com o banco de dados e o sistema externo sejam seguras.

Após a implementação, serão necessários testes exaustivos para garantir que o fluxo funciona conforme o esperado, especialmente com o arquivo "Relatório DIRF 2025.xlsx" de 124.4MB e a correção das rubricas no eSocial.

---

## 7. PRÓXIMOS PASSOS

Aguardamos a confirmação do seu entendimento sobre esta tarefa complexa. Uma vez confirmada, o desenvolvimento do Ponto 1 pode ser iniciado. Por favor, mantenha-nos informados sobre o progresso e quaisquer desafios que possam surgir.
