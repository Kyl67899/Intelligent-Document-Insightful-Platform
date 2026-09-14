<div align="center">

# 📄 Intelligent Document Insightful Platform

**Turn stacks of PDFs into searchable knowledge — instantly summarized, tagged, and ready for Q&A.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#-license)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)](#-tech-stack)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?logo=flask)](#-tech-stack)
[![Claude](https://img.shields.io/badge/LLM-Claude-6b5bff)](#-tech-stack)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#-contributing)

[Problem](#-the-problem) • [Solution](#-the-solution) • [Tech Stack](#-tech-stack) • [Demo](#-demo) • [Getting Started](#-getting-started) • [Usage](#-how-to-use) • [Contributing](#-contributing) • [Roadmap](#-roadmap--future-features)

</div>

---

## 🧩 The Problem

Knowledge workers, researchers, legal teams, and analysts routinely deal with **piles of unstructured PDF documents** — contracts, reports, research papers, policy documents — and:

- **Reading every page is slow.** Extracting the key point of a 40-page report can take longer than the meeting it's needed for.
- **Important details get buried.** Critical clauses, risks, or findings are easy to miss when skimming.
- **Finding answers means re-reading.** "What does this contract say about termination?" usually means `Ctrl+F` and hoping the right keyword was used.
- **Context switching kills productivity.** Manually summarizing, tagging, and organizing documents pulls focus away from actual decision-making.

There's no lightweight, self-hostable tool that lets you **upload a document and immediately get a summary, key insights, and the ability to ask it questions** — without wiring together five different SaaS tools.

## 💡 The Solution

**Intelligent Document Insightful Platform (IDIP)** is a full-stack web app that turns any PDF into structured, queryable knowledge in seconds:

1. **Upload** one or more PDFs through a clean, drag-and-drop dashboard.
2. The platform **extracts text** (with OCR fallback for scanned documents), then sends it to an LLM to generate:
   - A concise summary (≤200 words)
   - 3–5 key insights
   - An automatic topic/category label
3. The document is **embedded into a vector database**, enabling semantic search.
4. You can then **ask natural-language questions** about any processed document and get answers grounded in its actual content — not hallucinated guesses.

All of this sits behind secure, per-user authentication, so every account only ever sees its own documents.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend framework** | [Next.js](https://nextjs.org/) (App Router, React 18) |
| **Styling** | [Tailwind CSS v4](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/)-style primitives |
| **UI components** | [Material UI](https://mui.com/) (data-dense table/interactions) |
| **Animation** | [Framer Motion](https://www.framer.com/motion/) |
| **Backend framework** | [Flask](https://flask.palletsprojects.com/) (Python) |
| **Auth** | JWT access tokens + server-side sessions, bcrypt password hashing |
| **Database (relational)** | SQLAlchemy ORM — SQLite (dev) / PostgreSQL-ready (prod) |
| **Document parsing** | [PyMuPDF](https://pymupdf.readthedocs.io/) + Tesseract OCR fallback |
| **Vector database** | [Chroma](https://www.trychroma.com/) (persisted locally) |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| **LLM** | [Anthropic Claude](https://www.anthropic.com/) — summarization, insight extraction, QA |
| **File storage** | Local disk (default) or S3-compatible cloud storage |

---

## 🎬 Demo

> _Screenshots/GIF coming soon — contributions welcome! See [Contributing](#-contributing)._

<div align="center">

| Login | Dashboard | Q&A |
|---|---|---|
| ![login placeholder](docs/screenshots/login.png) | ![dashboard placeholder](docs/screenshots/dashboard.png) | ![qa placeholder](docs/screenshots/qa.png) |

</div>

**Typical flow:**

1. Sign up / log in →
2. Drag a PDF into the upload zone →
3. Watch the status go `processing → ready` as the table fills in with a summary, category, and key insights →
4. Click the chat icon on a ready document →
5. Ask a question and get an answer sourced from that document's content.

> 🎥 Want to add a live demo link or recording here? Open a PR — see [Contributing](#-contributing).

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)
- (Optional, for scanned PDFs) [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on your `PATH`

### 1. Clone the repo

```bash
git clone https://github.com/Kyl67899/Intelligent-Document-Insightful-Platform.git
cd Intelligent-Document-Insightful-Platform
```

### 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env            # then set SECRET_KEY, JWT_SECRET_KEY, ANTHROPIC_API_KEY

python app.py                   # runs on http://localhost:5000
```

### 3. Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:5000

npm run dev                        # runs on http://localhost:3000
```

Full environment variable reference and architecture details live in [`SETUP.md`](./SETUP.md).

---

## 📖 How to Use

1. **Create an account** — sign up with an email and password (8+ characters). You're logged in immediately via a JWT + secure session.
2. **Upload documents** — drag and drop one or more PDFs onto the upload zone, or click to browse. Multiple files can be uploaded at once.
3. **Watch processing happen** — each document's status moves from `processing` to `ready` (or `failed`, with an error message) automatically; the table polls in the background so you don't need to refresh.
4. **Review the analysis** — every ready document shows its filename, upload date, auto-detected category, and AI summary. Click the expand arrow on a row to see its 3–5 key insights.
5. **Ask questions** — click the chat icon on any `ready` document to select it, then type a question in the panel on the right (e.g. *"What are the payment terms?"*). The answer is generated from content retrieved specifically from that document via semantic search — not the model's general knowledge.
6. **Manage your library** — delete documents you no longer need; this also removes their vector embeddings.

---

## 🤝 Contributing

Contributions of all sizes are welcome — bug fixes, new features, documentation, tests, or demo assets.

### How to contribute

1. **Fork** the repository and create your branch from `main`:

   ```bash
   git checkout -b feature/short-description
   ```

2. **Make your changes.** Please:
   - Keep backend changes documented with clear docstrings/comments (see existing `services/` modules for the expected style).
   - Match the existing frontend patterns (Tailwind utility classes + shadcn-style components + MUI only where it's already used).
   - Add or update tests where applicable.
3. **Run checks locally** before opening a PR:

   ```bash
   # backend
   cd backend && python -m py_compile app.py config.py models.py

   # frontend
   cd frontend && npm run lint
   ```

4. **Commit using clear messages** (Conventional Commits encouraged, e.g. `feat: add PDF page thumbnails`, `fix: handle empty OCR text`).
5. **Open a Pull Request** against `main`, describing:
   - What problem it solves / what it adds
   - How you tested it
   - Screenshots for UI changes

### Good first issues

Look for issues tagged [`good first issue`](../../labels/good%20first%20issue) or [`help wanted`](../../labels/help%20wanted). Ideas that are always welcome:

- Adding real demo screenshots/GIFs to `docs/screenshots/`
- Writing unit/integration tests (backend `pytest`, frontend component tests)
- Improving error messages and edge-case handling
- Accessibility improvements to the dashboard

### Code of Conduct

Be respectful, constructive, and patient — this is a community project and everyone was a beginner once. Harassment or discrimination of any kind will not be tolerated.

### Reporting bugs / requesting features

Please open an issue with:

- A clear title and description
- Steps to reproduce (for bugs) or the use case (for features)
- Environment details (OS, Node/Python versions) when relevant

---

## 🗺 Roadmap / Future Features

- [ ] **Background job queue** (Celery/RQ + Redis) so uploads process asynchronously instead of blocking the request — critical for large PDFs or bulk uploads
- [ ] **Multi-document / cross-document Q&A** — ask a question and get answers synthesized across your entire library, not just one file
- [ ] **Support for more file types** — Word docs, PowerPoint, plain text, and web URLs
- [ ] **Team workspaces & sharing** — invite collaborators, share documents and Q&A threads with role-based permissions
- [ ] **Highlighted source citations** — click an answer and jump to the exact page/passage it came from
- [ ] **Document comparison** — diff two versions of a contract or report and summarize what changed
- [ ] **Export & reporting** — export summaries/insights to PDF, Markdown, or Notion
- [ ] **Custom analysis templates** — let users define their own extraction schema (e.g. "always extract parties, dates, and dollar amounts" for contracts)
- [ ] **Usage analytics dashboard** — track documents processed, most-asked questions, and token/cost usage
- [ ] **Alternative LLM/embedding providers** — pluggable support for OpenAI, local models (Ollama), and other embedding backends
- [ ] **Mobile-responsive redesign & PWA support**
- [ ] **Automated test suite + CI pipeline** (GitHub Actions)

Have an idea not listed here? [Open a feature request](../../issues/new)!

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).

## 🙏 Acknowledgments

Built with [Next.js](https://nextjs.org/), [Flask](https://flask.palletsprojects.com/), [Anthropic Claude](https://www.anthropic.com/), [Chroma](https://www.trychroma.com/), [PyMuPDF](https://pymupdf.readthedocs.io/), [shadcn/ui](https://ui.shadcn.com/), and [Material UI](https://mui.com/).
