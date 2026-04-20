<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

interface Problema {
  id: number
  titulo: string
  arquivo: string
  categoria: string
  status: 'resolvido' | 'em_andamento' | 'bloqueado' | 'infraestrutura'
  grupo: 'appa' | 'geral'
  dataDescoberta: string
  impacto: string
  descricao: string
  detalhes: string[]
}

interface Nodo3D {
  id: number
  mesh: THREE.Mesh
  vx: number
  vy: number
  vz: number
  problema: Problema
}

const problemas: Problema[] = [
  {
    id: 1,
    titulo: 'Bug planSaude — Valores Inflados (6x a 200x)',
    arquivo: 'BUG_PLANSAUDE_VALORES_INFLADOS.md',
    categoria: 'Plano de Saúde',
    status: 'em_andamento',
    grupo: 'appa',
    dataDescoberta: '02/04/2026',
    impacto: '10.443 CPFs com valores errados',
    descricao: 'Script _rebuild_jan_plansaude.py usou wildcard LIKE 92% (99 rubricas ao invés de 4) + soma dupla indRetif=1 + indRetif=2.',
    detalhes: [
      'Bug 1: Filtro wildcard nat_rubr LIKE 92% capturou 99 rubricas ao invés das 4 corretas (607, 774, 775, 516)',
      'Bug 2: Soma de original + retificação dobrou os valores',
      'Exemplos: Waldelice R$367.30 (errado) vs R$0 (correto), Anaildes R$1.503.18 vs R$7.51 (200x inflado)',
      'Correção parcial: 426 CPFs corrigidos via Planilha 1600, script correcao_426_dobrado.py',
      '67 CPFs SINTACLUNS ainda pendentes',
    ],
  },
  {
    id: 2,
    titulo: 'planSaude Sindicato vs Empresarial (FAQ 14.4)',
    arquivo: 'PLANSAUDE_SINDICATO_VS_EMPRESARIAL.md',
    categoria: 'Plano de Saúde',
    status: 'em_andamento',
    grupo: 'geral',
    dataDescoberta: '14/04/2026',
    impacto: '~156 CPFs rejeitados (erro [8])',
    descricao: 'eSocial exige planSaude SOMENTE para plano coletivo empresarial. Sindicato, autogestão e plano por adesão NÃO devem ter.',
    detalhes: [
      'FAQ 14.4 do eSocial: planSaude só para plano coletivo empresarial',
      'Evidência: Set/2025 Bahia — 1.014 CPFs com saúde, ZERO planSaude (padrão sindicato)',
      '~156 CPFs sem código de operadora (repasse sindicato) → eSocial rejeita',
      'Solução aprovada: se cnpjOper == NULL → enviar S-1210 SEM bloco planSaude',
      'Distribuição: ~1.500 COM operadora, ~156 SEM (sindicato), ~9.000 sem saúde',
    ],
  },
  {
    id: 3,
    titulo: '67 CPFs SINTACLUNS — planSaude Fantasma',
    arquivo: '67CPFS_SINTACLUNS_PLANSAUDE_FANTASMA.md',
    categoria: 'Plano de Saúde',
    status: 'em_andamento',
    grupo: 'appa',
    dataDescoberta: '17/04/2026',
    impacto: '67 CPFs com planSaude indevido',
    descricao: '67 CPFs receberam planSaude SINTACLUNS que NUNCA existiu nos XMLs originais. Injetado pela planilha "certo" (duplicada).',
    detalhes: [
      'Operadora: SINTACLUNS (CNPJ 05597049000197, CodANS 415260)',
      'Verificado em 3 ZIPs originais (jan2025, dez2024, 29692114): ZERO planSaude',
      'Planilha "caso final" (1801 linhas): ZERO SINTACLUNS',
      'Planilha "certo" (6074 linhas, DUPLICADA): contém esses CPFs',
      'Valores: todos múltiplos de R$22 (titular R$22, dependente R$22 cada)',
      'Ação: remover planSaude inteiramente desses 67 CPFs',
    ],
  },
  {
    id: 4,
    titulo: '426 CPFs — planSaude Dobrado',
    arquivo: '426CPFS_PLANSAUDE_DOBRADO.md',
    categoria: 'Plano de Saúde',
    status: 'resolvido',
    grupo: 'appa',
    dataDescoberta: '17/04/2026',
    impacto: '426 CPFs corrigidos',
    descricao: '426 CPFs com valores dobrados, corrigidos via S-1210 retificação usando Planilha 1600 como fonte de verdade.',
    detalhes: [
      'Script: correcao_426_dobrado.py',
      'Resultado: 426 OK, 0 ERRO, 9 lotes enviados',
      'Fonte: Planilha 1600 cpfs.xlsx (col17=ValorEvento em centavos)',
    ],
  },
  {
    id: 5,
    titulo: 'Rubrica 522 — Incidência IR 09→67',
    arquivo: 'RUBRICA_522_INCIDENCIA_IR_ERRADA.md',
    categoria: 'Incidências IR',
    status: 'resolvido',
    grupo: 'geral',
    dataDescoberta: '16/04/2026',
    impacto: '751 CPFs corrigidos (739 OK)',
    descricao: 'Rubrica 522 (Plano Saúde) com codIncIRRF=09 (diversas) ao invés de 67 (assistência médica). Valores não somavam no totalizador IR.',
    detalhes: [
      'Mudança: codIncIRRF 09 → 67',
      'Resultado: 739 OK, 1 erro (recibo já retificado)',
      'Verificação: 5 CPFs checados aleatoriamente no portal — valores corretos',
      'Exemplo: R$49.40 médico + R$22.53 odonto = R$71.93 total ✓',
    ],
  },
  {
    id: 6,
    titulo: 'Rubrica 566 (INSS) — codIncIRRF 11→41',
    arquivo: 'RUBRICA_566_INSS_INCIDENCIA_IR.md',
    categoria: 'Incidências IR',
    status: 'bloqueado',
    grupo: 'geral',
    dataDescoberta: '02/04/2026',
    impacto: '16.000-20.000 pessoas sem dedução INSS',
    descricao: 'Rubrica 566 com codIncIRRF=11 (remuneração) deveria ser 41 (Previdência Social). INSS não aparece como dedução no extrator RF.',
    detalhes: [
      'Contexto: DIRF extinta em 2025 → tudo pelo eSocial agora',
      'Impacto: Dedução Previdência Social = ZERO no extrator RF',
      'Fluxo correção: S-1010 → S-1298 → S-1200 → S-1210 → S-1299 → DCTFWeb',
      'Bloqueador: 3 sistemas enviando simultaneamente + recibos divergentes',
      '~18 meses retroativos (jan/2025 a presente)',
    ],
  },
  {
    id: 7,
    titulo: 'S-1010 — 154 Rubricas Pendentes',
    arquivo: 'S1010_RUBRICAS_PENDENTES.md',
    categoria: 'Incidências IR',
    status: 'em_andamento',
    grupo: 'geral',
    dataDescoberta: '02/04/2026',
    impacto: '154 rubricas com incidências divergentes',
    descricao: 'Das 448 rubricas no cruzamento EB, 154 têm divergências. ~80 bloqueadas por natureza expirada.',
    detalhes: [
      'Total: 448 rubricas, 154 pendentes, ~80 bloqueadas',
      'Bot 90% pronto para executar correções em massa',
      'Aguarda finalização de naturezas (Marcos/Ana)',
    ],
  },
  {
    id: 8,
    titulo: 'Verba 47 — Dados Incompletos',
    arquivo: 'VERBA_47_INCOMPLETA.md',
    categoria: 'Incidências IR',
    status: 'bloqueado',
    grupo: 'appa',
    dataDescoberta: '02/04/2026',
    impacto: 'Afeta cálculos de IR',
    descricao: 'Não subiu errada, mas não completamente certa, ficou faltando um tiquinho de coisa.',
    detalhes: [
      'Segunda prioridade após rubrica 566',
      'Precisa investigação com Ana para identificar o que falta',
    ],
  },
  {
    id: 9,
    titulo: 'Dedução Dependentes Set — R$739k vs R$20k',
    arquivo: 'DEDUCAO_DEPENDENTES_SETEMBRO.md',
    categoria: 'Setembro/2025',
    status: 'bloqueado',
    grupo: 'appa',
    dataDescoberta: '16/04/2026',
    impacto: 'Discrepância massiva eSocial vs RF',
    descricao: 'S-5002 mostra R$739k em deduções de dependentes, RF extrator mostra ~R$20k. 3 gerações de S-5002 após exclusão massiva.',
    detalhes: [
      '06/Out: 7.762 S-1210 originais (R$739k)',
      '24/Out: S-3000 exclusão MASSIVA de 7.771 S-1210',
      '24/Out: Reenvio completo + S-1299 fechamento #3',
      '3 gerações: Gen1=R$739k, Gen2=R$0 (pós-exclusão), Gen3=R$739k (reenvio)',
      'Hipótese: DCTFWeb transmitida com Gen2 (zero)',
    ],
  },
  {
    id: 10,
    titulo: 'Recibos GI ≠ eSocial',
    arquivo: 'RECIBOS_GI_DIVERGENTES_ESOCIAL.md',
    categoria: 'Recibos / S-1210',
    status: 'em_andamento',
    grupo: 'geral',
    dataDescoberta: '02/04/2026',
    impacto: 'Impossibilidade de retificar via GI',
    descricao: '3 sistemas enviam ao eSocial (GI, Sandro, Easy-Social). Recibos ficam stale no GI após Sandro retificar.',
    detalhes: [
      'Sandro recusou compartilhar dados de recibos',
      'Solução: Easy-Social construindo extração independente de XMLs',
      'Denis baixa ZIPs, Xande extrai, Marcos integra DEPARA',
    ],
  },
  {
    id: 11,
    titulo: 'Duplicidade S-1210 — 100 CPFs (Erro [106])',
    arquivo: 'DUPLICIDADE_S1210_JANEIRO_100CPFS.md',
    categoria: 'Recibos / S-1210',
    status: 'bloqueado',
    grupo: 'appa',
    dataDescoberta: '15/04/2026',
    impacto: '100 CPFs com S-1210 duplicado',
    descricao: '100 CPFs com erro [106] (duplicidade). Possível conflito de perRef entre dezembro e janeiro.',
    detalhes: ['Precisa analisar ZIPs de dezembro/2024', 'ZIP disponível: ~596MB'],
  },
  {
    id: 12,
    titulo: 'Recibos Não Encontrados (~94 CPFs)',
    arquivo: 'RECIBOS_NAO_ENCONTRADOS_JANEIRO.md',
    categoria: 'Recibos / S-1210',
    status: 'em_andamento',
    grupo: 'appa',
    dataDescoberta: '16/04/2026',
    impacto: '~94 CPFs sem recibos para retificação',
    descricao: '~160 CPFs sem recibos corretos. Coleta manual em andamento (~66 coletados antes do eSocial cair).',
    detalhes: [
      'Script de 50 em 50 desenvolvido mas IA queimou consultas',
      'Coleta manual: Ana + Xande pelo portal',
      'eSocial caiu com 502 durante coleta',
    ],
  },
  {
    id: 13,
    titulo: 'Pensão Alimentícia — Beneficiário 28 anos',
    arquivo: 'PENSAO_ALIMENTICIA_BENEFICIARIOS.md',
    categoria: 'Pensão Alimentícia',
    status: 'em_andamento',
    grupo: 'appa',
    dataDescoberta: '16/04/2026',
    impacto: '1 CPF bloqueado (erro [8])',
    descricao: '1 CPF com pensão alimentícia e filho de 28 anos. Erro [8]: "Informação dos beneficiários deve ser preenchido".',
    detalhes: [
      '2 filhos registrados, ambos com CPF',
      'Filho de 1998 (28 anos) — limite pensão 21-24',
      'Ana vai marcar como "pensionista"',
    ],
  },
  {
    id: 14,
    titulo: 'Erro Precedência — Pensão Acordo (4 CPFs)',
    arquivo: 'ERRO_PRECEDENCIA_PENSAO_ACORDO.md',
    categoria: 'Pensão Alimentícia',
    status: 'bloqueado',
    grupo: 'appa',
    dataDescoberta: '16/04/2026',
    impacto: '4 CPFs rejeitados',
    descricao: '4 CPFs rejeitados por regra de precedência de pensão alimentícia acordo. Dados parecem corretos no GI.',
    detalhes: ['Evento: natureza pensão alimentícia acordo', 'Possível contato com Paloma'],
  },
  {
    id: 15,
    titulo: 'Verbas Indenizatórias Rescisão — Zeradas',
    arquivo: 'VERBAS_INDENIZATORIAS_RESCISAO_ZERADAS.md',
    categoria: 'Rescisão',
    status: 'bloqueado',
    grupo: 'geral',
    dataDescoberta: '02/04/2026',
    impacto: 'Todos os desligamentos afetados',
    descricao: 'Pagamentos de rescisão (aviso prévio, férias indenizadas, etc.) aparecendo ZERO no eSocial.',
    detalhes: ['Afeta: aviso prévio, férias, 13º, multa FGTS', 'Não priorizado ainda'],
  },
  {
    id: 16,
    titulo: 'Caso Ranieri — Demissão vs Maternidade',
    arquivo: 'CASO_RANIERI_DEMISSAO_MATERNIDADE.md',
    categoria: 'Rescisão',
    status: 'resolvido',
    grupo: 'appa',
    dataDescoberta: '16/04/2026',
    impacto: '1 funcionária',
    descricao: 'Gestante de Minas com carta de demissão atrasada. Decisão: pagar licença-maternidade, demitir após retorno.',
    detalhes: ['Empresa cúmplice na demora', 'Pagar licença, demitir depois'],
  },
  {
    id: 17,
    titulo: 'Mudança Operadora Set/2025',
    arquivo: 'OPERADORA_MUDANCA_SETEMBRO_2025.md',
    categoria: 'Operadora',
    status: 'resolvido',
    grupo: 'appa',
    dataDescoberta: '14/04/2026',
    impacto: 'Códigos diferentes por período',
    descricao: 'APPA trocou de operadora em set/2025. CNPJ e CodANS mudaram. Pipeline precisa usar código correto por período.',
    detalhes: [
      'Antes: CNPJ 44649812000138 / ANS 359017',
      'Depois: CNPJ 63554067000198 / ANS 368253',
    ],
  },
  {
    id: 18,
    titulo: 'Bebê Dental — Sindicato',
    arquivo: 'BEBE_DENTAL_SINDICATO.md',
    categoria: 'Cadastro',
    status: 'resolvido',
    grupo: 'appa',
    dataDescoberta: '16/04/2026',
    impacto: '1 beneficiário',
    descricao: 'Bebê aparecia como beneficiário dental mas não no sindicato. Ana corrigiu manualmente no GI.',
    detalhes: ['Eventos 621 e 605 alterados', 'Correção feita no GI'],
  },
  {
    id: 19,
    titulo: 'IA Queimando Consultas eSocial',
    arquivo: 'IA_QUEIMANDO_CONSULTAS_ESOCIAL.md',
    categoria: 'Infraestrutura',
    status: 'infraestrutura',
    grupo: 'geral',
    dataDescoberta: '16/04/2026',
    impacto: 'Bloqueio total de trabalho',
    descricao: 'IA queimou TODAS as 10 consultas diárias sem autorização. 4-5 incidentes recorrentes. Precisa hard limit.',
    detalhes: [
      'Limite: 10/dia (reseta 6h)',
      'Autorização máx IA: 5',
      'Sugestão Ana: hard limit 3',
    ],
  },
  {
    id: 20,
    titulo: 'eSocial — Portal Instável (502)',
    arquivo: 'ESOCIAL_INSTABILIDADE_PORTAL.md',
    categoria: 'Infraestrutura',
    status: 'infraestrutura',
    grupo: 'geral',
    dataDescoberta: '16/04/2026',
    impacto: 'Bloqueio de coleta e consultas',
    descricao: 'Portal eSocial com erro 502 Bad Gateway. Bloqueou coleta manual de recibos.',
    detalhes: ['~66 recibos coletados antes do crash', 'Tentar horários de menor uso'],
  },
  {
    id: 21,
    titulo: 'Internet Lenta — Ana',
    arquivo: 'INTERNET_LENTA_ANA.md',
    categoria: 'Infraestrutura',
    status: 'infraestrutura',
    grupo: 'appa',
    dataDescoberta: '16/04/2026',
    impacto: 'Coleta 5-10x mais lenta',
    descricao: 'Rede da Ana muito lenta vs Xande. Fabrício (TI) não assumiu. Possível WiFi instável.',
    detalhes: ['Xande: 4 recibos rápido. Ana: "carregando..."', 'Possível fix: cabo ethernet'],
  },
]

const conexoes: [number, number][] = [
  [1, 2], [1, 3], [1, 4], [2, 3], [2, 17], [3, 4],
  [5, 6], [5, 7], [6, 7], [6, 8], [7, 8],
  [10, 11], [10, 12], [11, 12],
  [13, 14], [15, 16],
  [12, 19], [12, 20], [19, 20], [20, 21],
  [1, 5], [9, 17], [6, 15],
]

const containerRef = ref<HTMLDivElement | null>(null)
const modalAberto = ref<Problema | null>(null)
const hoveredProblema = ref<Problema | null>(null)
const tooltipX = ref(0)
const tooltipY = ref(0)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let nodos: Nodo3D[] = []
let lines: THREE.Line[] = []
let glowSprites: THREE.Sprite[] = []
let animId = 0
let raycaster: THREE.Raycaster
let mouse = new THREE.Vector2()
let hoveredMesh: THREE.Mesh | null = null
let labelContainer: HTMLDivElement | null = null
let labelElements: HTMLDivElement[] = []

const BLUE = 0x0066ff
const ORANGE = 0xff6600
const SPREAD = 25
const BOUNDARY = 30

function grupoColor(g: string): number {
  return g === 'appa' ? ORANGE : BLUE
}

function grupoHex(g: string): string {
  return g === 'appa' ? '#ff6600' : '#0066ff'
}

function grupoLabel(g: string): string {
  return g === 'appa' ? 'APPA' : 'Geral'
}

function statusCor(s: string): string {
  return ({ resolvido: '#22c55e', em_andamento: '#eab308', bloqueado: '#ef4444', infraestrutura: '#f97316' }[s] ?? '#94a3b8')
}

function statusLabel(s: string): string {
  return ({ resolvido: '\u2705 Resolvido', em_andamento: '\uD83D\uDFE1 Em Andamento', bloqueado: '\uD83D\uDD34 Bloqueado', infraestrutura: '\u26A0\uFE0F Infra' }[s] ?? s)
}

function createGlowTexture(r: number, g: number, b: number): THREE.Texture {
  const size = 256
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')!
  const center = size / 2
  const gradient = ctx.createRadialGradient(center, center, 0, center, center, center)
  gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.6)`)
  gradient.addColorStop(0.15, `rgba(${r}, ${g}, ${b}, 0.35)`)
  gradient.addColorStop(0.4, `rgba(${r}, ${g}, ${b}, 0.12)`)
  gradient.addColorStop(0.7, `rgba(${r}, ${g}, ${b}, 0.03)`)
  gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`)
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, size, size)
  const tex = new THREE.CanvasTexture(canvas)
  return tex
}

function initScene() {
  const container = containerRef.value
  if (!container) return

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x060e1f)
  scene.fog = new THREE.FogExp2(0x060e1f, 0.008)

  camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000)
  camera.position.set(0, 8, 55)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.2
  container.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.rotateSpeed = 0.5
  controls.zoomSpeed = 0.8
  controls.minDistance = 15
  controls.maxDistance = 120
  controls.autoRotate = true
  controls.autoRotateSpeed = 0.25

  const ambientLight = new THREE.AmbientLight(0x1a1a3e, 0.6)
  scene.add(ambientLight)

  const pointLight1 = new THREE.PointLight(0x0088ff, 120, 250)
  pointLight1.position.set(25, 25, 35)
  scene.add(pointLight1)

  const pointLight2 = new THREE.PointLight(0x0044ff, 80, 200)
  pointLight2.position.set(-25, -15, -25)
  scene.add(pointLight2)

  const pointLight3 = new THREE.PointLight(0x6600ff, 40, 150)
  pointLight3.position.set(0, -20, 15)
  scene.add(pointLight3)

  const pointLight4 = new THREE.PointLight(0xffffff, 20, 100)
  pointLight4.position.set(0, 30, 0)
  scene.add(pointLight4)

  // Orange light for APPA side
  const pointLight5 = new THREE.PointLight(0xff6600, 60, 200)
  pointLight5.position.set(-20, 10, 15)
  scene.add(pointLight5)

  raycaster = new THREE.Raycaster()

  // Label overlay container
  labelContainer = document.createElement('div')
  labelContainer.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;overflow:hidden;'
  container.appendChild(labelContainer)

  createNodes()
  createLines()
}

function createNodes() {
  const sphereGeo = new THREE.SphereGeometry(1, 32, 32)
  const glowTexBlue = createGlowTexture(0, 120, 255)
  const glowTexOrange = createGlowTexture(255, 120, 0)

  // Separate indices for positioning each group on different sides
  const appaProblemas = problemas.filter(p => p.grupo === 'appa')
  const geralProblemas = problemas.filter(p => p.grupo === 'geral')

  problemas.forEach((p) => {
    const isAppa = p.grupo === 'appa'
    const groupList = isAppa ? appaProblemas : geralProblemas
    const groupIdx = groupList.indexOf(p)
    const groupCount = groupList.length

    // APPA on left side (negative X), Geral on right side (positive X)
    const sideOffset = isAppa ? -SPREAD * 0.45 : SPREAD * 0.45
    const angle = (groupIdx / groupCount) * Math.PI * 2
    const r = SPREAD * (0.2 + Math.random() * 0.4)
    const height = (Math.random() - 0.5) * SPREAD * 0.8

    const nodeColor = grupoColor(p.grupo)
    const material = new THREE.MeshStandardMaterial({
      color: nodeColor,
      emissive: nodeColor,
      emissiveIntensity: 0.6,
      metalness: 0.5,
      roughness: 0.2,
    })

    const size = 0.8 + p.detalhes.length * 0.12
    const mesh = new THREE.Mesh(sphereGeo, material)
    mesh.scale.setScalar(size)
    mesh.position.set(
      sideOffset + Math.cos(angle) * r,
      height,
      Math.sin(angle) * r,
    )
    mesh.userData = { problemaId: p.id, baseScale: size }
    scene.add(mesh)

    // Neon glow sprite
    const spriteMat = new THREE.SpriteMaterial({
      map: isAppa ? glowTexOrange : glowTexBlue,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      opacity: 0.7,
    })
    const sprite = new THREE.Sprite(spriteMat)
    sprite.scale.setScalar(size * 5)
    mesh.add(sprite)
    glowSprites.push(sprite)

    // HTML label
    const label = document.createElement('div')
    label.className = 'node-label'
    const groupTag = isAppa ? '<span class=\"node-grupo node-grupo-appa\">APPA</span>' : '<span class=\"node-grupo node-grupo-geral\">GERAL</span>'
    label.innerHTML = `<span class="node-id" style="border-color: ${grupoHex(p.grupo)}80; box-shadow: 0 0 8px ${grupoHex(p.grupo)}66">${p.id}</span>${groupTag}<span class="node-title">${truncTitle(p.titulo, 28)}</span>`
    labelContainer!.appendChild(label)
    labelElements.push(label)

    nodos.push({
      id: p.id,
      mesh,
      vx: (Math.random() - 0.5) * 0.003,
      vy: (Math.random() - 0.5) * 0.003,
      vz: (Math.random() - 0.5) * 0.003,
      problema: p,
    })
  })
}

function truncTitle(s: string, max: number): string {
  return s.length > max ? s.slice(0, max - 1) + '\u2026' : s
}

function createLines() {
  const lineMat = new THREE.LineBasicMaterial({
    color: 0x1144aa,
    transparent: true,
    opacity: 0.35,
  })

  for (const [aId, bId] of conexoes) {
    const a = nodos.find((n) => n.id === aId)
    const b = nodos.find((n) => n.id === bId)
    if (!a || !b) continue

    const geo = new THREE.BufferGeometry().setFromPoints([
      a.mesh.position.clone(),
      b.mesh.position.clone(),
    ])
    const line = new THREE.Line(geo, lineMat)
    line.userData = { from: aId, to: bId }
    scene.add(line)
    lines.push(line)
  }
}

function updateLines() {
  for (const line of lines) {
    const { from, to } = line.userData
    const a = nodos.find((n) => n.id === from)
    const b = nodos.find((n) => n.id === to)
    if (!a || !b) continue
    const positions = line.geometry.attributes.position as THREE.BufferAttribute
    positions.setXYZ(0, a.mesh.position.x, a.mesh.position.y, a.mesh.position.z)
    positions.setXYZ(1, b.mesh.position.x, b.mesh.position.y, b.mesh.position.z)
    positions.needsUpdate = true
  }
}

function updateLabels() {
  const container = containerRef.value
  if (!container) return
  const w = container.clientWidth
  const h = container.clientHeight

  nodos.forEach((n, i) => {
    const label = labelElements[i]
    // Get world position of the mesh and project to screen
    const worldPos = new THREE.Vector3()
    n.mesh.getWorldPosition(worldPos)

    // Offset downward in world space by the sphere radius
    const offsetPos = worldPos.clone()
    const ndc = offsetPos.clone().project(camera)

    if (ndc.z > 1) {
      label.style.display = 'none'
      return
    }

    const screenX = (ndc.x * 0.5 + 0.5) * w
    const screenY = (-ndc.y * 0.5 + 0.5) * h

    // Calculate screen-space sphere radius for title offset
    const baseScale = n.mesh.userData.baseScale as number
    const dist = camera.position.distanceTo(worldPos)
    const screenRadius = (baseScale * 600) / dist

    // Scale the ID circle to match the sphere's screen size
    const idEl = label.querySelector('.node-id') as HTMLElement
    if (idEl) {
      const idSize = Math.max(18, screenRadius * 1.2)
      idEl.style.width = `${idSize}px`
      idEl.style.height = `${idSize}px`
      idEl.style.fontSize = `${Math.max(8, idSize * 0.45)}px`
    }

    // Position: center the ID circle on the sphere, title hangs below
    const idHeight = Math.max(18, screenRadius * 1.2)
    label.style.display = ''
    label.style.transform = `translate(-50%, -${idHeight / 2}px) translate(${screenX}px, ${screenY}px)`
    // Title gap: push it below the sphere
    const titleEl = label.querySelector('.node-title') as HTMLElement
    if (titleEl) {
      titleEl.style.marginTop = `${Math.max(0, screenRadius - idHeight / 2 + 4)}px`
    }
    const opacity = Math.max(0, Math.min(1, 1 - (dist - 25) / 55))
    label.style.opacity = String(opacity)
  })
}

function physics3D() {
  const time = performance.now() * 0.001
  for (const n of nodos) {
    const pos = n.mesh.position

    // Gravity toward center (very gentle)
    n.vx += (0 - pos.x) * 0.00004
    n.vy += (0 - pos.y) * 0.00004
    n.vz += (0 - pos.z) * 0.00004

    // Repulsion between nodes
    for (const m of nodos) {
      if (m.id === n.id) continue
      const dx = pos.x - m.mesh.position.x
      const dy = pos.y - m.mesh.position.y
      const dz = pos.z - m.mesh.position.z
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1
      if (dist < 8) {
        const force = (8 - dist) * 0.001
        n.vx += (dx / dist) * force
        n.vy += (dy / dist) * force
        n.vz += (dz / dist) * force
      }
    }

    // Spring edges
    for (const [a, b] of conexoes) {
      if (a !== n.id && b !== n.id) continue
      const other = nodos.find((nn) => nn.id === (a === n.id ? b : a))
      if (!other) continue
      const dx = other.mesh.position.x - pos.x
      const dy = other.mesh.position.y - pos.y
      const dz = other.mesh.position.z - pos.z
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1
      const target = 10
      const force = (dist - target) * 0.00008
      n.vx += (dx / dist) * force
      n.vy += (dy / dist) * force
      n.vz += (dz / dist) * force
    }

    // Very subtle organic breathing
    const phase = n.id * 1.37
    n.vx += Math.sin(time * 0.12 + phase) * 0.0004
    n.vy += Math.cos(time * 0.1 + phase * 1.5) * 0.0004
    n.vz += Math.sin(time * 0.08 + phase * 0.8) * 0.0004

    // Strong damping for smooth stop
    n.vx *= 0.96
    n.vy *= 0.96
    n.vz *= 0.96

    // Apply velocity
    pos.x += n.vx
    pos.y += n.vy
    pos.z += n.vz

    // Boundary
    if (pos.x < -BOUNDARY) { pos.x = -BOUNDARY; n.vx *= -0.5 }
    if (pos.x > BOUNDARY) { pos.x = BOUNDARY; n.vx *= -0.5 }
    if (pos.y < -BOUNDARY) { pos.y = -BOUNDARY; n.vy *= -0.5 }
    if (pos.y > BOUNDARY) { pos.y = BOUNDARY; n.vy *= -0.5 }
    if (pos.z < -BOUNDARY) { pos.z = -BOUNDARY; n.vz *= -0.5 }
    if (pos.z > BOUNDARY) { pos.z = BOUNDARY; n.vz *= -0.5 }

    // Subtle pulsing glow
    const mat = n.mesh.material as THREE.MeshStandardMaterial
    mat.emissiveIntensity = 0.55 + Math.sin(time * 0.8 + phase) * 0.08
  }
}

function onPointerMove(e: PointerEvent) {
  const container = containerRef.value
  if (!container) return
  const rect = container.getBoundingClientRect()
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const meshes = nodos.map((n) => n.mesh)
  const intersects = raycaster.intersectObjects(meshes)

  if (hoveredMesh && hoveredMesh !== intersects[0]?.object) {
    const mat = hoveredMesh.material as THREE.MeshStandardMaterial
    mat.emissiveIntensity = 0.5
    const base = hoveredMesh.userData.baseScale
    hoveredMesh.scale.setScalar(base)
    hoveredMesh = null
    hoveredProblema.value = null
  }

  if (intersects.length > 0) {
    const mesh = intersects[0].object as THREE.Mesh
    if (mesh !== hoveredMesh) {
      hoveredMesh = mesh
      const mat = mesh.material as THREE.MeshStandardMaterial
      mat.emissiveIntensity = 1.2
      const base = mesh.userData.baseScale
      mesh.scale.setScalar(base * 1.4)
      const id = mesh.userData.problemaId
      hoveredProblema.value = problemas.find((pp) => pp.id === id) ?? null
    }
    tooltipX.value = e.clientX - rect.left
    tooltipY.value = e.clientY - rect.top
    container.style.cursor = 'pointer'
  } else {
    container.style.cursor = 'grab'
  }
}

function onPointerDown(e: PointerEvent) {
  const container = containerRef.value
  if (!container) return
  const rect = container.getBoundingClientRect()
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const meshes = nodos.map((n) => n.mesh)
  const intersects = raycaster.intersectObjects(meshes)

  if (intersects.length > 0) {
    const id = intersects[0].object.userData.problemaId
    const p = problemas.find((pp) => pp.id === id)
    if (p) modalAberto.value = p
  }
}

function animate() {
  animId = requestAnimationFrame(animate)
  physics3D()
  updateLines()
  updateLabels()
  controls.update()
  renderer.render(scene, camera)
}

function onResize() {
  const container = containerRef.value
  if (!container) return
  camera.aspect = container.clientWidth / container.clientHeight
  camera.updateProjectionMatrix()
  renderer.setSize(container.clientWidth, container.clientHeight)
}

onMounted(() => {
  initScene()
  animate()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', onResize)
  if (renderer) {
    renderer.dispose()
    renderer.domElement.remove()
  }
  if (labelContainer) labelContainer.remove()
})

const legendItems = [
  { label: 'Resolvido', cor: '#22c55e' },
  { label: 'Em Andamento', cor: '#eab308' },
  { label: 'Bloqueado', cor: '#ef4444' },
  { label: 'Infraestrutura', cor: '#f97316' },
]

const grupoItems = [
  { label: `APPA (${problemas.filter(p => p.grupo === 'appa').length})`, cor: '#ff6600' },
  { label: `Geral (${problemas.filter(p => p.grupo === 'geral').length})`, cor: '#0066ff' },
]
</script>

<template>
  <div class="grafo-page">
    <div class="grafo-header">
      <div>
        <h1 class="text-xl font-bold text-white">Problemas APPA</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Grafo 3D interativo · {{ problemas.length }} problemas · {{ conexoes.length }} conexões
          <span class="text-slate-600 ml-2">Arraste para girar · Scroll para zoom · Clique em uma esfera</span>
        </p>
      </div>
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-3">
          <span class="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Grupo:</span>
          <div v-for="item in grupoItems" :key="item.label" class="flex items-center gap-1.5">
            <div class="w-3 h-3 rounded-full" :style="{ background: item.cor, boxShadow: '0 0 6px ' + item.cor }"></div>
            <span class="text-[10px] text-slate-400">{{ item.label }}</span>
          </div>
        </div>
        <div class="w-px h-4 bg-slate-700"></div>
        <div class="flex items-center gap-3">
          <span class="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Status:</span>
          <div v-for="item in legendItems" :key="item.label" class="flex items-center gap-1.5">
            <div class="w-3 h-3 rounded-full" :style="{ background: item.cor, boxShadow: '0 0 6px ' + item.cor }"></div>
            <span class="text-[10px] text-slate-400">{{ item.label }}</span>
          </div>
        </div>
      </div>
    </div>
    <div ref="containerRef" class="grafo-canvas-container" @pointermove="onPointerMove" @pointerdown="onPointerDown">
      <!-- Tooltip flutuante -->
      <div v-if="hoveredProblema" class="node-tooltip" :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }">
        <div class="tooltip-status" :style="{ background: statusCor(hoveredProblema.status) }"></div>
        <div class="tooltip-body">
          <div class="tooltip-title">{{ hoveredProblema.titulo }}</div>
          <div class="tooltip-meta">
            <span class="tooltip-badge" :style="{ color: statusCor(hoveredProblema.status) }">{{ statusLabel(hoveredProblema.status) }}</span>
            <span class="tooltip-sep">·</span>
            <span class="tooltip-grupo" :style="{ color: grupoHex(hoveredProblema.grupo) }">{{ grupoLabel(hoveredProblema.grupo) }}</span>
            <span class="tooltip-sep">·</span>
            <span>{{ hoveredProblema.impacto }}</span>
          </div>
          <div class="tooltip-desc">{{ hoveredProblema.descricao.slice(0, 120) }}{{ hoveredProblema.descricao.length > 120 ? '…' : '' }}</div>
        </div>
      </div>
    </div>
    <Teleport to="body">
      <div v-if="modalAberto" class="modal-overlay" @click.self="modalAberto = null">
        <div class="modal-content">
          <button class="modal-close" @click="modalAberto = null">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
          <div class="modal-header">
            <div class="modal-status-bar" :style="{ background: statusCor(modalAberto.status) }"></div>
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <span class="modal-status-badge" :style="{ background: statusCor(modalAberto.status) + '20', color: statusCor(modalAberto.status), borderColor: statusCor(modalAberto.status) + '50' }">{{ statusLabel(modalAberto.status) }}</span>
                <span class="modal-grupo-badge" :style="{ background: grupoHex(modalAberto.grupo) + '20', color: grupoHex(modalAberto.grupo), borderColor: grupoHex(modalAberto.grupo) + '50' }">{{ grupoLabel(modalAberto.grupo) }}</span>
                <span class="modal-cat-badge">{{ modalAberto.categoria }}</span>
              </div>
              <h2 class="text-lg font-bold text-white leading-tight">{{ modalAberto.titulo }}</h2>
            </div>
          </div>
          <div class="modal-meta">
            <div class="modal-meta-item">
              <span class="modal-meta-label">Data</span>
              <span class="modal-meta-value">{{ modalAberto.dataDescoberta }}</span>
            </div>
            <div class="modal-meta-item">
              <span class="modal-meta-label">Impacto</span>
              <span class="modal-meta-value">{{ modalAberto.impacto }}</span>
            </div>
            <div class="modal-meta-item">
              <span class="modal-meta-label">Arquivo</span>
              <span class="modal-meta-value font-mono text-[#0066FF]">{{ modalAberto.arquivo }}</span>
            </div>
          </div>
          <div class="modal-section">
            <h3 class="modal-section-title">Descrição</h3>
            <p class="text-sm text-slate-300 leading-relaxed">{{ modalAberto.descricao }}</p>
          </div>
          <div class="modal-section">
            <h3 class="modal-section-title">Detalhes</h3>
            <ul class="space-y-2">
              <li v-for="(d, i) in modalAberto.detalhes" :key="i" class="flex items-start gap-2.5 text-sm text-slate-300">
                <span class="text-[#0066FF] mt-0.5 shrink-0 text-lg leading-none">&bull;</span>
                <span>{{ d }}</span>
              </li>
            </ul>
          </div>
          <div class="modal-section">
            <h3 class="modal-section-title">Problemas Conectados</h3>
            <div class="flex flex-wrap gap-2">
              <button v-for="conn in conexoes.filter(([a, b]) => a === modalAberto!.id || b === modalAberto!.id).map(([a, b]) => problemas.find((p) => p.id === (a === modalAberto!.id ? b : a))).filter(Boolean)" :key="conn!.id" class="connected-pill" :style="{ borderColor: statusCor(conn!.status) + '60' }" @click="modalAberto = conn!">
                <div class="w-2 h-2 rounded-full shrink-0" :style="{ background: statusCor(conn!.status) }"></div>
                <span class="text-xs text-slate-300">{{ conn!.titulo }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.grafo-page { display: flex; flex-direction: column; height: calc(100vh - 112px); overflow: hidden; }
.grafo-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; border-bottom: 1px solid rgba(0, 102, 255, 0.15); background: rgba(6, 14, 31, 0.8); flex-shrink: 0; }
.grafo-canvas-container { flex: 1; position: relative; overflow: hidden; cursor: grab; }

/* Node labels (HTML overlay) */
:deep(.node-label) {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  pointer-events: none;
  white-space: nowrap;
  transition: opacity 0.2s;
}
:deep(.node-id) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, rgba(100, 180, 255, 0.5), rgba(0, 102, 255, 0.35) 60%, rgba(0, 60, 180, 0.2));
  border: 1.5px solid rgba(0, 140, 255, 0.6);
  box-shadow: 0 0 8px rgba(0, 120, 255, 0.4), inset 0 0 6px rgba(100, 180, 255, 0.15);
  color: #c8e4ff;
  font-weight: 700;
  font-family: system-ui, sans-serif;
  transition: width 0.1s, height 0.1s;
}
:deep(.node-title) {
  font-size: 10px;
  font-weight: 500;
  color: rgba(180, 210, 255, 0.8);
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.8);
  font-family: system-ui, sans-serif;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
}
:deep(.node-grupo) {
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: system-ui, sans-serif;
}
:deep(.node-grupo-appa) {
  color: #ff9944;
  background: rgba(255, 102, 0, 0.15);
  border: 1px solid rgba(255, 102, 0, 0.3);
}
:deep(.node-grupo-geral) {
  color: #66aaff;
  background: rgba(0, 102, 255, 0.15);
  border: 1px solid rgba(0, 102, 255, 0.3);
}

/* Tooltip */
.node-tooltip {
  position: absolute;
  pointer-events: none;
  z-index: 100;
  transform: translate(16px, -50%);
  display: flex;
  width: 320px;
  background: rgba(8, 15, 38, 0.95);
  border: 1px solid rgba(0, 102, 255, 0.3);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 20px rgba(0, 102, 255, 0.1);
  backdrop-filter: blur(12px);
  animation: tooltipIn 0.15s ease;
}
.tooltip-status { width: 4px; flex-shrink: 0; }
.tooltip-body { padding: 12px 14px; flex: 1; min-width: 0; }
.tooltip-title { font-size: 13px; font-weight: 700; color: #fff; line-height: 1.3; margin-bottom: 6px; }
.tooltip-meta { display: flex; align-items: center; gap: 6px; font-size: 10px; color: #64748b; margin-bottom: 6px; }
.tooltip-badge { font-weight: 600; }
.tooltip-grupo { font-weight: 600; }
.tooltip-sep { color: #334155; }
.tooltip-desc { font-size: 11px; color: #94a3b8; line-height: 1.4; }

@keyframes tooltipIn { from { opacity: 0; transform: translate(16px, -50%) scale(0.95); } to { opacity: 1; transform: translate(16px, -50%) scale(1); } }

.modal-overlay { position: fixed; inset: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(8px); animation: fadeIn 0.2s ease; }
.modal-content { position: relative; width: 90%; max-width: 680px; max-height: 85vh; overflow-y: auto; background: #0d1530; border: 1px solid rgba(0, 102, 255, 0.2); border-radius: 16px; padding: 0; animation: scaleIn 0.25s ease; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 102, 255, 0.08); }
.modal-content::-webkit-scrollbar { width: 6px; }
.modal-content::-webkit-scrollbar-track { background: transparent; }
.modal-content::-webkit-scrollbar-thumb { background: rgba(0, 102, 255, 0.3); border-radius: 3px; }
.modal-close { position: absolute; top: 16px; right: 16px; z-index: 10; display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1); background: rgba(255, 255, 255, 0.05); color: #94a3b8; cursor: pointer; transition: all 0.15s; }
.modal-close:hover { background: rgba(255, 255, 255, 0.12); color: #fff; }
.modal-header { display: flex; gap: 16px; padding: 28px 28px 20px; }
.modal-status-bar { width: 4px; border-radius: 2px; flex-shrink: 0; align-self: stretch; }
.modal-status-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; border: 1px solid; }
.modal-grupo-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; border: 1px solid; }
.modal-cat-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 500; color: #0066ff; background: rgba(0, 102, 255, 0.1); border: 1px solid rgba(0, 102, 255, 0.25); }
.modal-meta { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; margin: 0 28px; border-radius: 10px; overflow: hidden; background: rgba(255, 255, 255, 0.06); }
.modal-meta-item { padding: 12px 16px; background: rgba(10, 16, 36, 0.6); }
.modal-meta-label { display: block; font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 4px; }
.modal-meta-value { display: block; font-size: 12px; color: #e2e8f0; font-weight: 500; }
.modal-section { padding: 20px 28px; border-top: 1px solid rgba(255, 255, 255, 0.05); }
.modal-section-title { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; font-weight: 600; margin-bottom: 10px; }
.connected-pill { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 8px; background: rgba(255, 255, 255, 0.04); border: 1px solid; cursor: pointer; transition: background 0.15s; }
.connected-pill:hover { background: rgba(255, 255, 255, 0.08); }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes scaleIn { from { opacity: 0; transform: scale(0.92); } to { opacity: 1; transform: scale(1); } }
</style>
