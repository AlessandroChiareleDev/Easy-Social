<template>
  <div class="eventos-tab">
    <h2 class="titulo">Diagrama de Eventos eSocial</h2>
    <p class="subtitulo">Clique em qualquer evento para ver a explicação completa</p>
    <div class="legenda">
      <span class="leg"><span class="dot green"></span> Já enviamos</span>
      <span class="leg"><span class="dot red"></span> Obrigatório — ainda não enviamos</span>
      <span class="leg"><span class="dot yellow"></span> Opcional — não se aplica ainda</span>
      <span class="leg"><span class="dot gray"></span> Retorno automático do governo</span>
    </div>

    <div class="diagrama">
      <div class="inicio-fim inicio">INÍCIO</div>
      <div class="seta-vertical"></div>

      <!-- S-1000 sozinho -->
      <div class="linha">
        <div v-for="e in linha1" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <!-- Tabelas em paralelo -->
      <div class="fase-tag">Tabelas — enviar em paralelo</div>
      <div class="linha">
        <div v-for="e in linha2" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <!-- Não-Periódicos: Admissões -->
      <div class="fase-tag">Não-Periódicos — quando acontecem</div>
      <div class="linha">
        <div v-for="e in linha3" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <!-- Alterações / Afastamentos -->
      <div class="linha">
        <div v-for="e in linha4" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <!-- Desligamento / TSV -->
      <div class="linha">
        <div v-for="e in linha5" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <!-- Processos / Exclusão -->
      <div class="linha">
        <div v-for="e in linha6" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <!-- Periódicos — Remuneração -->
      <div class="fase-tag">Periódicos — Folha Mensal</div>
      <div class="linha">
        <div v-for="e in linha7" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <!-- Pagamento -->
      <div class="linha">
        <div v-for="e in linha8" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <!-- Fechamento -->
      <div class="linha">
        <div v-for="e in linha9" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <!-- Retorno do Governo -->
      <div class="fase-tag retorno-tag">Retorno Automático do Governo</div>
      <div class="linha">
        <div v-for="e in linha10" :key="e.codigo" :class="['nw', { nexp: codigoAberto === e.codigo }]">
          <div :class="['nd', cor(e)]" @click="toggle(e.codigo)">
            <div class="nd-top"><span class="nd-cod">{{ e.codigo }}</span><span v-if="e.qtdEnviada > 0" class="nd-bdg">{{ e.qtdEnviada }}</span><span class="nd-arr">{{ codigoAberto === e.codigo ? '▾' : '▸' }}</span></div>
            <div class="nd-nm">{{ e.nome }}</div>
          </div>
          <div v-if="codigoAberto === e.codigo" class="nd-det">
            <div class="r"><span class="lb">Status</span><span :class="'vl ' + stCls(e)">{{ stTxt(e) }}</span></div>
            <div v-if="e.qtdEnviada > 0" class="r"><span class="lb">Enviados</span><span class="vl">{{ e.qtdEnviada }} registro(s)</span></div>
            <div class="r"><span class="lb">Obrigatório</span><span class="vl">{{ e.obrigatorio ? 'Sim' : 'Depende do caso' }}</span></div>
            <div class="desc">{{ e.descricao }}</div>
            <div v-if="e.campos" class="tags"><span class="lb">Campos:</span><span v-for="c in e.campos" :key="c" class="tg">{{ c }}</span></div>
            <div v-if="e.dependencias" class="tags"><span class="lb">Depende de:</span><span v-for="d in e.dependencias" :key="d" class="dp">{{ d }}</span></div>
          </div>
        </div>
      </div>
      <div class="seta-vertical"></div>

      <div class="inicio-fim fim">FIM — DCTFWeb</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Evento {
  codigo: string
  nome: string
  descricao: string
  obrigatorio: boolean
  retorno: boolean
  campos?: string[]
  dependencias?: string[]
  qtdEnviada: number
}

const contagensPorTipo = ref<Record<string, number>>({})

onMounted(async () => {
  try {
    const res = await fetch('/api/envios/resumo')
    const json = await res.json()
    if (json.success && json.resumo?.por_tipo) {
      for (const item of json.resumo.por_tipo) {
        contagensPorTipo.value[item.tipo_evento] = Number(item.total)
      }
    }
  } catch { /* silencioso */ }
})

function qtd(codigo: string): number {
  let total = contagensPorTipo.value[codigo] || 0
  for (const [key, val] of Object.entries(contagensPorTipo.value)) {
    if (key !== codigo && key.includes(codigo.replace('S-', 'S'))) total += val
  }
  return total
}

function cor(e: Evento): string {
  if (e.retorno) return 'c-gray'
  if (e.qtdEnviada > 0) return 'c-green'
  if (e.obrigatorio) return 'c-red'
  return 'c-yellow'
}

function stCls(e: Evento): string {
  if (e.qtdEnviada > 0) return 'v-ok'
  if (e.retorno) return 'v-ret'
  if (e.obrigatorio) return 'v-pend'
  return 'v-opt'
}

function stTxt(e: Evento): string {
  if (e.qtdEnviada > 0) return '\u2705 Já enviamos'
  if (e.retorno) return '\uD83D\uDCE5 Retorno do Governo'
  if (e.obrigatorio) return '\u274C Ainda não enviamos'
  return '\u23F8 Opcional / Não se aplica'
}

const codigoAberto = ref<string | null>(null)
function toggle(codigo: string) {
  codigoAberto.value = codigoAberto.value === codigo ? null : codigo
}

const ev = computed<Record<string, Evento>>(() => ({
  'S-1000': { codigo: 'S-1000', nome: 'Empregador / Contribuinte', obrigatorio: true, retorno: false, descricao: 'Cadastro inicial do empregador no eSocial. É o PRIMEIRO evento — sem ele, NADA funciona. Contém CNPJ, razão social, natureza jurídica, classificação tributária.', campos: ['CNPJ/CPF', 'Razão Social', 'Natureza Jurídica', 'Classificação Tributária', 'Contato responsável'], qtdEnviada: qtd('S-1000') },
  'S-1005': { codigo: 'S-1005', nome: 'Tabela de Estabelecimentos', obrigatorio: true, retorno: false, descricao: 'Cadastra cada estabelecimento (filial, obra). Informa CNAE, RAT/FAP. Pode ser enviado em paralelo com S-1010 e S-1020 após o S-1000.', campos: ['CNPJ filial', 'CNAE', 'Alíquota RAT', 'FAP'], dependencias: ['S-1000'], qtdEnviada: qtd('S-1005') },
  'S-1010': { codigo: 'S-1010', nome: 'Tabela de Rubricas', obrigatorio: true, retorno: false, descricao: 'Cadastra TODAS as rubricas da folha (proventos, descontos). Cada rubrica tem natureza (natRubr), incidências CP/IRRF/FGTS. É o coração da folha — sem rubricas corretas, o cálculo do governo fica errado.', campos: ['Código Rubrica', 'Descrição', 'Natureza (natRubr)', 'Tipo (provento/desconto)', 'Incidência CP', 'Incidência IRRF', 'Incidência FGTS'], dependencias: ['S-1000'], qtdEnviada: qtd('S-1010') },
  'S-1020': { codigo: 'S-1020', nome: 'Tabela de Lotações', obrigatorio: true, retorno: false, descricao: 'Define lotações tributárias (departamentos para tributação). Tem FPAS, código de terceiros. Referenciada na remuneração.', campos: ['Código Lotação', 'Tipo', 'FPAS', 'Código Terceiros'], dependencias: ['S-1000'], qtdEnviada: qtd('S-1020') },
  'S-1070': { codigo: 'S-1070', nome: 'Processos Adm/Judiciais', obrigatorio: false, retorno: false, descricao: 'Cadastra processos que alteram a tributação (liminares, decisões judiciais). Só envia se existir processo que suspenda contribuição.', campos: ['Nº Processo', 'Tipo', 'Indicativo de Suspensão'], dependencias: ['S-1000'], qtdEnviada: qtd('S-1070') },
  'S-2190': { codigo: 'S-2190', nome: 'Registro Preliminar', obrigatorio: false, retorno: false, descricao: 'Pré-admissão opcional. Gera matrícula antes da data de admissão efetiva. A maioria das empresas pula direto pro S-2200.', campos: ['CPF', 'Data Nascimento', 'Data Admissão'], dependencias: ['S-1000'], qtdEnviada: qtd('S-2190') },
  'S-2200': { codigo: 'S-2200', nome: 'Admissão do Trabalhador', obrigatorio: true, retorno: false, descricao: 'Cadastro COMPLETO do trabalhador: CPF, endereço, cargo, salário, jornada, categoria. Efetiva a admissão no eSocial. Sem ele não dá pra enviar remuneração.', campos: ['CPF', 'NIS/PIS', 'Nome', 'Cargo', 'Salário', 'Jornada', 'Categoria', 'Matrícula'], dependencias: ['S-1000', 'S-1005', 'S-1020'], qtdEnviada: qtd('S-2200') },
  'S-2300': { codigo: 'S-2300', nome: 'TSV — Início', obrigatorio: false, retorno: false, descricao: 'Cadastra Trabalhador Sem Vínculo: diretores, estagiários, autônomos recorrentes. Equivalente ao S-2200 mas para TSV.', campos: ['CPF', 'Categoria', 'Data Início', 'Remuneração'], dependencias: ['S-1000'], qtdEnviada: qtd('S-2300') },
  'S-2205': { codigo: 'S-2205', nome: 'Alteração Cadastral', obrigatorio: false, retorno: false, descricao: 'Altera dados cadastrais do trabalhador (endereço, nome social, estado civil). NÃO altera contrato — pra isso é S-2206.', campos: ['CPF', 'Matrícula', 'Dados Alterados'], dependencias: ['S-2200'], qtdEnviada: qtd('S-2205') },
  'S-2206': { codigo: 'S-2206', nome: 'Alteração Contratual', obrigatorio: false, retorno: false, descricao: 'Altera dados do contrato: salário, cargo, jornada, lotação. Para promoções, transferências, reajustes.', campos: ['Matrícula', 'Data Alteração', 'Cargo', 'Salário', 'Jornada'], dependencias: ['S-2200'], qtdEnviada: qtd('S-2206') },
  'S-2210': { codigo: 'S-2210', nome: 'CAT — Acidente de Trabalho', obrigatorio: false, retorno: false, descricao: 'Comunica acidente de trabalho. Substitui a CAT em papel. Obrigatório quando acontece acidente, mesmo sem afastamento.', campos: ['Data Acidente', 'Tipo', 'Local', 'CID'], dependencias: ['S-2200'], qtdEnviada: qtd('S-2210') },
  'S-2220': { codigo: 'S-2220', nome: 'Saúde — ASO', obrigatorio: false, retorno: false, descricao: 'Registra ASOs: admissional, periódico, retorno, demissional. Alimenta o PPP eletrônico.', campos: ['Tipo ASO', 'Data', 'Médico', 'Exames'], dependencias: ['S-2200'], qtdEnviada: qtd('S-2220') },
  'S-2230': { codigo: 'S-2230', nome: 'Afastamento Temporário', obrigatorio: false, retorno: false, descricao: 'Férias, licença-médica, maternidade, aux-doença. Fundamental para cálculo correto de remuneração.', campos: ['Data Início', 'Motivo', 'Data Término', 'CID'], dependencias: ['S-2200'], qtdEnviada: qtd('S-2230') },
  'S-2299': { codigo: 'S-2299', nome: 'Desligamento', obrigatorio: true, retorno: false, descricao: 'Rescisão do contrato. Motivo, data, valores rescisórios, multa FGTS, aviso prévio. Encerra o vínculo no eSocial.', campos: ['Data Desligamento', 'Motivo (tab 19)', 'Aviso Prévio', 'Valores por rubrica'], dependencias: ['S-2200'], qtdEnviada: qtd('S-2299') },
  'S-2399': { codigo: 'S-2399', nome: 'TSV — Término', obrigatorio: false, retorno: false, descricao: 'Encerra contrato de Trabalhador Sem Vínculo.', campos: ['Matrícula', 'Data Término', 'Motivo'], dependencias: ['S-2300'], qtdEnviada: qtd('S-2399') },
  'S-2500': { codigo: 'S-2500', nome: 'Processo Trabalhista', obrigatorio: false, retorno: false, descricao: 'Informa processo trabalhista com decisão/acordo que gere pagamento de verbas ou recolhimento de FGTS/contribuições.', campos: ['Nº Processo', 'Vara', 'Data Sentença', 'Valores por rubrica'], dependencias: ['S-1000'], qtdEnviada: qtd('S-2500') },
  'S-3000': { codigo: 'S-3000', nome: 'Exclusão de Eventos', obrigatorio: false, retorno: false, descricao: 'Exclui qualquer evento enviado anteriormente. Envia a exclusão e depois reenvia o evento correto.', campos: ['Tipo Evento', 'Nº Recibo', 'Período Apuração'], dependencias: ['S-1000'], qtdEnviada: qtd('S-3000') },
  'S-1200': { codigo: 'S-1200', nome: 'Remuneração (CLT)', obrigatorio: true, retorno: false, descricao: 'Detalha remuneração mensal de cada trabalhador, rubrica por rubrica. O governo usa isso pra calcular INSS e FGTS por pessoa.', campos: ['Matrícula', 'Período', 'Rubrica + Valor (cada item)', 'Lotação'], dependencias: ['S-1010', 'S-1020', 'S-2200'], qtdEnviada: qtd('S-1200') },
  'S-1202': { codigo: 'S-1202', nome: 'Remuneração (RPPS)', obrigatorio: false, retorno: false, descricao: 'Equivalente ao S-1200 para servidores públicos com RPPS.', campos: ['Matrícula', 'Período', 'Rubrica + Valor'], dependencias: ['S-1010', 'S-2200'], qtdEnviada: qtd('S-1202') },
  'S-1210': { codigo: 'S-1210', nome: 'Pagamentos / IRRF', obrigatorio: true, retorno: false, descricao: 'Informa pagamentos efetivamente realizados. Usado pra calcular IRRF. Um trabalhador pode ter vários pagamentos/mês (adiantamento, salário, férias, PLR).', campos: ['CPF', 'Data Pagamento', 'Tipo', 'Valor Líquido', 'Retenção IR'], dependencias: ['S-1200'], qtdEnviada: qtd('S-1210') },
  'S-1260': { codigo: 'S-1260', nome: 'Comercialização Rural PF', obrigatorio: false, retorno: false, descricao: 'Comercialização de produção rural por pessoa física. Só se aplica a empregador rural PF.', campos: ['Tipo Comercialização', 'Valor', 'CNPJ Adquirente'], dependencias: ['S-1000'], qtdEnviada: qtd('S-1260') },
  'S-1270': { codigo: 'S-1270', nome: 'Trabalhadores Avulsos', obrigatorio: false, retorno: false, descricao: 'Contratação de avulsos via OGMO ou sindicato (portuários e não-portuários).', campos: ['CNPJ OGMO/Sindicato', 'Lotação', 'Remunerações'], dependencias: ['S-1020'], qtdEnviada: qtd('S-1270') },
  'S-1280': { codigo: 'S-1280', nome: 'Info. Complementares', obrigatorio: false, retorno: false, descricao: 'Complementa periódicos: desoneração CPRB, substituição de contribuição patronal.', campos: ['Indicativo Substituição', 'Percentual Redução'], dependencias: ['S-1000'], qtdEnviada: qtd('S-1280') },
  'S-1298': { codigo: 'S-1298', nome: 'Reabertura Periódicos', obrigatorio: false, retorno: false, descricao: 'Reabre o período já fechado pelo S-1299 para retificação. Depois precisa fechar novamente.', campos: ['Período Apuração'], dependencias: ['S-1299'], qtdEnviada: qtd('S-1298') },
  'S-1299': { codigo: 'S-1299', nome: 'FECHAMENTO da Folha', obrigatorio: true, retorno: false, descricao: 'FECHA a folha do período. Após isso o governo calcula tudo e gera os retornos (S-5001, S-5002, S-5011, S-5012). Sem fechamento, não gera DCTFWeb.', campos: ['Período Apuração', 'Indicativo Apuração'], dependencias: ['S-1200', 'S-1210'], qtdEnviada: qtd('S-1299') },
  'S-5001': { codigo: 'S-5001', nome: 'Bases CP por Trabalhador', obrigatorio: false, retorno: true, descricao: 'Gerado automaticamente após cada S-1200. Mostra as bases de cálculo (INSS + FGTS) que o governo calculou por trabalhador.', campos: ['CPF', 'Base CP', 'Base FGTS', 'Valores calculados'], dependencias: ['S-1200'], qtdEnviada: qtd('S-5001') },
  'S-5002': { codigo: 'S-5002', nome: 'IRRF por Trabalhador', obrigatorio: false, retorno: true, descricao: 'Gerado após cada S-1210. Mostra o cálculo de IRRF por trabalhador. Fundamental pra conferir se os códigos de incidência IRRF das rubricas estão certos.', campos: ['CPF', 'Base IRRF', 'Valor IRRF Calculado', 'Faixa'], dependencias: ['S-1210'], qtdEnviada: qtd('S-5002') },
  'S-5003': { codigo: 'S-5003', nome: 'Bases por Estabelecimento', obrigatorio: false, retorno: true, descricao: 'Totaliza bases de contribuição POR ESTABELECIMENTO (não por trabalhador). Confere FPAS e terceiros.', campos: ['CNPJ', 'FPAS', 'Base CP Patronal'], dependencias: ['S-1299'], qtdEnviada: qtd('S-5003') },
  'S-5011': { codigo: 'S-5011', nome: 'Consolidação CP — Empregador', obrigatorio: false, retorno: true, descricao: 'Gerado após S-1299. Consolida TODAS as contribuições previdenciárias do empregador. Alimenta a DCTFWeb com o INSS a pagar.', campos: ['Total CP Empregador', 'Total CP Empregado', 'Total RAT/Terceiros'], dependencias: ['S-1299'], qtdEnviada: qtd('S-5011') },
  'S-5012': { codigo: 'S-5012', nome: 'IRRF Consolidado — Empregador', obrigatorio: false, retorno: true, descricao: 'Consolida todo o IRRF. Total de IR retido a recolher via DARF.', campos: ['Código Receita', 'Base IRRF Total', 'Valor Total a Recolher'], dependencias: ['S-1299'], qtdEnviada: qtd('S-5012') },
}))

const g = (cod: string): Evento => ev.value[cod]!
const linha1  = computed(() => [g('S-1000')])
const linha2  = computed(() => [g('S-1005'), g('S-1010'), g('S-1020'), g('S-1070')])
const linha3  = computed(() => [g('S-2190'), g('S-2200'), g('S-2300')])
const linha4  = computed(() => [g('S-2205'), g('S-2206'), g('S-2210'), g('S-2220'), g('S-2230')])
const linha5  = computed(() => [g('S-2299'), g('S-2399')])
const linha6  = computed(() => [g('S-2500'), g('S-3000')])
const linha7  = computed(() => [g('S-1200'), g('S-1202'), g('S-1260'), g('S-1270'), g('S-1280')])
const linha8  = computed(() => [g('S-1210')])
const linha9  = computed(() => [g('S-1298'), g('S-1299')])
const linha10 = computed(() => [g('S-5001'), g('S-5002'), g('S-5003'), g('S-5011'), g('S-5012')])
</script>

<style scoped>
.eventos-tab { padding: 24px 0; }
.titulo { font-size: 22px; font-weight: 700; color: #e0e6ed; margin: 0 0 6px 0; }
.subtitulo { font-size: 13px; color: rgba(224,230,237,0.45); margin: 0 0 12px 0; }
.legenda { display: flex; flex-wrap: wrap; gap: 18px; margin-bottom: 28px; }
.leg { display: flex; align-items: center; gap: 6px; font-size: 12px; color: rgba(224,230,237,0.55); }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.green { background: #22c55e; }
.dot.red { background: #ef4444; }
.dot.yellow { background: #eab308; }
.dot.gray { background: #64748b; }

.diagrama { display: flex; flex-direction: column; align-items: center; }
.seta-vertical { width: 2px; height: 28px; background: linear-gradient(to bottom, rgba(0,102,255,0.5), rgba(0,102,255,0.15)); position: relative; }
.seta-vertical::after { content: ''; position: absolute; bottom: -4px; left: -3px; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 6px solid rgba(0,102,255,0.5); }

.fase-tag { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: rgba(0,102,255,0.7); background: rgba(0,102,255,0.08); padding: 4px 14px; border-radius: 10px; margin: 6px 0 8px 0; }
.retorno-tag { color: rgba(100,116,139,0.8); background: rgba(100,116,139,0.1); }

.inicio-fim { font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; padding: 10px 32px; border-radius: 20px; }
.inicio { background: linear-gradient(135deg, rgba(0,102,255,0.2), rgba(0,102,255,0.08)); color: #0066ff; border: 1px solid rgba(0,102,255,0.3); }
.fim { background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(34,197,94,0.08)); color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }

.linha { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; width: 100%; max-width: 900px; }

.nw { flex: 0 1 auto; min-width: 130px; max-width: 200px; transition: all 0.3s; }
.nw.nexp { max-width: 400px; min-width: 300px; flex-basis: 100%; }

.nd { padding: 10px 14px; border-radius: 10px; cursor: pointer; border: 1.5px solid transparent; transition: all 0.2s; }
.nd:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.3); }

.c-green { background: rgba(34,197,94,0.12); border-color: rgba(34,197,94,0.35); }
.c-green:hover { border-color: rgba(34,197,94,0.7); }
.c-green .nd-cod { color: #22c55e; }

.c-red { background: rgba(239,68,68,0.10); border-color: rgba(239,68,68,0.3); }
.c-red:hover { border-color: rgba(239,68,68,0.6); }
.c-red .nd-cod { color: #ef4444; }

.c-yellow { background: rgba(234,179,8,0.10); border-color: rgba(234,179,8,0.25); }
.c-yellow:hover { border-color: rgba(234,179,8,0.5); }
.c-yellow .nd-cod { color: #eab308; }

.c-gray { background: rgba(100,116,139,0.10); border-color: rgba(100,116,139,0.25); }
.c-gray:hover { border-color: rgba(100,116,139,0.5); }
.c-gray .nd-cod { color: #94a3b8; }

.nd-top { display: flex; align-items: center; gap: 6px; }
.nd-cod { font-size: 14px; font-weight: 800; font-family: 'JetBrains Mono','Fira Code',monospace; letter-spacing: 0.03em; }
.nd-bdg { font-size: 9px; font-weight: 700; background: rgba(34,197,94,0.25); color: #22c55e; padding: 1px 5px; border-radius: 6px; }
.nd-arr { margin-left: auto; font-size: 12px; color: rgba(224,230,237,0.3); }
.nd-nm { font-size: 10px; color: rgba(224,230,237,0.55); margin-top: 2px; line-height: 1.3; }

.nd-det { padding: 10px 14px 14px; border-top: 1px solid rgba(0,102,255,0.12); margin-top: 6px; background: rgba(15,23,42,0.4); border-radius: 0 0 10px 10px; animation: expandIn 0.2s ease-out; }
.r { display: flex; gap: 8px; margin-bottom: 5px; align-items: baseline; }
.lb { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: rgba(224,230,237,0.3); white-space: nowrap; }
.vl { font-size: 12px; color: #e0e6ed; }
.v-ok { color: #22c55e; }
.v-pend { color: #ef4444; }
.v-opt { color: #eab308; }
.v-ret { color: #94a3b8; }

.desc { font-size: 12px; color: rgba(224,230,237,0.7); line-height: 1.6; margin: 8px 0; border-left: 2px solid rgba(0,102,255,0.2); padding-left: 10px; }
.tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px; align-items: center; }
.tg { font-size: 10px; padding: 2px 7px; border-radius: 4px; background: rgba(0,102,255,0.08); color: rgba(224,230,237,0.5); }
.dp { font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono','Fira Code',monospace; padding: 2px 8px; border-radius: 5px; background: rgba(0,102,255,0.15); color: #0066ff; }

@keyframes expandIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
</style>
