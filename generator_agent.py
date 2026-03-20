"""
Generator Agent
===============
Responsible for producing the initial response to a user's prompt.

In Rule-Based Mode: Uses template-driven logic and heuristics to craft a response.
In API Mode: Sends the prompt to Claude/OpenAI and returns the raw response.

The Generator Agent does NOT evaluate quality — that's the Critic Agent's job.
"""

import os
import textwrap
from utils.logger import Logger


class GeneratorAgent:
    """
    Generates an initial response to the user's prompt.
    
    Attributes:
        mode (str): 'rule' or 'api'
        api_key (str): API key (used only in API mode)
        logger (Logger): Shared logger instance
    """

    def __init__(self, mode="rule", api_key=None):
        """
        Initialize the GeneratorAgent.
        
        Args:
            mode (str): 'rule' for simulated logic, 'api' for real API calls.
            api_key (str): Optional API key for API mode.
        """
        self.mode = mode
        self.api_key = api_key
        self.logger = Logger()

    # ──────────────────────────────────────────────────────────────────────────
    # Public Interface
    # ──────────────────────────────────────────────────────────────────────────

    def generate(self, prompt: str) -> str:
        """
        Generate an initial response for the given prompt.
        
        Args:
            prompt (str): The user's question or topic.
        
        Returns:
            str: The generated response text.
        """
        self.logger.agent("GENERATOR", f"Creating initial response for: \"{prompt[:60]}...\"" if len(prompt) > 60 else f"Creating initial response for: \"{prompt}\"")

        if self.mode == "api":
            response = self._generate_via_api(prompt)
        else:
            response = self._generate_rule_based(prompt)

        self.logger.success(f"Initial response generated ({len(response.split())} words)")
        return response

    # ──────────────────────────────────────────────────────────────────────────
    # Rule-Based Generation (No API Required)
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_rule_based(self, prompt: str) -> str:
        """
        Simulate a response using rule-based heuristics.
        
        This creates a realistic but intentionally imperfect first draft
        so that the Critic and Improver agents have something meaningful to work with.
        
        Args:
            prompt (str): User's input.
        
        Returns:
            str: A simulated first-draft response.
        """
        # Detect the type of prompt for better simulation
        prompt_lower = prompt.lower()
        topic = self._extract_topic(prompt)

        # Build a structured but basic initial draft
        # Deliberately lacks: depth, examples, transitions, and strong conclusion
        response = textwrap.dedent(f"""
        {topic} is something that is important and relevant today. There are several aspects to consider when thinking about this subject.

        First, we should understand the basics. {topic} involves various components that work together. People who study this field often note that it has many applications in real life.

        Second, there are some key points to keep in mind. The subject has evolved over time and continues to develop. Many experts have written about this topic and shared their perspectives.

        Third, practical considerations matter. When applying knowledge of {topic}, it helps to think carefully and consider different angles. Results can vary depending on the situation and context.

        In conclusion, {topic} is a broad area. There is always more to learn and explore on this subject.
        """).strip()

        return response

    def _extract_topic(self, prompt: str) -> str:
        """
        Extract a clean topic label from the user's prompt.
        
        Args:
            prompt (str): Raw user input.
        
        Returns:
            str: Short topic string.
        """
        # Remove common question starters for a cleaner topic label
        starters = [
            "explain", "describe", "what is", "what are", "how does", "how do",
            "tell me about", "give me", "write about", "discuss", "define",
            "can you explain", "please explain", "i want to know about"
        ]
        topic = prompt.strip()
        for starter in starters:
            if topic.lower().startswith(starter):
                topic = topic[len(starter):].strip()
                break

        # Trim punctuation and capitalize
        topic = topic.rstrip("?.!").strip()

        # If the extracted topic is still very long, take just the first concept
        if len(topic) > 60:
            for delimiter in [", covering", ", including", " to a ", " for a ", " in a ", ","]:
                if delimiter in topic:
                    topic = topic.split(delimiter)[0].strip()
                    break
            # Final fallback: truncate to first 6 words
            if len(topic) > 60:
                topic = " ".join(topic.split()[:6])

        if topic:
            topic = topic[0].upper() + topic[1:]

        return topic if topic else "This topic"

    # ──────────────────────────────────────────────────────────────────────────
    # API-Based Generation (Claude / OpenAI)
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_via_api(self, prompt: str) -> str:
        """
        Generate a response using the Anthropic Claude API.
        Falls back to OpenAI if Claude key is unavailable.
        
        Args:
            prompt (str): User's input.
        
        Returns:
            str: API-generated response.
        """
        # Try Anthropic Claude first
        if os.environ.get("ANTHROPIC_API_KEY"):
            return self._call_anthropic(prompt)
        
        # Fallback to OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            return self._call_openai(prompt)

        # If somehow we reach here, fall back to rule-based
        self.logger.warning("No valid API key found. Falling back to rule-based generation.")
        return self._generate_rule_based(prompt)

    def _call_anthropic(self, prompt: str) -> str:
        """
        Call the Anthropic Claude API to generate a response.
        
        Args:
            prompt (str): User's input.
        
        Returns:
            str: Claude's response.
        """
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            system_prompt = (
                "You are a knowledgeable assistant tasked with providing clear, "
                "informative, and well-structured responses. Generate a comprehensive "
                "initial response that covers the key aspects of the topic. "
                "Your response will be reviewed and improved in subsequent iterations."
            )

            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        except ImportError:
            self.logger.warning("'anthropic' package not installed. Run: pip install anthropic")
            return self._generate_rule_based(prompt)
        except Exception as e:
            self.logger.warning(f"Anthropic API error: {e}. Falling back to rule-based.")
            return self._generate_rule_based(prompt)

    def _call_openai(self, prompt: str) -> str:
        """
        Call the OpenAI API to generate a response.
        
        Args:
            prompt (str): User's input.
        
        Returns:
            str: OpenAI's response.
        """
        try:
            import openai
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a knowledgeable assistant. Generate a clear, "
                            "informative, and well-structured initial response. "
                            "Your response will be reviewed and improved iteratively."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024
            )
            return response.choices[0].message.content

        except ImportError:
            self.logger.warning("'openai' package not installed. Run: pip install openai")
            return self._generate_rule_based(prompt)
        except Exception as e:
            self.logger.warning(f"OpenAI API error: {e}. Falling back to rule-based.")
            return self._generate_rule_based(prompt)
