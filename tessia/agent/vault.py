import os
import re

# Regex for [[wikilink]] or [[wikilink|alias]]
WIKILINK_REGEX = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]")

def extract_wikilinks(content):
    """Extracts target link names from [[wikilinks]]."""
    if not content:
        return []
    matches = WIKILINK_REGEX.findall(content)
    # Normalize link names (strip whitespace and lower/title keying)
    return [m.strip() for m in matches if m.strip()]

def _canonical_key(name):
    """Normalizes note titles/filenames for graph node matching."""
    name = os.path.splitext(name)[0]  # strip extension if present
    return name.replace("_", " ").replace("-", " ").strip().lower()

class KnowledgeVault:
    def __init__(self):
        self.nodes = {}       # key -> node metadata
        self.edges = []       # list of {source, target} dicts
        self.file_types = {}  # ext -> count
        self.total_files = 0

    def build_graph(self, indexed_files):
        """Builds nodes and edges from scanned file records."""
        self.nodes.clear()
        self.edges.clear()
        self.file_types.clear()
        self.total_files = len(indexed_files)

        # Step 1: Create nodes for all actual indexed files
        key_to_id = {}
        for file_info in indexed_files:
            ext = file_info["extension"]
            self.file_types[ext] = self.file_types.get(ext, 0) + 1

            filename = file_info["filename"]
            raw_title = os.path.splitext(filename)[0].replace("_", " ")
            canon_key = _canonical_key(filename)

            node_id = filename
            key_to_id[canon_key] = node_id

            self.nodes[node_id] = {
                "id": node_id,
                "title": raw_title,
                "filepath": file_info["filepath"],
                "extension": ext,
                "size_bytes": file_info["size_bytes"],
                "content": file_info["content"],
                "wikilinks": extract_wikilinks(file_info["content"]),
                "in_degree": 0,
                "out_degree": 0,
                "total_degree": 0,
                "is_virtual": False
            }

        # Step 2: Extract edges and create virtual nodes for uncreated targets
        edge_set = set()
        for node_id, node in list(self.nodes.items()):
            for link_target in node["wikilinks"]:
                target_key = _canonical_key(link_target)

                if target_key in key_to_id:
                    target_id = key_to_id[target_key]
                else:
                    # Target node doesn't exist as a physical file - create virtual node
                    virtual_id = link_target + ".md"
                    key_to_id[target_key] = virtual_id
                    target_id = virtual_id
                    
                    if target_id not in self.nodes:
                        self.nodes[target_id] = {
                            "id": target_id,
                            "title": link_target.replace("_", " "),
                            "filepath": None,
                            "extension": ".md",
                            "size_bytes": 0,
                            "content": "",
                            "wikilinks": [],
                            "in_degree": 0,
                            "out_degree": 0,
                            "total_degree": 0,
                            "is_virtual": True
                        }

                if node_id != target_id and (node_id, target_id) not in edge_set:
                    edge_set.add((node_id, target_id))
                    self.edges.append({"source": node_id, "target": target_id})

        # Step 3: Compute degree metrics and identify hubs
        for edge in self.edges:
            src = edge["source"]
            tgt = edge["target"]
            if src in self.nodes:
                self.nodes[src]["out_degree"] += 1
            if tgt in self.nodes:
                self.nodes[tgt]["in_degree"] += 1

        for n in self.nodes.values():
            n["total_degree"] = n["in_degree"] + n["out_degree"]

    def get_top_hubs(self, top_n=10):
        """Returns top N most connected nodes (hubs)."""
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda x: x["total_degree"],
            reverse=True
        )
        return sorted_nodes[:top_n]

    def get_stats(self):
        """Returns indexer summary statistics."""
        return {
            "total_files": self.total_files,
            "file_types": dict(self.file_types),
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "top_hubs": [
                {
                    "title": node["title"],
                    "id": node["id"],
                    "degree": node["total_degree"],
                    "in_degree": node["in_degree"],
                    "out_degree": node["out_degree"],
                    "is_virtual": node["is_virtual"]
                }
                for node in self.get_top_hubs(10)
            ]
        }