import os
import random

DEMO_DIR = os.path.join(os.path.dirname(__file__), "demo")

def generate_demo():
    os.makedirs(DEMO_DIR, exist_ok=True)
    random.seed(42)

    files = {
        "AI_Systems.md": """# AI Systems
Overview of [[Artificial_Intelligence]] and modern software architectures.

- Core components: [[Neural_Networks]], [[Knowledge_Graphs]], [[Agent_Architecture]]
- Applications: [[Research_Assistant]], [[Voice_Interface]]

See also: [[Socratic_Teaching]] for educational AI.
""",
        "Knowledge_Graphs.md": """# Knowledge Graphs
Knowledge graphs represent entities and their relationships.

- Links: [[AI_Systems]], [[Memory_Management]], [[Vault_Indexing]]
- Used in [[Research_Assistant]] to map cross-references.
- Graph edges can be extracted via [[Wikilinks_Parser]].
""",
        "Neural_Networks.md": """# Neural Networks
Foundation of deep learning and language models.

- Related topics: [[AI_Systems]], [[Transformer_Models]], [[Machine_Learning]]
- Used by [[Voice_Interface]] for speech recognition.
""",
        "Agent_Architecture.md": """# Agent Architecture
Design patterns for autonomous AI assistants like [[TESSIA]].

- Subsystems: [[Memory_Management]], [[Vault_Indexing]], [[Tools_Router]]
- Integrates [[Research_Assistant]] and [[Teacher_Mode]].
""",
        "Research_Assistant.md": """# Research Assistant
Automated research workflows.

- Works with [[Knowledge_Graphs]] to trace facts.
- Connects to [[AI_Systems]] and [[Adaptive_Learning]].
- Reads documents processed by [[Vault_Indexing]].
""",
        "Teacher_Mode.md": """# Teacher Mode
Adaptive teaching framework for TESSIA.

- Methods: [[Socratic_Teaching]], [[Adaptive_Learning]], [[Project_Based_Learning]]
- Linked with [[Agent_Architecture]] and [[Memory_Management]].
""",
        "Socratic_Teaching.md": """# Socratic Teaching
Teaching by asking guiding questions rather than giving direct answers.

- Part of [[Teacher_Mode]].
- Integrates with [[Adaptive_Learning]].
""",
        "Adaptive_Learning.md": """# Adaptive Learning
Tracking student knowledge levels from Basic to Advanced.

- Works with [[Socratic_Teaching]] and [[Teacher_Mode]].
- Influences [[Research_Assistant]] summaries.
""",
        "Project_Based_Learning.md": """# Project-Based Learning
Connecting theoretical concepts to hands-on software projects.

- Connects [[Teacher_Mode]] to real code.
""",
        "Voice_Interface.md": """# Voice Interface
Speech input and output for TESSIA.

- Relies on speech models from [[Neural_Networks]].
- Integrated into [[Agent_Architecture]].
""",
        "Memory_Management.md": """# Memory Management
Isolated, explicit user memory storage.

- Governed by [[Agent_Architecture]].
- Links concepts stored in [[Knowledge_Graphs]].
- Updates [[TESSIA_Config.txt]].
""",
        "Vault_Indexing.md": """# Vault Indexing
Scans local directories for Markdown, TXT, and PDF files.

- Feeds nodes into [[Knowledge_Graphs]].
- Implements [[Wikilinks_Parser]].
- Used by [[Agent_Architecture]] and [[Research_Assistant]].
""",
        "Wikilinks_Parser.md": """# Wikilinks Parser
Extracts target links in the format `[[Target Note]]`.

- Essential for [[Vault_Indexing]].
- Builds edges for [[Knowledge_Graphs]].
""",
        "Transformer_Models.md": """# Transformer Models
Sequence-to-sequence models underlying LLMs.

- Subtopic of [[Neural_Networks]] and [[AI_Systems]].
""",
        "Machine_Learning.md": """# Machine Learning
Broad field covering statistical learning models.

- Parent concept for [[Neural_Networks]] and [[AI_Systems]].
""",
        "Tools_Router.md": """# Tools Router
Routes incoming user requests to relevant tools safely.

- Part of [[Agent_Architecture]].
- Controls call access to [[Vault_Indexing]] and [[Research_Assistant]].
""",
        "TESSIA_Config.txt": """TESSIA System Configuration Notes
- Mode: Demo Mode Active
- Linked Modules: [[Agent_Architecture]], [[Memory_Management]]
- Target User: Harshith
""",
        "Sample_Paper.txt": """Research Summary Notes
Topic: Knowledge graph extraction using [[Wikilinks_Parser]].
References: [[Knowledge_Graphs]], [[AI_Systems]], [[Vault_Indexing]].
"""
    }

    for filename, content in files.items():
        filepath = os.path.join(DEMO_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"Generated {len(files)} demo files in {DEMO_DIR}")

if __name__ == "__main__":
    generate_demo()