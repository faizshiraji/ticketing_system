# CCL/CCDL Support frontend

Vue 3 + Vite + TypeScript SPA for the ticketing API.

## Develop

```bash
# from repo root — Django must be running on :8000
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173/

## Build

```bash
npm run build
```

## Env

`VITE_API_BASE_URL` defaults to `http://127.0.0.1:8000`. Backend `.env` must allow the Vite origin in `CORS_ALLOWED_ORIGINS`.
