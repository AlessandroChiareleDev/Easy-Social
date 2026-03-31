# Design Reference Request — Easy e-Social Login & Internal Pages

## Context

I'm building **Easy e-Social**, an internal enterprise tool for managing eSocial (Brazilian government payroll compliance system). The app handles:

- User authentication with company selection (multi-tenant)
- Data validation workflows (comparing spreadsheet data against government tables)
- Automation bot control panel

**Tech stack**: Vue 3 + TypeScript + Tailwind CSS 4 + Vite  
**Current state**: Backend is complete. Need frontend design direction.

---

## Questions for Design AI

### 1. Login Page Design

I need a **login page** for an internal B2B SaaS tool (not consumer-facing). Requirements:

- Email + password fields
- "Entrar" (Login) button
- Error message display
- Brand: "Easy e-Social" — professional, modern, trustworthy
- Color palette suggestion that conveys: reliability, technology, compliance/legal feel
- Should it have a sidebar illustration + form layout (split screen), or a centered card layout?
- What background treatment works best for a business tool? (gradient, pattern, solid, image?)
- Should I use glassmorphism, neumorphism, or flat/material style?
- Give me specific CSS values: border-radius, shadows, spacing, font-sizes
- Dark theme or light theme for a tool used during work hours?

### 2. Company Selection Page (Post-Login)

After login, the user sees a list of companies they have access to and picks one. Questions:

- Card grid vs list layout for 1-20 companies?
- What information to show per card? (name, CNPJ, role, icon)
- How to handle single-company users (auto-redirect or still show selection)?
- Animation/transition from login → company selection?

### 3. Main App Layout (Internal Pages)

Once inside a company, the user navigates between:

- **Painel** (Dashboard with upload stats)
- **Tabelas** (Data table viewer)
- **Validador de Naturezas** (Validation workflow with suggestion cards)
- **Robô eSocial** (Bot control panel)

Questions:

- **Navigation**: Top navbar, left sidebar, or combination?
- How to show the selected company name + switch option?
- User avatar/menu position?
- Consistent card/panel styling for all internal pages?
- Recommended spacing system (4px, 8px, 16px grid)?
- Typography scale for headings, body, labels, badges?

### 4. Component Design Tokens

Please provide specific design tokens I should use across the app:

- Primary color (and shades: 50-900)
- Secondary/accent color
- Success, warning, error, info colors
- Neutral/gray scale
- Border radius values (small, medium, large)
- Shadow levels (sm, md, lg, xl)
- Font stack recommendation
- Animation duration standards (fast, normal, slow)

### 5. Responsive Considerations

- The app will primarily be used on desktop (1920x1080, 1440x900)
- Should it be fully responsive or desktop-optimized?
- Minimum supported width?

---

## What I Want Back

1. **Color palette** with hex codes
2. **Layout recommendation** for login, company selector, and main app
3. **Component styling guide** (buttons, inputs, cards, badges, tables)
4. **Specific CSS/Tailwind values** I can implement directly
5. **One or two reference screenshots/examples** of similar enterprise tools for inspiration (Notion, Linear, Vercel Dashboard, etc.)

---

## Brand Keywords

Professional, modern, clean, trustworthy, efficient, Brazilian enterprise compliance tool.
