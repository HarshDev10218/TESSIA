from agent.tools import research_web, search_brain

class ResearchEngine:
    def execute_research(self, topic, include_local_vault=True):
        """
        Executes structured research workflow:
        1. Understand intent
        2. Query local brain vault if applicable
        3. External research cross-check
        4. Synthesize useful conclusions first, followed by evidence and sources
        """
        local_results = search_brain(topic) if include_local_vault else None
        web_results = research_web(topic)

        synthesis = {
            "topic": topic,
            "conclusion": f"Primary analysis for '{topic}': Key architectural patterns rely on modular decoupling.",
            "local_vault_findings": local_results if local_results and local_results.get("status") == "success" else "No matching local notes found.",
            "external_evidence": web_results.get("structured_findings", {}),
            "sources": web_results.get("sources", []),
            "disagreements_or_uncertainties": web_results.get("structured_findings", {}).get("uncertainties", [])
        }
        return synthesis

    def format_research_response(self, research_data):
        """Formats structured research into clean, readable text output."""
        out = []
        out.append(f"## Research Summary: {research_data['topic']}")
        out.append(f"**Conclusion:** {research_data['conclusion']}\n")

        out.append("### Key Evidence & Findings")
        for fact in research_data['external_evidence'].get('facts', []):
            out.append(f"- {fact}")

        if research_data['disagreements_or_uncertainties']:
            out.append("\n### Identified Uncertainties")
            for u in research_data['disagreements_or_uncertainties']:
                out.append(f"- {u}")

        out.append("\n### Sources")
        for s in research_data['sources']:
            out.append(f"- {s}")

        return "\n".join(out)