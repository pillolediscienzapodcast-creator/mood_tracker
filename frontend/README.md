# Frontend — Startup Template

SPA in **Vue 3 + TypeScript** con Vite, Pinia e Vue Router. Node.js **22 LTS**.

## Setup

```bash
npm install
```

## Sviluppo

```bash
npm run dev        # http://localhost:5173
```

In sviluppo le chiamate a `/api` vengono inoltrate al backend tramite il proxy di
Vite (vedi `vite.config.ts`), evitando problemi di CORS. Il target è configurabile
con la variabile d'ambiente `VITE_PROXY_TARGET` (in Docker vale `http://backend:8000`).

## Build e anteprima

```bash
npm run build      # type-check (vue-tsc) + build di produzione
npm run preview    # anteprima della build
npm run type-check # solo controllo dei tipi
```

## Configurazione

L'URL base delle API si imposta con `VITE_API_BASE_URL` (default `/api/v1`).
Copia il template e adatta i valori:

```bash
cp .env.example .env
```

## Struttura

```
src/
├── router/      # rotte (lazy-loaded)
├── stores/      # store Pinia (es. stato del backend)
├── services/    # client API riutilizzabile
├── views/       # pagine
├── components/  # componenti condivisi
└── assets/      # stili
```
