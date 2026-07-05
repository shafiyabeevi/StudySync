#  StudySync

**An AI-powered study and exam preparation portal.**
Upload your notes, get exam-ready summaries, ask doubts in plain English (or Tamil), teach concepts back to the AI, and track exactly where you're strong and where you're guessing.

---

##  Features

### Core
- **Document Upload** — Upload PDF or DOCX study material (up to 20MB). Text is automatically extracted, chunked, and indexed for search.
- **AI Exam Notes** — Automatically generates a "teacher-style" summary of each document: key points, definitions, and formulas, structured for quick exam revision.
- **Doubt-Solving Chatbot** — Ask questions about your uploaded document in English. Ask for an explanation in Tamil (or another language) and it answers specifically in that language.
- **Find Books — Reference Finder** — Search any topic (e.g. "computer networks") and get real reference books/articles from the web with working links.
- **Delete Documents** — A simple three-dot menu on each document card lets you delete documents you no longer need, with a confirmation step to prevent accidental removal.

### Novelty Features
- **Teach-It-Back Mode** — Flips the usual AI role. Explain a topic back to the AI in your own words (typed or voice), and get gentle, structured feedback: what you got right, what you missed, and a model answer — based on the Feynman Technique.
- **Confidence Calibration Meter** — Before revealing if a quiz/Teach-It-Back answer is correct, rate how confident you were. Over time, StudySync shows where your confidence and real performance don't match — surfacing topics you *think* you know but don't.
- **Crowd Confusion Heatmap** — On shared documents, tracks which paragraphs generate the most doubt-questions across students and highlights them for everyone, turning individual confusion into a collective signal.
- **Feedback Loop** — A quick 👍/👎 on every AI-generated output (chat answers, exam notes, quiz questions, Teach-It-Back grading) to track what's working and what needs improvement.

---

##  Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React (Vite) + Tailwind CSS | Fast, responsive UI |
| Backend | Python (FastAPI) | API server, async request handling |
| Database & Storage | Supabase (PostgreSQL) | Users, documents, results, file storage |
| Vector Search | ChromaDB | Semantic search over document content (RAG) |
| AI Models | Google Gemini / Groq (Llama) | Notes generation, chatbot, grading |
| Web Search | Tavily API | Reference book/article discovery |

---

## Project Structure

```
SiteCraft/
├── frontend/                 # React + Vite + Tailwind app
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── ...
│   └── package.json
├── backend/                  # FastAPI app
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py         # DB models / schemas
│   │   ├── local_db.py       # DB connection helpers
│   │   ├── routes/
│   │   │   ├── documents.py
│   │   │   ├── chat.py
│   │   │   ├── teach_it_back.py
│   │   │   ├── confidence.py
│   │   │   ├── heatmap.py
│   │   │   └── feedback.py
│   │   └── ai/                # LLM prompt templates & clients
│   └── requirements.txt
├── .env.example
└── README.md
```

*(Structure may vary slightly depending on how the project was scaffolded — update this section to match your actual folders.)*

---

## 🚀 Getting Started

### Prerequisites
- [Node.js](https://nodejs.org/) (LTS)
- [Python 3.10+](https://www.python.org/)
- A [Supabase](https://supabase.com/) project (free tier)
- Free API keys from:
  - [Google AI Studio](https://aistudio.google.com/) (Gemini)
  - [Groq Console](https://console.groq.com/) (Llama models)
  - [Tavily](https://tavily.com/) (web search)

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/studysync.git
cd studysync
```

### 2. Configure environment variables
Copy the example file and fill in your keys:
```bash
cp .env.example .env
```
```env
GEMINI_API_KEY=
GROQ_API_KEY=
TAVILY_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

### 3. Set up the backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Backend runs at `http://localhost:8000` by default.

### 4. Set up the frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173` by default (or similar Vite port).

---

## How It Works (High Level)

1. **Upload** → document is parsed, chunked, and embedded into ChromaDB.
2. **Exam Notes** → an LLM reads the chunks and generates a structured, teacher-style summary, cached for fast reloads.
3. **Chatbot** → retrieves relevant chunks (RAG) for a question, answers in the language requested.
4. **Teach-It-Back** → student's explanation + original source chunks are sent to the LLM for structured, encouraging feedback.
5. **Confidence Calibration** → confidence ratings are logged alongside correctness/scores and compared over time per topic.
6. **Heatmap** → doubt-question chunk references are counted per document and rendered as highlight intensity.
7. **Find Books** → a topic query is sent to the Tavily API, filtered and returned as a clean list of links.

---

##  Roadmap
- [ ] Full authentication (Supabase Auth) for multi-user support
- [ ] Flashcards & quiz generation from exam notes
- [ ] Progress tracking dashboard
- [ ] Audio/podcast-style exam notes (text-to-speech)
- [ ] Teacher/admin dashboard for feedback and heatmap analytics

---

##  Contributing
This is currently a solo/academic project. Suggestions and issues are welcome via GitHub Issues.

## 📄 License
Specify your license here (e.g., MIT) — add a `LICENSE` file to the repo root.
