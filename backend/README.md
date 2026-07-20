# TalentUP Fichaje — Backend

Backend FastAPI multi-tenant del SaaS de fichaje digital para hostelería.

## Desarrollo local

```bash
# Activar entorno
source venv/Scripts/activate

# Variables de entorno (opcional, por defecto usa SQLite)
export DATABASE_URL="sqlite+aiosqlite:///./talentup_fichaje.db"
export SECRET_KEY="dev-secret"

# Arrancar
uvicorn app.main:app --reload
```

## Tests

```bash
pytest
```

## Migraciones

```bash
# SQLite dev: tablas creadas automáticamente.
# PostgreSQL prod:
alembic upgrade head
```

## Deploy automático a Railway

El repositorio incluye `.github/workflows/deploy-backend.yml` para hacer deploy
automático a Railway en cada push a `main` o `master` que toque el backend.

### Requisitos

1. Crea un proyecto en [Railway](https://railway.app/) y vincúlalo a este repositorio.
2. Genera un token de acceso en Railway (`Account → API Tokens`).
3. En GitHub, ve a **Settings → Secrets and variables → Actions** y añade:
   - `RAILWAY_TOKEN`: el token generado en Railway.
4. Ajusta el nombre del servicio en el workflow si es necesario:
   ```yaml
   railway up --service=<TU_SERVICIO> --detach
   ```

Con esto, cada push a `main` desplegará el backend automáticamente.

## Variables de entorno importantes

- `DATABASE_URL`: URL de la base de datos (obligatoria en producción).
- `REDIS_URL`: URL de Redis para rate limiting distribuido (opcional en dev).
- `SECRET_KEY`: clave para firmar JWT.
- `RAILWAY_TOKEN`: token usado por el workflow de GitHub Actions.

## Licencia

Propiedad de TalentUP.
