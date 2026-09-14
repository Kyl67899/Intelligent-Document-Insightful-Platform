# Intelligent Document Insightful Platform

Upload PDF documents, get AI-generated summaries, key insights, and a
topic category, then ask natural-language questions about them using
semantic search + an LLM.

- **Frontend:** Next.js (App Router), Tailwind CSS v4, shadcn-style UI
  primitives, Material UI (for the data table), Framer Motion
- **Backend:** Python, Flask, JWT + server-side session auth,
  PyMuPDF (OCR fallback via Tesseract), Chroma vector database,
  Anthropic Claude for summarization/insights/QA

---

## 1. Architecture overview

```
frontend (Next.js, :3000)
   │  REST (JSON + multipart), JWT bearer + session cookie
   ▼
backend (Flask, :5000)
   ├── auth/        signup, login, logout, refresh, me
   ├── documents/   upload → OCR → LLM analysis → vector index
   ├── qa/          semantic search → LLM answer
   └── services/
        ├── storage_service.py   local disk or S3
        ├── ocr_service.py       PyMuPDF text extraction + OCR fallback
        ├── llm_service.py       Claude: summary/insights/category, QA
        └── vector_service.py    Chroma embeddings + similarity search
```

**Document pipeline** (runs on upload):
1. File is saved (local `uploads/` folder by default, or S3).
2. Text is extracted per page with PyMuPDF; pages with little/no
   embedded text fall back to Tesseract OCR on a rendered page image.
3. The full extracted text is sent to Claude to generate a `<=200`
   word summary, 3-5 key insights, and a category label.
4. The text is chunked (overlapping word windows) and embedded via
   `sentence-transformers`, then stored in a per-document namespace in
   a local Chroma vector database.
5. The `Document` row is updated with status `ready` (or `failed` with
   an error message).

**Q&A pipeline**: the frontend sends a `document_id` + `question`; the
backend runs a similarity search scoped to that document in Chroma,
then asks Claude to answer using only the retrieved chunks as context.

> **Note on scaling:** for simplicity this demo runs the whole pipeline
> synchronously inside the upload request. For production, move
> `_process_document()` in `documents/routes.py` onto a background task
> queue (Celery/RQ + Redis) and have the frontend poll `GET
> /api/documents/:id` for status, which the UI already does.

---

## 2. Prerequisites

- Node.js 18+
- Python 3.11+
- (Optional, for scanned PDFs) [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
  installed on your system and on `PATH`
- An [Anthropic API key](https://console.anthropic.com/)

---

## 3. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# then edit .env and set at minimum:
#   SECRET_KEY, JWT_SECRET_KEY  -> any long random strings
#   ANTHROPIC_API_KEY           -> your Claude API key

python app.py
# Backend runs on http://localhost:5000
# SQLite DB (idip.db) and the uploads/ + chroma_db/ folders are
# created automatically on first run.
```

### Key environment variables (`backend/.env`)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` / `JWT_SECRET_KEY` | Flask session signing / JWT signing (use different random strings) |
| `DATABASE_URL` | SQLAlchemy URL; defaults to local SQLite, swap for Postgres in prod |
| `FRONTEND_ORIGIN` | Allowed CORS origin for the Next.js app |
| `STORAGE_BACKEND` | `local` (default) or `s3` |
| `ANTHROPIC_API_KEY` / `LLM_MODEL` | LLM used for analysis + QA |
| `CHROMA_PERSIST_DIR` / `EMBEDDING_MODEL` | Vector DB location + embedding model |

See `backend/.env.example` for the full list with defaults.

---

## 4. Frontend setup

```bash
cd frontend
npm install

cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:5000

npm run dev
# Frontend runs on http://localhost:3000
```

Because this project uses **Tailwind CSS v4**, theming is CSS-first —
all design tokens (colors, radius, font) live in `app/globals.css`
under an `@theme` block rather than a large `tailwind.config.js`.

---

## 5. Using the app

1. Go to `http://localhost:3000` → redirected to `/signup`.
2. Create an account (email + password, 8+ characters).
3. On the dashboard, drag & drop one or more PDF files and click
   **Upload & Analyze**. The table shows live status
   (`processing` → `ready`/`failed`) and polls automatically.
4. Expand a row to see the 3-5 key insights; the summary and category
   also appear inline.
5. Click the chat icon on a `ready` document to select it, then ask
   questions in the right-hand panel — answers are generated from
   semantically retrieved chunks of that specific document.

---

## 6. API reference

All endpoints are prefixed with `/api`. Protected endpoints require
`Authorization: Bearer <access_token>` **and** the session cookie set
at login (the frontend's `axios` client already sends both).

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/signup` | Create an account, returns user + access token |
| POST | `/api/auth/login` | Log in, returns user + access token |
| POST | `/api/auth/logout` | Clear the server-side session |
| POST | `/api/auth/refresh` | Issue a new access token from the session cookie |
| GET | `/api/auth/me` | Current authenticated user |
| POST | `/api/documents/upload` | Multipart upload, field `files` (one or more PDFs) |
| GET | `/api/documents` | List the current user's documents |
| GET | `/api/documents/:id` | Get one document |
| DELETE | `/api/documents/:id` | Delete a document + its vector data |
| POST | `/api/qa/ask` | `{ document_id, question }` → grounded answer |
| GET | `/api/health` | Health check |

---

## 7. Project structure

```
.
├── backend/
│   ├── app.py                 # Flask app factory / entrypoint
│   ├── config.py               # env-driven configuration
│   ├── extensions.py           # db, bcrypt, cors, session singletons
│   ├── models.py                # User, Document SQLAlchemy models
│   ├── auth/routes.py           # signup/login/logout/refresh/me
│   ├── documents/routes.py      # upload + analysis pipeline
│   ├── qa/routes.py             # semantic search + QA
│   ├── services/
│   │   ├── ocr_service.py       # PyMuPDF text extraction + OCR fallback
│   │   ├── llm_service.py       # Claude summary/insights + QA answers
│   │   ├── vector_service.py    # Chroma embeddings + search
│   │   └── storage_service.py   # local / S3 file storage
│   ├── utils/decorators.py      # JWT auth decorator
│   └── requirements.txt / .env.example
└── frontend/
    ├── app/
    │   ├── layout.tsx, globals.css
    │   ├── page.tsx              # redirects based on auth state
    │   ├── login/, signup/       # AuthForm-based pages
    │   └── dashboard/page.tsx    # upload + table + QA layout
    ├── components/
    │   ├── ui/                   # shadcn-style button/input/label/card
    │   ├── AuthForm.tsx
    │   ├── DocumentUpload.tsx
    │   ├── DocumentTable.tsx     # MUI table with expandable insights
    │   ├── QAPanel.tsx
    │   └── ProtectedRoute.tsx
    ├── providers/
    │   ├── AuthProvider.tsx      # JWT state + auto-refresh
    │   └── MuiThemeProvider.tsx
    ├── lib/{api.ts, utils.ts}
    └── package.json / tailwind.config.ts / .env.local.example
```

---

## 8. Security notes

- Passwords are hashed with bcrypt, never stored in plaintext.
- Access tokens are short-lived JWTs; a separate HttpOnly session
  cookie backs silent refresh and immediate revocation on logout.
- Set `SESSION_COOKIE_SECURE=True` and serve both apps over HTTPS in
  production.
- Rotate `SECRET_KEY` / `JWT_SECRET_KEY` between environments and
  never commit `.env` files (already covered by `.gitignore`).
