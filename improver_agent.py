"""
Improver Agent
==============
Refines a response based on structured feedback from the Critic Agent.

The Improver Agent applies targeted transformations to address each identified weakness:
  - Low clarity      → Simplify sentences, remove vague language
  - Low completeness → Expand paragraphs, add missing content
  - Low logic        → Add structural transitions and a proper conclusion
  - Low tone         → Replace informal language with professional alternatives
  - Low specificity  → Inject concrete examples and illustrative details

In API Mode, the Improver sends the original response + critique to Claude/OpenAI
and asks for a rewritten, improved version.
"""

import re
import os
import textwrap
from utils.logger import Logger


class ImproverAgent:
    """
    Improves a response based on critic feedback.
    
    Attributes:
        mode (str): 'rule' or 'api'
        api_key (str): Optional API key
        logger (Logger): Shared logger instance
    """

    def __init__(self, mode="rule", api_key=None):
        """
        Initialize the ImproverAgent.
        
        Args:
            mode (str): 'rule' or 'api'
            api_key (str): Optional API key
        """
        self.mode = mode
        self.api_key = api_key
        self.logger = Logger()

    # ──────────────────────────────────────────────────────────────────────────
    # Public Interface
    # ──────────────────────────────────────────────────────────────────────────

    def improve(self, response: str, critique: dict, prompt: str, iteration: int) -> str:
        """
        Apply improvements to a response based on critic feedback.
        
        Args:
            response (str): Current response text to improve.
            critique (dict): Output from CriticAgent.evaluate().
            prompt (str): Original user prompt (for context).
            iteration (int): Current iteration number (1-based).
        
        Returns:
            str: Improved response text.
        """
        self.logger.agent("IMPROVER", f"Applying improvements (iteration {iteration})...")

        if self.mode == "api":
            improved = self._improve_via_api(response, critique, prompt)
        else:
            improved = self._improve_rule_based(response, critique, prompt, iteration)

        old_count = len(response.split())
        new_count = len(improved.split())
        delta = new_count - old_count
        sign = "+" if delta >= 0 else ""
        self.logger.success(f"Improvement applied — {old_count} → {new_count} words ({sign}{delta})")

        return improved

    # ──────────────────────────────────────────────────────────────────────────
    # Rule-Based Improvement
    # ──────────────────────────────────────────────────────────────────────────

    def _improve_rule_based(self, response: str, critique: dict, prompt: str, iteration: int) -> str:
        """
        Apply targeted, rule-based improvements based on critique scores.
        
        Improvements are applied in order of severity (worst score first).
        Each iteration builds on the previous version.
        
        Args:
            response (str): Text to improve.
            critique (dict): Critique dict with 'scores' and 'weaknesses'.
            prompt (str): Original prompt.
            iteration (int): Iteration number.
        
        Returns:
            str: Improved text.
        """
        scores = critique["scores"]
        improved = response
        topic = self._extract_topic(prompt)

        # Sort dimensions by score (ascending) to fix worst issues first
        sorted_dims = sorted(scores.items(), key=lambda x: x[1])

        for dim, score in sorted_dims:
            if score < 7.0:
                self.logger.detail(f"  Fixing: {dim} (score {score}/10)")
                improved = self._apply_fix(improved, dim, score, topic, iteration)

        return improved.strip()

    def _apply_fix(self, text: str, dimension: str, score: float, topic: str, iteration: int) -> str:
        """
        Apply a specific fix for a given quality dimension.
        
        Args:
            text (str): Current text.
            dimension (str): Dimension to fix.
            score (float): Current score for that dimension.
            topic (str): Extracted topic.
            iteration (int): Iteration number.
        
        Returns:
            str: Fixed text.
        """
        if dimension == "clarity":
            return self._fix_clarity(text)
        elif dimension == "completeness":
            return self._fix_completeness(text, topic, score, iteration)
        elif dimension == "logic":
            return self._fix_logic(text)
        elif dimension == "tone":
            return self._fix_tone(text)
        elif dimension == "specificity":
            return self._fix_specificity(text, topic, iteration)
        return text

    def _fix_clarity(self, text: str) -> str:
        """
        Improve clarity by replacing vague phrases with clearer alternatives.
        
        Args:
            text (str): Text to fix.
        
        Returns:
            str: Clearer text.
        """
        replacements = {
            "various aspects":              "key aspects",
            "several things":              "several important factors",
            "many aspects":               "multiple key dimensions",
            "different angles":           "multiple perspectives",
            "continues to develop":       "is rapidly evolving",
            "keep in mind":               "note",
            "always more to learn":       "significant depth to explore in this field",
            "broad area":                 "multifaceted discipline",
            "it has many applications":   "it has wide-ranging practical applications",
            "results can vary":           "outcomes depend on specific context and implementation",
            "think carefully":            "apply systematic analysis",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _fix_completeness(self, text: str, topic: str, score: float, iteration: int) -> str:
        """
        Expand the response with additional relevant content.
        
        Args:
            text (str): Text to expand.
            topic (str): Subject matter.
            score (float): Current completeness score.
            iteration (int): Determines which expansion block to add.
        
        Returns:
            str: Expanded text.
        """
        # Choose expansion content based on iteration to avoid repetition
        expansions = [
            textwrap.dedent(f"""

            Understanding {topic} in Depth

            To fully grasp {topic}, it is essential to explore its foundational principles. At its core, this subject encompasses a set of interconnected ideas that have been refined through both theory and practice. Scholars and practitioners in this field have identified several key mechanisms that drive outcomes and determine success.

            The historical development of {topic} offers important context. Over time, early frameworks have been challenged, refined, and replaced by more sophisticated models that better account for real-world complexity. This evolution reflects the dynamic nature of knowledge in this area.
            """),
            textwrap.dedent(f"""

            Practical Applications and Real-World Relevance

            One of the most compelling aspects of {topic} is its practical applicability. In professional settings, understanding this subject enables better decision-making, problem-solving, and innovation. Organizations that have invested in deep knowledge of {topic} consistently demonstrate stronger performance and adaptability.

            Consider, for example, how principles drawn from {topic} have been applied in technology, education, healthcare, and business. In each domain, practitioners adapt core concepts to their unique challenges, demonstrating the versatility and enduring relevance of this knowledge.
            """),
            textwrap.dedent(f"""

            Common Challenges and How to Overcome Them

            Despite its importance, {topic} presents several recurring challenges. Practitioners often struggle with the complexity of applying theoretical knowledge to real situations, managing trade-offs between competing priorities, and staying current as the field evolves.

            Effective approaches to these challenges include: structured learning frameworks, mentorship from experienced practitioners, iterative experimentation, and continuous reflection on outcomes. By acknowledging these difficulties proactively, learners can develop resilience and adaptability in their engagement with {topic}.
            """),
        ]

        # Pick expansion based on iteration (cycling through available options)
        expansion = expansions[(iteration - 1) % len(expansions)]
        return text + expansion

    def _fix_logic(self, text: str) -> str:
        """
        Improve logical flow by adding transitions and strengthening the conclusion.
        
        Args:
            text (str): Text to fix.
        
        Returns:
            str: More logically structured text.
        """
        # Add transitions to existing paragraph starters
        transition_map = [
            (r'^(First,)', r'To begin with,'),
            (r'^(Second,)', r'Building on this foundation,'),
            (r'^(Third,)', r'Furthermore,'),
        ]
        for pattern, replacement in transition_map:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)

        # Strengthen the conclusion paragraph only if not already strengthened
        paragraphs = text.split('\n\n')
        if paragraphs:
            last = paragraphs[-1]
            already_enhanced = any(
                phrase in last
                for phrase in ["Understanding these dimensions", "To synthesize the key points discussed:"]
            )
            if not already_enhanced and not any(
                word in last.lower() for word in ["therefore", "ultimately", "as demonstrated", "it is clear"]
            ):
                # Replace the weak concluding sentence with a stronger one
                last_sentences = re.split(r'(?<=[.!?])\s+', last.strip())
                if last_sentences:
                    last_sentences[-1] = (
                        "Understanding these dimensions and their interrelationships is "
                        "essential for anyone seeking to apply this knowledge effectively."
                    )
                    paragraphs[-1] = " ".join(last_sentences)
            text = '\n\n'.join(paragraphs)

        return text

    def _fix_tone(self, text: str) -> str:
        """
        Improve professional tone by replacing informal language.
        
        Args:
            text (str): Text to fix.
        
        Returns:
            str: More professionally toned text.
        """
        informal_to_formal = {
            "stuff":        "material",
            "things":       "elements",
            "kind of":      "somewhat",
            "sort of":      "relatively",
            "basically":    "fundamentally",
            "really really": "exceptionally",
            "very very":    "highly",
            "a lot of":     "a significant number of",
            "get better":   "improve",
            "make sure":    "ensure",
            "find out":     "determine",
            "look at":      "examine",
            "talk about":   "discuss",
        }
        for informal, formal in informal_to_formal.items():
            text = text.replace(informal, formal)

        return text

    def _fix_specificity(self, text: str, topic: str, iteration: int) -> str:
        """
        Add concrete examples and specifics to the response.
        
        Args:
            text (str): Text to improve.
            topic (str): Subject matter.
            iteration (int): Controls which example to insert.
        
        Returns:
            str: More specific text.
        """
        # Example blocks tied to iteration number
        examples = [
            f"\n\nFor example, consider how {topic} manifests in practice: a professional encountering this concept for the first time might apply its principles by breaking the problem into smaller components, analyzing each systematically, and synthesizing a coherent solution. This structured approach consistently yields superior outcomes compared to ad hoc methods.",
            f"\n\nTo illustrate this more concretely, research in this area has shown that practitioners who develop deep expertise in {topic} are, on average, significantly more effective at achieving their goals. Specifically, they demonstrate stronger analytical skills, clearer communication, and more robust decision-making frameworks.",
            f"\n\nA practical example: organizations that systematically apply insights from {topic} have reported measurable improvements in efficiency, stakeholder satisfaction, and long-term sustainability. These outcomes underscore the tangible value of investing in this knowledge.",
        ]

        example_text = examples[(iteration - 1) % len(examples)]

        # Insert before the final paragraph
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1:
            paragraphs.insert(-1, example_text.strip())
            return '\n\n'.join(paragraphs)
        else:
            return text + example_text

    # ──────────────────────────────────────────────────────────────────────────
    # API-Based Improvement
    # ──────────────────────────────────────────────────────────────────────────

    def _improve_via_api(self, response: str, critique: dict, prompt: str) -> str:
        """
        Use Claude API to generate an improved version of the response.
        
        Sends the original response plus the structured critique and asks
        Claude to produce a significantly better version.
        
        Args:
            response (str): Current response.
            critique (dict): Critic's evaluation.
            prompt (str): Original user prompt.
        
        Returns:
            str: Improved response from the API.
        """
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            # Format weaknesses as a bulleted list
            weaknesses_text = "\n".join(f"  • {w}" for w in critique.get("weaknesses", []))
            feedback_text = "\n".join(f"  • {f}" for f in critique.get("feedback", []))
            scores_text = "\n".join(
                f"  • {dim.capitalize()}: {score}/10"
                for dim, score in critique["scores"].items()
            )

            improve_prompt = f"""You are an expert writer and editor. Your task is to significantly improve a response based on specific feedback.

Original Question/Topic:
{prompt}

Current Response (needs improvement):
---
{response}
---

Quality Scores:
{scores_text}

Identified Weaknesses:
{weaknesses_text}

Specific Improvement Instructions:
{feedback_text}

Please rewrite the response to address ALL identified weaknesses. The improved version should:
1. Be significantly better than the original in the weak areas
2. Preserve and build upon the strengths
3. Be well-structured, specific, and professionally written
4. Include concrete examples where relevant
5. Have a clear introduction, body, and conclusion

Write ONLY the improved response, with no preamble or meta-commentary."""

            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1500,
                messages=[{"role": "user", "content": improve_prompt}]
            )
            return message.content[0].text.strip()

        except Exception as e:
            self.logger.warning(f"API improvement failed: {e}. Using rule-based fallback.")
            return self._improve_rule_based(response, critique, prompt, 1)

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_topic(self, prompt: str) -> str:
        """
        Extract a clean topic label from a prompt string.
        
        Args:
            prompt (str): User's raw input.
        
        Returns:
            str: Cleaned topic string.
        """
        starters = [
            "explain", "describe", "what is", "what are", "how does", "how do",
            "tell me about", "give me", "write about", "discuss", "define",
            "can you explain", "please explain"
        ]
        topic = prompt.strip()
        for starter in starters:
            if topic.lower().startswith(starter):
                topic = topic[len(starter):].strip()
                break

        topic = topic.rstrip("?.!").strip()

        # If the extracted topic is still very long, take just the first concept
        if len(topic) > 60:
            for delimiter in [", covering", ", including", " to a ", " for a ", " in a ", ","]:
                if delimiter in topic:
                    topic = topic.split(delimiter)[0].strip()
                    break
            if len(topic) > 60:
                topic = " ".join(topic.split()[:6])

        if topic:
            topic = topic[0].upper() + topic[1:]

        return topic if topic else "this subject"
