# TalentUP Fichaje — Plan de Imagen y Marketing

> Elaborado con: `frontend-design`, `design-critique`, `design-system`, `brand-review`, `marketing-plan` (AARRR), `popular-web-designs` (Apple HIG), y GitHub API search.

---

## 1. Diagnóstico Honesto — Qué Está Mal Ahora

### 1.1 Problemas críticos de diseño

| # | Problema | Por qué es grave | Causa |
|---|---|---|---|
| 1 | **Emojis en navegación** (📊 👥 📅 ⏰ 📋 🏖️ 🩺 📈 ⚙️) | Apple NO usa emojis. Usa SF Symbols: iconos vectoriales monocromos de 1px stroke. Los emojis gritan "hecho con IA" | Subagent los añadió como atajo |
| 2 | **Dark mode en todo** | Apple alterna light/dark. El dashboard de gestión es LIGHT (#f5f5f7), no black. El black es para hero inmersivo, no para tablas de datos | Me fui a lo fácil con Linear en vez de leer el template Apple |
| 3 | **Bordes en cards** | Apple casi nunca usa borders. Elevación = shadow suave + contraste de fondo | Linear me llevó a rgba borders |
| 4 | **Tipografía genérica** | Apple usa SF Pro con optical sizing, negative tracking universal (-0.022em), weight 600 en headlines. Nosotros heredamos system-ui sin intención | Falta de aplicación del template |
| 5 | **Naranja saturado** | #FF6B35 al full es agresivo. Apple usa un solo accent MUTED. El naranja debe usarse con restraint extremo | Marca sin calibrar |
| 6 | **Sin iconos reales** | Los SVGs del nav son genéricos. Apple usa SF Symbols con peso visual consistente | Falta sistema de iconos |

### 1.2 Veredicto design-critique

| Dimensión | Score | Nota |
|---|---|---|
| First impression | 3/10 | Parece un dashboard de IA genérico, no un producto premium |
| Usability | 6/10 | Funciona, pero la navegación con emojis confunde |
| Visual hierarchy | 4/10 | Los emojis compiten con el texto. Sin orden de lectura claro |
| Consistency | 5/10 | Inconsistente: dark mode + naranja saturado + emojis + borders |
| Accessibility | 6/10 | Contraste OK en dark, pero en light fallaría |

**Score total: 24/50 — Insuficiente para un producto comercial**

---

## 2. Design System — Apple HIG + TalentUP Brand

### 2.1 Filosofía: "Clarity Hospitality"

Apple HIG dice: **Clarity, Deference, Depth**. Para TalentUP:

- **Clarity**: cada pantalla tiene un job. El dashboard muestra datos, no decora.
- **Deference**: la UI se retira. El contenido (empleados, fichajes, turnos) es el héroe.
- **Depth**: jerarquía visual con shadow suave y contraste de fondo, NO con borders.

### 2.2 Color System — Light mode (Apple real)

| Token | Valor | Uso |
|---|---|---|
| `--bg-primary` | `#ffffff` | Dashboard, tablas, forms |
| `--bg-secondary` | `#f5f5f7` | Secciones alternas, sidebar |
| `--bg-tertiary` | `#fafafa` | Hover states, inputs |
| `--surface` | `#ffffff` | Cards |
| `--surface-elevated` | `#ffffff` + shadow | Modals, dropdowns |
| `--text-primary` | `#1d1d1f` | Texto principal (Apple near-black) |
| `--text-secondary` | `rgba(0,0,0,0.6)` | Texto secundario |
| `--text-tertiary` | `rgba(0,0,0,0.3)` | Placeholders, muted |
| `--accent` | `#FF6B35` | SOLO CTAs, links, estados activos |
| `--accent-hover` | `#E55A2B` | Hover (más oscuro, no más claro) |
| `--accent-bg` | `rgba(255,107,53,0.08)` | Fondo de accent (active states) |
| `--success` | `#34C759` | Apple system green |
| `--warning` | `#FF9500` | Apple system orange |
| `--error` | `#FF3B30` | Apple system red |
| `--info` | `#007AFF` | Apple system blue |
| `--border` | `rgba(0,0,0,0.08)` | Dividers sutiles (raro) |
| `--shadow-card` | `0 3px 5px 30px rgba(0,0,0,0.22)` | Apple card shadow |
| `--shadow-modal` | `0 8px 32px rgba(0,0,0,0.3)` | Modals |

**Regla crítica: el naranja se gana.** Aparece SOLO en:
- Botón primary (1 por pantalla)
- Link activo en sidebar
- Estados de focus
- Badge de alerta
Nunca como decoración, nunca en fondos, nunca en gradientes.

### 2.3 Tipografía — SF Pro / system-ui

| Rol | Size | Weight | Tracking | Line-height |
|---|---|---|---|---|
| Display (login) | 48px | 600 | -0.028em | 1.07 |
| H1 (page title) | 32px | 600 | -0.022em | 1.10 |
| H2 (section) | 24px | 600 | -0.018em | 1.20 |
| H3 (card title) | 17px | 600 | -0.022em | 1.24 |
| Body | 17px | 400 | -0.022em | 1.47 |
| Body small | 15px | 400 | -0.016em | 1.47 |
| Caption | 13px | 400 | -0.008em | 1.43 |
| Label (uppercase) | 12px | 600 | 0.06em | 1.33 |
| Mono (datos) | 14px | 500 | 0 | 1.43 |

**Font stack:** `font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;`

### 2.4 Iconos — SF Symbols style

**CERO emojis.** Los iconos son SVG inline con estas reglas:
- Stroke 1.5px (no 2px, no fill)
- Color: `currentColor` (hereda del texto)
- Size: 20x20px en nav, 16x16px inline
- Estilo: outline/line (no filled/solid)

Sistema de iconos para las 9 secciones:
| Sección | Icono SVG (descripción) |
|---|---|
| Dashboard | Grid 2x2, lines only |
| Empleados | Person silhouette, single line |
| Calendario | Calendar, 2 lines top |
| Turnos | Clock, hands at 10:10 |
| Fichajes | Fingerprint, single contour |
| Vacaciones | Sun, 8 rays |
| Bajas | Medical cross, outline |
| Informes | Document with fold |
| Configuración | Gear, 6 teeth |

### 2.5 Componentes — sin borders, shadow Apple

| Componente | Reglas |
|---|---|
| **Card** | `background:#fff`, `border:none`, `border-radius:12px`, `shadow-card` |
| **Button primary** | `background:#FF6B35`, `color:#fff`, `radius:980px` (pill), `padding:8px 16px` |
| **Button secondary** | `background:transparent`, `border:1px solid #FF6B35`, `color:#FF6B35`, `radius:980px` |
| **Button ghost** | `background:transparent`, `color:rgba(0,0,0,0.6)`, `radius:980px` |
| **Input** | `background:#f5f5f7`, `border:none`, `radius:8px`, `padding:12px 16px` |
| **Modal** | `background:#fff`, `border:none`, `radius:12px`, `shadow-modal` |
| **Table** | `background:#fff`, sin borders entre rows, solo `border-bottom:1px solid rgba(0,0,0,0.04)` |
| **Badge** | `radius:4px` (NO pill), `font-size:11px`, `font-weight:600`, `text-transform:uppercase` |

### 2.6 Layout

- Sidebar: 240px, `background:#f5f5f7`, sin glass (Apple sidebar es opaco light)
- Navbar: `background:rgba(255,255,255,0.72)`, `backdrop-filter:saturate(180%) blur(20px)` (glass light)
- Content: `background:#ffffff`, `padding:32px`
- Max width: 1200px

---

## 3. Brand Voice — Cómo Habla TalentUP

### 3.1 Personalidad

> TalentUP es el gerente experimentado que lleva 20 años en hostelería. Habla claro, sin tecnicismos, entiende tu día a día. No te vende nada — te lo enseña.

### 3.2 Atributos de voz

| Atributo | Somos | NO somos |
|---|---|---|
| **Directo** | "Carlos no fichó el martes" | "Se detectó una incidencia de ausencia" |
| **Profesional** | "Nómina de julio lista para revisión" | "¡Tu nómina está súper lista! 🎉" |
| **Concreto** | "3 empleados en baja, 2 vacaciones" | "Tenemos algunas ausencias en el equipo" |
| **Cálido** | "¿Necesitas ayuda? Estamos aquí" | "Para asistencia técnica contacte con soporte" |

### 3.3 Terminología

| Usar | No usar | Por qué |
|---|---|---|
| Fichar | Registrar asistencia | Es el término del sector |
| Empleado | Trabajador/colaborador | RD-ley usa "empleado" |
| Turno | Horario laboral | "Turno" es hostelería |
| Baja | Incapacidad temporal | "Baja" es universal |
| Convenio | Acuerdo colectivo | "Convenio" es el término legal |
| Nómina | Recibo salarial | "Nómina" es el estándar |
| Parte | Parte de baja/trabajo | Documento oficial |

### 3.4 Reglas de estilo

- Sentence case en títulos (NO Title Case): "Empleados activos" no "Empleados Activos"
- Sin emojis en UI. Nunca. Para nada.
- Sin signos de exclamación dobles (¡!)
- Números siempre en dígitos: "10 empleados" no "diez empleados"
- Fechas: "18 jul 2026" (corto) o "18 de julio de 2026" (formal)
- Horas: 24h ("14:32" no "2:32 PM")

---

## 4. Plan de Marketing — AARRR

### 4.1 Posicionamiento

**Categoría:** Fichaje digital para hostelería
**ICP:** Restaurante/Bar con 10-50 empleados, 1-5 establecimientos, dueño-gerente que hace nóminas a mano
**Claim:** "El fichaje que entiende la hostelería. NFC, offline, y nómina sin Excel."

### 4.2 AARRR

#### Acquisition (extraños → aware)

| Canal | Acción | Coste | Timeline |
|---|---|---|---|
| SEO | Programmatic SEO: "fichaje digital + [ciudad]" | €0 | 90 días |
| Google My Business | Ficha optimizada por ciudad | €0 | 30 días |
| Cold email | 50 restaurantes/día en zona | €0 | 90 días |
| LinkedIn | 3 posts/semana sobre RRHH hostelería | €0 | 90 días |
| Producto Hunt | Launch day | €0 | 90 días |

#### Activation (aware → primera experiencia)

| Paso | Acción | Métrica |
|---|---|---|
| Landing | Hero: "Ficha en 2 segundos. Sin app, sin tablet" | Conversion rate >3% |
| Signup | Email + nombre del restaurante. Sin tarjeta | Signup completion >60% |
| Onboarding | Setup wizard: añade 1 empleado, 1 turno, 1 fichaje | Time-to-value <5min |
| Aha moment | Empleado ficha con PIN y ve confirmación | First clock-in rate >80% |

#### Retention (usuario convertido → repite)

| Mecanismo | Acción |
|---|---|
| Daily habit | Fichar es diario. El gestor abre el dashboard para ver quién fichó |
| Notificaciones | "Carlos no fichó su turno de mañana" a las 10:00 |
| Informe semanal | "Resumen: 5 fichajes, 2 incidencias, 1 baja" por email |
| Nómina mensual | "Nómina de julio lista" — momento de mayor valor |

#### Referral (usuarios → traen más)

| Mecanismo | Acción |
|---|---|
| Referido | 1 mes gratis por restaurante referido |
| WhatsApp | "Comparte con otro restaurante" button en dashboard |
| Caso de éxito | Primer cliente → caso de éxito → landing page |

#### Revenue (monetización)

| Plan | Precio | Incluye |
|---|---|---|
| Básico | 29€/mes/restaurante | Hasta 15 empleados, fichaje, informes básicos |
| Pro | 39€/mes/restaurante | Hasta 50 empleados, nóminas, vacaciones, bajas |
| Multi | Personalizado | Multi-restaurante, API, soporte dedicado |

**Pricing model:** por establecimiento, no por usuario. Sin límite de empleados en cada plan (solo bandwidth).

### 4.3 90-day roadmap

| Semanas | Focus | Entregable |
|---|---|---|
| 1-2 | Unblock | Rediseño light mode Apple, sin emojis, SF Symbols |
| 3-4 | Foundation | Landing page, SEO setup, Google My Business |
| 5-8 | Velocity | Cold email 50/día, LinkedIn 3/sem, contenido SEO |
| 9-12 | Compound | ProductHunt launch, 10 restaurantes piloto, feedback loop |

---

## 5. Ejecución — Qué Hago Ahora

### Fase 1: Rediseño (esta sesión)

1. **Cambiar dark mode → light mode** (Apple #f5f5f7)
2. **Eliminar TODOS los emojis** del nav y reemplazar con SVG SF Symbols style
3. **Recalibrar naranja** — menos saturado, más restraint
4. **Sin borders en cards** — solo shadow Apple
5. **Tipografía SF Pro** con tracking correcto
6. **Pill CTAs** 980px radius
7. **Glass light en navbar** (saturate + blur)

### Fase 2: Landing page (próxima sesión)

1. Hero: "El fichaje que entiende la hostelería"
2. 3 features: NFC, offline, nómina
3. Pricing: 29€/39€
4. CTA: "Empezar gratis"

### Fase 3: Marketing (próximas sesiones)

1. SEO programmatic
2. Cold email
3. LinkedIn content
4. ProductHunt launch