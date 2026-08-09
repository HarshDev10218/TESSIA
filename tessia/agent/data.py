import os
import re

# Constants
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB limit
IGNORED_DIRS = {
    ".git", "node_modules", "caches", "__pycache__", ".venv",
    "venv", ".idea", ".vscode", "dist", "build", ".cache"
}
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}

def get_data_mode():
    """Reads TESSIA_DEMO environment variable. Default is 1 (Demo mode)."""
    return os.environ.get("TESSIA_DEMO", "1").strip()

def get_target_directories():
    """
    Returns list of directory paths to scan based on mode.
    Only agent/data.py accesses environment and folder paths directly.
    """
    mode = get_data_mode()
    if mode == "1":
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        demo_dir = os.path.join(base_dir, "data", "demo")
        return [demo_dir]
    else:
        # Real mode: Read configured folders from environment variable TESSIA_FOLDERS
        configured = os.environ.get("TESSIA_FOLDERS", "")
        if not configured:
            return []
        paths = [p.strip() for p in configured.split(",") if p.strip()]
        return [p for p in paths if os.path.isdir(p)]

def _extract_pdf_text_stdlib(filepath):
    """
    Extract readable text stream fragments from PDF using standard library.
    Acts as a lightweight, pure-Python fallback without external dependencies.
    """
    try:
        with open(filepath, "rb") as f:
            content = f.read()
        # Find stream objects or text between BT (Begin Text) and ET (End Text)
        text_parts = []
        # Extract ASCII / UTF-8 readable strings inside PDF stream blocks
        matches = re.findall(b"BT(.*?)ET", content, re.DOTALL)
        for match in matches:
            # Extract parenthesized strings (e.g. (Hello World) Tj)
            str_matches = re.findall(b"\\((.*?)\\)", match)
            for s in str_matches:
                try:
                    decoded = s.decode("utf-8", errors="ignore")
                    if decoded.strip():
                        text_parts.append(decoded.strip())
                except Exception:
                    continue
        return " ".join(text_parts)
    except Exception as e:
        return f"[PDF Read Error: {str(e)}]"

def read_file_content(filepath):
    """Safely reads file content subject to size and extension checks."""
    if not os.path.exists(filepath):
        return None
    
    if os.path.getsize(filepath) > MAX_FILE_SIZE_BYTES:
        return None  # Skip files larger than 2MB

    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return None

    if ext == ".pdf":
        return _extract_pdf_text_stdlib(filepath)

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"[File Read Error: {str(e)}]"

def scan_files():
    """
    Recursively scans allowed directories and returns structured raw file metadata.
    Does NOT modify, write, delete, or overwrite any source file.
    """
    directories = get_target_directories()
    indexed_files = []

    for root_dir in directories:
        if not os.path.exists(root_dir):
            continue

        for root, dirs, files in os.walk(root_dir):
            # Exclude ignored directories in-place
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    full_path = os.path.join(root, filename)

                    # Check file size
                    try:
                        size = os.path.getsize(full_path)
                    except OSError:
                        continue

                    if size > MAX_FILE_SIZE_BYTES:
                        continue

                    content = read_file_content(full_path)
                    if content is not None:
                        indexed_files.append({
                            "filepath": full_path,
                            "filename": filename,
                            "extension": ext,
                            "size_bytes": size,
                            "content": content
                        })

    return indexed_files