"""
Critic Agent
============
Evaluates a response and identifies weaknesses across multiple quality dimensions.

Scoring Dimensions (each 0-10):
  - Clarity     : Is the response easy to understand?
  - Completeness: Does it cover the topic thoroughly?
  - Logic       : Is the reasoning sound and well-structured?
  - Tone        : Is the language appropriate and engaging?
  - Specificity : Does it include concrete details, examples, or evidence?

The final score is a weighted average of these dimensions.
The Critic also produces actionable feedback for the Improver Agent.
"""

import re
import os
from utils.logger import Logger


class CriticAgent:
    """
    Evaluates response quality and provides structured feedback.
    
    Attributes:
        mode (str): 'rule' or 'api'
        api_key (str): Optional API key
        logger (Logger): Shared logger instance
    
    Scoring Weights:
        - Clarity      25%
        - Completeness 30%
        - Logic        20%
        - Tone         10%
        - Specificity  15%
    """

    # Scoring dimension weights (must sum to 1.0)
    WEIGHTS = {
        "clarity":      0.25,
        "completeness": 0.30,
        "logic":        0.20,
        "tone":         0.10,
        "specificity":  0.15,
    }

    def __init__(self, mode="rule", api_key=None):
        """
        Initialize the CriticAgent.
        
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

    def evaluate(self, response: str, prompt: str) -> dict:
        """
        Evaluate a response and return a structured critique.
        
        Args:
            response (str): The text to evaluate.
            prompt (str): The original user prompt (for context).
        
        Returns:
            dict: {
                'scores': {dimension: score, ...},
                'overall_score': float,
                'feedback': [list of feedback strings],
                'strengths': [list of strength strings],
                'weaknesses': [list of weakness strings]
            }
        """
        self.logger.agent("CRITIC", "Evaluating response quality...")

        if self.mode == "api":
            result = self._evaluate_via_api(response, prompt)
        else:
            result = self._evaluate_rule_based(response, prompt)

        overall = result["overall_score"]
        grade = self._score_to_grade(overall)
        self.logger.success(f"Evaluation complete — Score: {overall:.1f}/10 ({grade})")

        # Print dimension scores
        for dim, score in result["scores"].items():
            bar = self._score_bar(score)
            self.logger.detail(f"  {dim.capitalize():<14} {bar}  {score:.1f}/10")

        # Print feedback summary
        if result["weaknesses"]:
            self.logger.detail("  Weaknesses identified:")
            for w in result["weaknesses"]:
                self.logger.detail(f"    • {w}")

        return result

    # ──────────────────────────────────────────────────────────────────────────
    # Rule-Based Evaluation
    # ──────────────────────────────────────────────────────────────────────────

    def _evaluate_rule_based(self, response: str, prompt: str) -> dict:
        """
        Evaluate the response using rule-based heuristics.
        
        Analyzes text properties like length, structure, vocabulary,
        sentence variety, and use of examples to estimate quality.
        
        Args:
            response (str): Text to evaluate.
            prompt (str): Original prompt for relevance checking.
        
        Returns:
            dict: Full evaluation result.
        """
        words = response.split()
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]

        word_count = len(words)
        sentence_count = max(len(sentences), 1)
        avg_sentence_len = word_count / sentence_count
        paragraph_count = len(paragraphs)

        # ── Clarity Score ────────────────────────────────────────────────────
        # Based on: sentence length variety, absence of repetition, readability
        clarity_score = 5.0
        if avg_sentence_len < 10:
            clarity_score -= 1.0  # Too choppy
        elif avg_sentence_len > 30:
            clarity_score -= 1.5  # Too dense
        else:
            clarity_score += 1.0

        # Check for varied sentence lengths (sign of good writing)
        if sentence_count > 2:
            lengths = [len(s.split()) for s in sentences]
            variance = max(lengths) - min(lengths)
            if variance > 8:
                clarity_score += 1.0
            
        # Penalize excessive repetition of vague phrases
        vague_phrases = ["various", "several", "many aspects", "different angles", "continues to develop"]
        vague_count = sum(response.lower().count(p) for p in vague_phrases)
        clarity_score -= min(vague_count * 0.5, 2.0)

        clarity_score = max(1.0, min(10.0, clarity_score))

        # ── Completeness Score ───────────────────────────────────────────────
        # Based on: word count, paragraph structure, topic coverage
        completeness_score = 3.0

        if word_count >= 100:
            completeness_score += 1.0
        if word_count >= 200:
            completeness_score += 1.5
        if word_count >= 350:
            completeness_score += 1.0
        if paragraph_count >= 3:
            completeness_score += 1.0
        if paragraph_count >= 5:
            completeness_score += 1.0

        # Check if key prompt words appear in response
        prompt_keywords = set(re.findall(r'\b\w{5,}\b', prompt.lower()))
        response_keywords = set(re.findall(r'\b\w{5,}\b', response.lower()))
        overlap = len(prompt_keywords & response_keywords)
        coverage_ratio = overlap / max(len(prompt_keywords), 1)
        completeness_score += coverage_ratio * 2.0

        completeness_score = max(1.0, min(10.0, completeness_score))

        # ── Logic Score ──────────────────────────────────────────────────────
        # Based on: presence of structure markers, transition words, conclusion
        logic_score = 4.0
        
        structure_markers = ["first", "second", "third", "finally", "therefore",
                             "however", "furthermore", "in addition", "as a result",
                             "consequently", "in conclusion", "to summarize"]
        found_markers = sum(1 for m in structure_markers if m in response.lower())
        logic_score += min(found_markers * 0.5, 3.0)

        # Penalize if there's no conclusion-like paragraph
        has_conclusion = any(p.lower()[:30].find(word) != -1
                            for p in paragraphs[-1:]
                            for word in ["conclusion", "summary", "overall", "therefore", "thus"])
        if not has_conclusion:
            logic_score -= 1.0

        logic_score = max(1.0, min(10.0, logic_score))

        # ── Tone Score ───────────────────────────────────────────────────────
        # Based on: professional vocabulary, absence of filler words
        tone_score = 5.0

        filler_words = ["stuff", "things", "very very", "really really", "kind of", "sort of", "basically"]
        filler_count = sum(response.lower().count(f) for f in filler_words)
        tone_score -= min(filler_count * 0.5, 2.0)

        # Reward formal/professional vocabulary
        formal_words = ["demonstrates", "indicates", "suggests", "furthermore",
                       "consequently", "significant", "essential", "fundamental"]
        formal_count = sum(1 for w in formal_words if w in response.lower())
        tone_score += min(formal_count * 0.3, 2.0)

        tone_score = max(1.0, min(10.0, tone_score))

        # ── Specificity Score ────────────────────────────────────────────────
        # Based on: presence of examples, numbers, specific terminology
        specificity_score = 3.0

        example_indicators = ["for example", "for instance", "such as", "e.g.", "specifically",
                              "in particular", "to illustrate", "consider"]
        example_count = sum(1 for e in example_indicators if e in response.lower())
        specificity_score += min(example_count * 1.0, 3.0)

        # Check for numbers/statistics
        numbers = re.findall(r'\b\d+\.?\d*\b', response)
        if len(numbers) >= 2:
            specificity_score += 1.0
        if len(numbers) >= 5:
            specificity_score += 1.0

        # Check for named concepts or quoted terms
        quoted_terms = re.findall(r'"[^"]{3,30}"', response)
        specificity_score += min(len(quoted_terms) * 0.5, 1.5)

        specificity_score = max(1.0, min(10.0, specificity_score))

        # ── Compute Weighted Overall Score ───────────────────────────────────
        scores = {
            "clarity":      round(clarity_score, 1),
            "completeness": round(completeness_score, 1),
            "logic":        round(logic_score, 1),
            "tone":         round(tone_score, 1),
            "specificity":  round(specificity_score, 1),
        }
        overall_score = sum(scores[dim] * weight for dim, weight in self.WEIGHTS.items())
        overall_score = round(overall_score, 2)

        # ── Generate Feedback ─────────────────────────────────────────────────
        strengths, weaknesses, feedback = self._generate_feedback(scores, word_count, response)

        return {
            "scores": scores,
            "overall_score": overall_score,
            "feedback": feedback,
            "strengths": strengths,
            "weaknesses": weaknesses,
        }

    def _generate_feedback(self, scores: dict, word_count: int, response: str):
        """
        Generate human-readable feedback based on scores.
        
        Args:
            scores (dict): Dimension scores.
            word_count (int): Word count of response.
            response (str): Response text.
        
        Returns:
            tuple: (strengths, weaknesses, combined_feedback)
        """
        strengths = []
        weaknesses = []
        feedback = []

        # Clarity feedback
        if scores["clarity"] >= 7.0:
            strengths.append("Response is clear and easy to read")
        elif scores["clarity"] < 5.0:
            w = "Improve clarity: use shorter, more varied sentences and avoid vague language"
            weaknesses.append(w)
            feedback.append(w)

        # Completeness feedback
        if scores["completeness"] >= 7.0:
            strengths.append("Good depth and coverage of the topic")
        else:
            if word_count < 200:
                w = f"Response is too brief ({word_count} words). Expand with more detail and depth"
                weaknesses.append(w)
                feedback.append(w)
            else:
                w = "Add more relevant points to better cover the topic"
                weaknesses.append(w)
                feedback.append(w)

        # Logic feedback
        if scores["logic"] >= 7.0:
            strengths.append("Well-structured with clear logical flow")
        else:
            w = "Improve structure: add clear transitions (First, Furthermore, In conclusion)"
            weaknesses.append(w)
            feedback.append(w)

        # Tone feedback
        if scores["tone"] >= 7.0:
            strengths.append("Appropriate and professional tone throughout")
        elif scores["tone"] < 5.0:
            w = "Improve tone: use more precise, professional language"
            weaknesses.append(w)
            feedback.append(w)

        # Specificity feedback
        if scores["specificity"] >= 7.0:
            strengths.append("Good use of specific examples and concrete details")
        else:
            w = 'Add concrete examples ("for example..."), statistics, or specific use cases'
            weaknesses.append(w)
            feedback.append(w)

        return strengths, weaknesses, feedback

    # ──────────────────────────────────────────────────────────────────────────
    # API-Based Evaluation
    # ──────────────────────────────────────────────────────────────────────────

    def _evaluate_via_api(self, response: str, prompt: str) -> dict:
        """
        Evaluate quality using the Claude API with structured JSON output.
        
        Args:
            response (str): Text to evaluate.
            prompt (str): Original user prompt.
        
        Returns:
            dict: Evaluation result dict.
        """
        try:
            import anthropic
            import json

            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            eval_prompt = f"""You are a strict but fair content quality evaluator.

Original Question/Topic: {prompt}

Response to Evaluate:
---
{response}
---

Evaluate this response on a scale of 0-10 for each dimension:
1. clarity (easy to understand, well-written sentences)
2. completeness (covers the topic thoroughly)
3. logic (well-structured, sound reasoning)
4. tone (appropriate, professional, engaging)
5. specificity (uses concrete examples, data, or details)

Return ONLY a valid JSON object with this exact structure:
{{
  "scores": {{
    "clarity": <float>,
    "completeness": <float>,
    "logic": <float>,
    "tone": <float>,
    "specificity": <float>
  }},
  "strengths": ["<strength1>", "<strength2>"],
  "weaknesses": ["<weakness1>", "<weakness2>"],
  "feedback": ["<actionable improvement 1>", "<actionable improvement 2>"]
}}"""

            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=800,
                messages=[{"role": "user", "content": eval_prompt}]
            )

            raw = message.content[0].text.strip()
            # Strip markdown code fences if present
            raw = re.sub(r'^```json\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            result = json.loads(raw)

            scores = result["scores"]
            overall = sum(scores[dim] * weight for dim, weight in self.WEIGHTS.items())

            return {
                "scores": {k: round(float(v), 1) for k, v in scores.items()},
                "overall_score": round(overall, 2),
                "feedback": result.get("feedback", []),
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("weaknesses", []),
            }

        except Exception as e:
            self.logger.warning(f"API evaluation failed: {e}. Using rule-based fallback.")
            return self._evaluate_rule_based(response, prompt)

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 9.0: return "A+"
        if score >= 8.0: return "A"
        if score >= 7.0: return "B"
        if score >= 6.0: return "C"
        if score >= 5.0: return "D"
        return "F"

    def _score_bar(self, score: float, width: int = 10) -> str:
        """
        Create a visual bar for a score.
        
        Args:
            score (float): Score from 0-10.
            width (int): Total bar width characters.
        
        Returns:
            str: Visual bar like [████░░░░░░]
        """
        filled = int(round(score / 10 * width))
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
