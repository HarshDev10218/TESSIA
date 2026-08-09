# TESSIA — Personal AI Assistant, Research Partner & Adaptive Guide

TESSIA is a local-first personal assistant, research assistant, teacher, knowledge graph guide, and voice companion designed to make the user more capable, not more dependent.

---

## 1. Architecture Overview
tessia/
├── agent/
│   ├── main.py        # HTTP Server, API routes (/api/graph, /api/chat, /api/speak, /api/listen)
│   ├── vault.py       # Knowledge graph indexing, degree hub ranking & Wikilinks parser
│   ├── tools.py       # Safe tool execution dispatcher (search_brain, remember, etc.)
│   ├── data.py        # Isolated file reader (Strictly READ-ONLY user folder access)
│   ├── voice.py       # ElevenLabs TTS & Scribe STT integrations (Python stdlib)
│   ├── memory.py      # Isolated memory persistence layer (Writes strictly to memory/)
│   ├── researcher.py  # Structured research engine with source attribution
│   ├── teacher.py     # Adaptive learning, level tracking, and Socratic teaching
│   └── prompt.md      # TESSIA system instructions and guardrails
│
├── ui/
│   ├── index.html     # Responsive 3-panel UI layout
│   ├── app.js         # Frontend controller, state machine & audio handler
│   ├── graph.js       # HTML5 Canvas force-directed graph renderer with label collision avoidance
│   └── styles.css     # Dark obsidian neural aesthetic styling
│
├── data/
│   ├── demo/          # Deterministic test dataset
│   └── generate_demo.py
│
├── memory/            # User-approved facts stored as dated Markdown files
├── TESSIA.md          # User profile and assistant configuration
├── .env               # Private environment variables (API keys)
├── .gitignore
└── README.md
---

## 2. Requirements & Setup

### Requirements
- **Python 3.8+** (Standard library only; **no** pip packages, no npm, no node, no React).
- Modern web browser (Chrome, Edge, Firefox, or Safari).

### Setup
1. Clone or place the `tessia` repository in your project directory.
2. Create `.env` in the root folder:
   ```env
   ELEVENLABS_API_KEY=your_actual_elevenlabs_key
   TESSIA_DEMO=1
   TESSIA_FOLDERS=/path/to/your/notes