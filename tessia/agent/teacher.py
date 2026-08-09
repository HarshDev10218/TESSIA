KNOWLEDGE_LEVELS = ["Unknown", "Familiar", "Basic", "Intermediate", "Strong", "Advanced"]

class TeacherEngine:
    def __init__(self):
        # In-memory tracking level per topic
        self.user_levels = {}

    def get_level(self, topic):
        return self.user_levels.get(topic, "Unknown")

    def update_level(self, topic, demonstrated_understanding):
        """
        Dynamically adjusts user knowledge level based on demonstrated capability.
        demonstrated_understanding: -1 (stuck), 0 (maintained), +1 (mastered step)
        """
        current = self.get_level(topic)
        curr_idx = KNOWLEDGE_LEVELS.index(current)
        
        if demonstrated_understanding > 0 and curr_idx < len(KNOWLEDGE_LEVELS) - 1:
            new_level = KNOWLEDGE_LEVELS[curr_idx + 1]
        elif demonstrated_understanding < 0 and curr_idx > 0:
            new_level = KNOWLEDGE_LEVELS[curr_idx - 1]
        else:
            new_level = current

        self.user_levels[topic] = new_level
        return new_level

    def build_lesson(self, topic, mode="standard"):
        """
        Teaches using: Concept ➔ Intuition ➔ Example ➔ Technical Explanation ➔ Practice
        """
        level = self.get_level(topic)

        if mode == "socratic":
            return {
                "mode": "socratic",
                "topic": topic,
                "current_level": level,
                "question": f"To begin exploring {topic}: What do you think happens when this system receives unexpected input?",
                "guidance": "Answer with your first intuition, and we will build from there."
            }

        return {
            "mode": "standard",
            "topic": topic,
            "current_level": level,
            "concept": f"**Concept:** {topic} is a structural pattern designed to decouple components.",
            "intuition": f"**Intuition:** Imagine a postal sorting office where packages are routed strictly by zip code rather than manually inspected at every door.",
            "example": f"**Example:** A central router passing requests to dedicated tool modules.",
            "technical_explanation": f"**Technical Detail:** Implements interface contracts and dispatch tables to maintain clean boundaries.",
            "user_practice_prompt": "Try explaining in your own words how you would apply this concept to your current project."
        }

    def offer_hint(self, topic, attempt_count):
        """Delivers progressive hints without giving away the direct solution immediately."""
        hints = [
            "Hint 1: Focus on how data enters the system before looking at state transitions.",
            "Hint 2: Check the return type of the primary handler method.",
            "Hint 3: Consider isolating the loop condition to prevent edge case overruns."
        ]
        idx = min(attempt_count - 1, len(hints) - 1)
        return hints[idx]