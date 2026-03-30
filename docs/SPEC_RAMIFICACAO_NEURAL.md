# Especificação: Ramificação Neural do Cérebro → Opções

## Visão Geral

Quando o usuário clica em uma região do cérebro, deve aparecer uma **rede de fios neurais** saindo da base do cérebro (da fissura central), que se juntam formando um **tronco grosso** que desce até as opções de navegação. Partículas de energia azul luminosas viajam constantemente pelos fios, do cérebro para as opções. As opções no final devem ter visual que combine com o cérebro (bordas brilhantes, glow).

## Referência Visual

A imagem de referência (enviada pelo usuário) mostra:

- Vários fios finos (vermelho, verde, amarelo) saindo de diferentes pontos do cérebro
- Os fios se curvam e convergem para um ponto central abaixo do cérebro
- A ideia é que esses fios sejam azul-cyan (#5ac8f5), mesma cor dos sulcos do cérebro

## Estado Atual (ANTES)

- Um único stem (linha de 3px) desce do cérebro
- Um ponto de junção
- Um rail horizontal conecta os cards
- Drops verticais levam aos cards
- Cards com borda azul sutil
- **Problema**: muito simples, parece um diagrama, não uma ramificação neural viva

## Estado Desejado (DEPOIS)

### 1. Múltiplos Fios Neurais (SVG animado)

Quando o grupo expande, **5-7 fios finos** (1-2px cada) saem de diferentes pontos na base do cérebro:

- Os fios saem de posições diferentes na parte inferior do cérebro (espalhados horizontalmente)
- Cada fio tem um caminho curvo diferente (usando SVG `<path>` com curvas Bézier)
- Os fios **convergem** para um ponto central ~60px abaixo do cérebro
- Do ponto de convergência, os fios se fundem em linhas que se ramificam para cada card
- Cor: `#5ac8f5` (cyan do cérebro) com opacidades variadas (0.3 a 0.7)
- Box-shadow/filter glow sutil em cada fio

### 2. Partículas de Energia (Bolinhas azuis animadas)

- Pequenas bolinhas luminosas (3-5px de diâmetro) viajam pelos fios
- Cada bolinha segue o path de um fio específico (usando CSS `offset-path` ou SVG `animateMotion`)
- **Velocidades diferentes**: cada bolinha tem duração de animação entre 1.5s e 3s
- **Tempos de início diferentes**: cada bolinha começa em momentos diferentes (stagger)
- As bolinhas têm glow (`box-shadow: 0 0 8px #5ac8f5`)
- Pelo menos 8-12 bolinhas visíveis ao mesmo tempo, em canais diferentes
- A animação é **contínua/infinita** enquanto o painel estiver aberto
- As bolinhas vão do cérebro → ponto de convergência → ramificação → card

### 3. Tronco Central

- Onde os fios convergem, a espessura visual aumenta (de 1-2px para ~4px)
- O ponto de convergência tem um glow mais forte
- Do tronco, os fios se ramificam novamente para cada card

### 4. Cards com Visual Cerebral

Os cards no final das ramificações devem:

- Ter **borda mais brilhante** (2px solid #5ac8f5 com glow forte)
- Background mais translúcido mostrando o glow
- Um **pulso de glow** sutil na borda (animação tipo breathing, 2-3s)
- Quando hover: glow intensifica significativamente
- O efeito todo deve parecer que energia está fluindo do cérebro para os cards

### 5. Animação de Entrada

Quando o usuário clica numa região:

1. **0-300ms**: Fios começam a "crescer" da base do cérebro (stroke-dasharray animation)
2. **200-500ms**: Fios chegam ao ponto de convergência
3. **400-700ms**: Ramificações se estendem até os cards
4. **500-800ms**: Cards aparecem com pop-in
5. **600ms+**: Partículas começam a fluir (e continuam infinitamente)

## Implementação Técnica

### SVG para os fios

```html
<svg class="neural-wires" viewBox="0 0 800 200">
  <!-- Fio 1: sai da esquerda do centro do cérebro -->
  <path
    d="M350,0 C340,30 370,60 400,80 L400,120 L200,180"
    stroke="#5ac8f5"
    stroke-width="1.5"
    fill="none"
    opacity="0.5"
  />
  <!-- Fio 2: sai do centro -->
  <path d="M400,0 C400,40 400,60 400,80 L400,120 L400,180" ... />
  <!-- ... mais fios -->

  <!-- Partículas usando animateMotion -->
  <circle r="3" fill="#5ac8f5">
    <animateMotion
      dur="2s"
      repeatCount="indefinite"
      path="M350,0 C340,30 ..."
    />
  </circle>
</svg>
```

### CSS Variables

```css
--brain-blue: #5ac8f5;
--brain-glow: rgba(90, 200, 245, 0.55);
--wire-thin: 1.5px;
--wire-thick: 4px;
```

### Partículas

- Usar `<circle>` SVG com `<animateMotion>` seguindo os mesmos paths dos fios
- Cada partícula tem `dur` diferente (1.5s, 2s, 2.5s, 3s)
- `begin` staggered (0s, 0.3s, 0.7s, 1.2s, ...)
- `filter: drop-shadow(0 0 6px #5ac8f5)` para glow

## Critério de Aceite

- [ ] Ao clicar numa região, aparecem 5+ fios saindo da base do cérebro
- [ ] Fios convergem para um ponto central
- [ ] Fios se ramificam até os cards
- [ ] 8+ partículas luminosas viajam pelos fios continuamente
- [ ] Partículas têm velocidades e tempos diferentes
- [ ] Cards têm borda brilhante com glow pulsante
- [ ] Cards hover intensifica o glow
- [ ] Animação de entrada suave (fios "crescem")
- [ ] Visual geral parece energia neural fluindo do cérebro
- [ ] Funciona com 2 items (Automação) e 3 items (Arquivos/Rubricas)
- [ ] Navegação aos clicks nos cards continua funcionando
