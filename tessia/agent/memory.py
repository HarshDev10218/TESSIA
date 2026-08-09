import os
import datetime

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory")

def init_memory_dir():
    """Ensures memory directory exists."""
    os.makedirs(MEMORY_DIR, exist_ok=True)

def record_confirmed_fact(fact, context="Explicitly confirmed by user"):
    """
    Writes one approved fact to memory/ as a dated Markdown file.
    Must ONLY be invoked after explicit confirmation from Harshith.
    """
    init_memory_dir()
    today_str = datetime.date.today().isoformat()
    filepath = os.path.join(MEMORY_DIR, f"{today_str}.md")

    entry = (
        f"# Memory\n\n"
        f"Date: {today_str}\n\n"
        f"Fact:\n{fact}\n\n"
        f"Context:\n{context}\n\n"
        f"---\n"
    )

    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(entry)
        return {
            "status": "success",
            "file": f"memory/{today_str}.md",
            "fact": fact,
            "message": f"Recorded to memory/{today_str}.md: '{fact}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Memory write failed: {str(e)}"}

def get_all_memories():
    """Reads all recorded memory entries."""
    init_memory_dir()
    memories = []
    if os.path.exists(MEMORY_DIR):
        for filename in sorted(os.listdir(MEMORY_DIR)):
            if filename.endswith(".md"):
                path = os.path.join(MEMORY_DIR, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        memories.append({"file": filename, "content": f.read()})
                except Exception:
                    continue
    return memories