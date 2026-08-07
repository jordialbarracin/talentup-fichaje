# Changelog — TalentUP Fichaje

Todos los cambios notables del proyecto se documentan aqui.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased] — v1.0.0 (en desarrollo)

### Anadido
- JWT refresh tokens (7 dias) con endpoint `/api/auth/refresh`
- Rate limiting middleware (sliding window per IP+endpoint)
- DPA.md (Data Processing Agreement RGPD Art.28)
- Grafana monitoring (docker-compose + provisioning + dashboard)
- GitHub Actions CI/CD (test + coverage + firmware build)
- i18n frontend ES/CA/EN (177 strings traducibles)
- Firmware CYD 2432S028 completo (911 lineas): TFT_eSPI + PN532 I2C + OTA + WDT + offline queue (SPIFFS)
- 68 tests nuevos para 7 routers (tenants, contracts, schedules, overtime, payroll, notifications, calendar)
- OpenAPI/Swagger documentation con response models y tags grouping
- Landing page mejorada: SEO, JSON-LD, pricing, features, FAQ, responsive

### Cambiado
- PRIVACY.md actualizado (referencias Supabase/Vercel)
- README.md reescrito con documentacion profesional y API reference
- .gitignore: excluido .pio/ y archivos sensibles
- Auth: tokens ahora incluyen campo "type" (access/refresh)
- Login y register ahora devuelven refresh_token ademas de access_token

### Corregido
- Conflictos de merge resueltos en main.py y auth.py

## [0.9.0] — 2026-07-19

### Anadido
- Backend FastAPI con 16 routers
- 49 tests iniciales (auth, employees, clock, shifts, vacations, leave, holidays, reports, security, incidents)
- Frontend SPA (index.html 129KB)
- Landing page inicial
- Firmware ESP32 SPI (363 lineas)
- Docker compose con PostgreSQL
- PRIVACY.md inicial
- Multi-tenant, JWT auth, bcrypt, audit log