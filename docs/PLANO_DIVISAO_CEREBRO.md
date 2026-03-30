# Plano de Divisão do Cérebro — Navegação Interativa

## Objetivo

Dividir a imagem PNG do cérebro (`docs/image.png`) em **3 regiões clicáveis** que, quando
montadas juntas no frontend, formam **exatamente** a imagem original — sem falhas, sem
sobreposições, sem costuras visíveis.

---

## Imagem de Referência

O usuário forneceu a imagem do cérebro com 3 contornos desenhados à mão indicando
as regiões:

| Cor do contorno | Região                   | ID Vue      | Grupo de navegação         |
| --------------- | ------------------------ | ----------- | -------------------------- |
| **Vermelho**    | Topo (ambos hemisférios) | `automacao` | Automação eSocial          |
| **Verde**       | Inferior-esquerdo        | `arquivos`  | Arquivos, Folhas e Tabelas |
| **Amarelo**     | Inferior-direito         | `rubricas`  | Rubricas                   |

---

## Anatomia da Divisão

A divisão NÃO é um corte reto. Ela segue contornos **orgânicos** que acompanham os
sulcos naturais do cérebro:

```
          ┌─────────────────────────┐
          │                         │
          │    VERMELHO (Automação)  │
          │     Topo do cérebro     │
          │                         │
     ─────┼───── sulco lateral ─────┼─────
          │           │             │
          │  VERDE    │  AMARELO    │
          │ (Tabelas) │ (Rubricas)  │
          │           │             │
          └───────────┴─────────────┘
                 fissura
              longitudinal
```

### Pontos-chave da divisão:

1. **Linha horizontal orgânica** (~55% da altura do cérebro): separa topo das regiões inferiores
2. **Linha vertical orgânica** (centro, fissura longitudinal): separa inferior-esquerdo do inferior-direito
3. Ambas as linhas são **curvas suaves**, não retas

---

## Abordagem Técnica

### Ferramenta: Python + Pillow

1. Carregar a imagem original (1536×1024, RGBA com fundo transparente)
2. Definir **3 polígonos** com coordenadas baseadas nos contornos da referência do usuário
3. Para cada região, criar uma máscara (preto/branco) com o polígono
4. Aplicar a máscara: manter alfa original dentro da máscara, zerá-lo fora
5. Salvar cada região como PNG separado em `frontend/public/`
6. Todas as imagens mantêm as dimensões 1536×1024 — pixels fora da região ficam transparentes

### Por que manter dimensões iguais?

- Empilhando as 3 imagens com `position: absolute`, elas se **encaixam perfeitamente**
- Não precisa de offsets, transforms ou cálculos de layout
- A soma visual = imagem original pixel por pixel

---

## Coordenadas dos Polígonos (estimadas da referência)

A imagem é 1536×1024. O cérebro ocupa aproximadamente de (130,30) a (1400,960).

### Região VERMELHA (Topo — Automação)

Polígono que cobre a metade superior do cérebro. Limite inferior é uma curva
que vai da borda esquerda do cérebro, passando pelo centro, até a borda direita.

Pontos aproximados:

```
(0, 0) → (1536, 0) → (1536, ~480) → curva pelo centro → (0, ~520) → fecha
```

A linha divisória segue o sulco lateral — desce um pouco mais nas laterais e
sobe no centro, criando uma curva côncava suave.

### Região VERDE (Inferior-Esquerda — Arquivos)

Polígono que cobre o quadrante inferior-esquerdo do cérebro.

Pontos aproximados:

```
(0, ~520) → segue a curva do topo até o centro (~768, ~480) → desce pelo
centro (fissura longitudinal) até embaixo (~768, 1024) → (0, 1024) → fecha
```

### Região AMARELA (Inferior-Direita — Rubricas)

Polígono que cobre o quadrante inferior-direito do cérebro.

Pontos aproximados:

```
(~768, ~480) → segue a curva do topo até a direita (1536, ~480) →
(1536, 1024) → (~768, 1024) → sobe pelo centro → fecha
```

> **Nota:** Os valores exatos serão refinados iterativamente testando no browser.

---

## Frontend — BrainNav.vue

### Estrutura HTML

```html
<div class="brain-nav" style="position: relative; width: 400px;">
  <img src="/brain-top.png" class="brain-region" data-region="automacao" />
  <img
    src="/brain-bottom-left.png"
    class="brain-region"
    data-region="arquivos"
  />
  <img
    src="/brain-bottom-right.png"
    class="brain-region"
    data-region="rubricas"
  />
</div>
```

### CSS

```css
.brain-nav {
  position: relative;
}
.brain-region {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: auto;
  cursor: pointer;
  transition:
    filter 0.2s,
    transform 0.15s;
}
.brain-region:hover {
  filter: brightness(1.3) drop-shadow(0 0 12px rgba(77, 201, 246, 0.6));
  transform: scale(1.02);
}
```

### Comportamento

- Cada `<img>` é clicável e emite `@select` com o ID da região
- Hover: brilho aumenta e glow azul aparece na peça
- As 3 imagens empilhadas = cérebro completo perfeito
- Pointer-events só ativam em pixels não-transparentes (via `pointer-events` CSS
  ou detecção de alfa no canvas)

---

## Teste de Aceitação

### Critérios

1. **Visual**: As 3 imagens montadas devem ser **pixel-perfect** idênticas à imagem original
2. **Interação**: Cada região deve ser clicável separadamente
3. **Hover**: Feedback visual claro ao passar o mouse em cada região
4. **Sem costuras**: Nenhuma linha, gap ou sobreposição visível entre as regiões
5. **Responsivo**: O cérebro deve redimensionar proporcionalmente

### Processo de teste

1. Abrir `http://localhost:5174` no browser
2. Navegar à página Painel (rota `/`)
3. Verificar visualmente que o cérebro está completo e idêntico à referência
4. Passar o mouse em cada região — deve iluminar só aquela parte
5. Clicar em cada região — deve abrir o painel de itens correspondente
6. Se houver qualquer defeito visual → ajustar coordenadas dos polígonos e re-gerar

---

## Arquivos Envolvidos

| Arquivo                                  | Ação                |
| ---------------------------------------- | ------------------- |
| `docs/image.png`                         | Fonte (não altera)  |
| `python-scripts/split_brain.py`          | Script de divisão   |
| `frontend/public/brain-top.png`          | Saída — região topo |
| `frontend/public/brain-bottom-left.png`  | Saída — inf-esq     |
| `frontend/public/brain-bottom-right.png` | Saída — inf-dir     |
| `frontend/public/brain-full.png`         | Referência completa |
| `frontend/src/components/BrainNav.vue`   | Componente Vue      |
| `frontend/src/views/PainelView.vue`      | Integração (pronto) |
