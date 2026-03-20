"""
Loop Controller
===============
The brain of the Self-Improving AI Agent system.

Orchestrates the full improvement pipeline:
  1. Generator creates initial response
  2. Critic evaluates and scores it
  3. If score < threshold and iterations remain → Improver refines it
  4. Critic re-evaluates the improved response
  5. Repeat until quality threshold is met or max iterations reached
  6. Save full history to output/history.json

The controller maintains a complete audit trail of all iterations,
scores, feedback, and responses.
"""

import json
import os
import time
from datetime import datetime

from agents.generator_agent import GeneratorAgent
from agents.critic_agent import CriticAgent
from agents.improver_agent import ImproverAgent
from utils.logger import Logger


class LoopController:
    """
    Orchestrates the multi-agent self-improvement loop.
    
    Attributes:
        mode (str): 'rule' or 'api'
        max_iterations (int): Maximum improvement cycles to run
        quality_threshold (float): Score at which to stop early (0-10)
        api_key (str): Optional API key
        logger (Logger): Shared logger instance
        history (list): Stores all iteration data
    """

    # Path to save the improvement history
    HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "history.json")

    def __init__(self, mode="rule", max_iterations=3, quality_threshold=8.0, api_key=None):
        """
        Initialize the LoopController with all agents.
        
        Args:
            mode (str): Operating mode.
            max_iterations (int): Max improvement iterations.
            quality_threshold (float): Stop early if score exceeds this.
            api_key (str): Optional API key.
        """
        self.mode = mode
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.api_key = api_key
        self.logger = Logger()
        self.history = []

        # Instantiate all agents with shared mode and api_key
        self.generator = GeneratorAgent(mode=mode, api_key=api_key)
        self.critic    = CriticAgent(mode=mode, api_key=api_key)
        self.improver  = ImproverAgent(mode=mode, api_key=api_key)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.HISTORY_FILE), exist_ok=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Main Orchestration
    # ──────────────────────────────────────────────────────────────────────────

    def run(self, prompt: str) -> dict:
        """
        Run the full self-improvement loop for a given prompt.
        
        Pipeline:
            Generate → Evaluate → [Improve → Evaluate] × N
        
        Args:
            prompt (str): The user's question or topic.
        
        Returns:
            dict: {
                'final_response': str,
                'final_score': float,
                'iterations_run': int,
                'history': list
            }
        """
        self.logger.section("STARTING IMPROVEMENT LOOP")
        self.logger.info(f"Prompt: \"{prompt}\"")
        self.logger.info(f"Mode: {self.mode.upper()}  |  Max Iterations: {self.max_iterations}  |  Threshold: {self.quality_threshold}/10")
        self.logger.divider()

        session_start = time.time()
        self.history = []

        # ── Step 1: Generate Initial Response ─────────────────────────────
        self.logger.phase("PHASE 1", "Initial Generation")
        current_response = self.generator.generate(prompt)
        self.logger.preview(current_response)

        # ── Step 2: Initial Evaluation ────────────────────────────────────
        self.logger.phase("PHASE 2", "Initial Evaluation")
        critique = self.critic.evaluate(current_response, prompt)
        current_score = critique["overall_score"]

        # Record iteration 0 (the initial version)
        self._record_iteration(
            iteration=0,
            label="Initial Response",
            response=current_response,
            critique=critique,
            improvement_applied=None
        )

        # ── Step 3: Improvement Loop ──────────────────────────────────────
        iterations_run = 0

        for i in range(1, self.max_iterations + 1):
            # Check if we've already hit the quality threshold
            if current_score >= self.quality_threshold:
                self.logger.success(
                    f"Quality threshold reached ({current_score:.1f} ≥ {self.quality_threshold})! "
                    f"Stopping early after {iterations_run} improvement iteration(s)."
                )
                break

            self.logger.divider()
            self.logger.phase(f"ITERATION {i}", f"Improvement Cycle")

            # ── Improve ───────────────────────────────────────────────────
            improved_response = self.improver.improve(
                response=current_response,
                critique=critique,
                prompt=prompt,
                iteration=i
            )

            # ── Re-Evaluate ───────────────────────────────────────────────
            self.logger.agent("CRITIC", f"Re-evaluating improved response...")
            new_critique = self.critic.evaluate(improved_response, prompt)
            new_score = new_critique["overall_score"]

            # Compute score delta
            delta = new_score - current_score
            delta_str = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
            self.logger.info(f"Score change: {current_score:.1f} → {new_score:.1f} ({delta_str})")

            # Record this iteration
            self._record_iteration(
                iteration=i,
                label=f"Iteration {i}",
                response=improved_response,
                critique=new_critique,
                improvement_applied=critique["feedback"]
            )

            # Update current state
            current_response = improved_response
            current_score = new_score
            critique = new_critique
            iterations_run = i

            self.logger.preview(current_response)

        # ── Step 4: Save History & Return ────────────────────────────────
        elapsed = time.time() - session_start
        self._save_history(prompt, elapsed)

        self.logger.divider()
        self.logger.info(f"Loop complete in {elapsed:.1f}s | Final score: {current_score:.1f}/10 | {iterations_run} improvement cycle(s) run")

        return {
            "final_response": current_response,
            "final_score": current_score,
            "iterations_run": iterations_run,
            "history": self.history,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # History Management
    # ──────────────────────────────────────────────────────────────────────────

    def _record_iteration(
        self,
        iteration: int,
        label: str,
        response: str,
        critique: dict,
        improvement_applied
    ):
        """
        Record a snapshot of this iteration to the history list.
        
        Args:
            iteration (int): 0 = initial, 1+ = improvement cycles
            label (str): Human-readable label (e.g., "Iteration 2")
            response (str): The response text at this iteration
            critique (dict): The critic's evaluation
            improvement_applied: Feedback list used to generate this version (None for initial)
        """
        entry = {
            "iteration": iteration,
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "response": response,
            "word_count": len(response.split()),
            "scores": critique["scores"],
            "overall_score": critique["overall_score"],
            "strengths": critique.get("strengths", []),
            "weaknesses": critique.get("weaknesses", []),
            "feedback": critique.get("feedback", []),
            "improvement_applied": improvement_applied,
        }
        self.history.append(entry)

    def _save_history(self, prompt: str, elapsed_seconds: float):
        """
        Serialize and write the full session history to a JSON file.
        
        The file is human-readable and useful for reviewing improvements.
        
        Args:
            prompt (str): Original user prompt.
            elapsed_seconds (float): Total time taken for the session.
        """
        session_data = {
            "session_metadata": {
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "mode": self.mode,
                "max_iterations": self.max_iterations,
                "quality_threshold": self.quality_threshold,
                "total_iterations": len(self.history),
                "elapsed_seconds": round(elapsed_seconds, 2),
                "initial_score": self.history[0]["overall_score"] if self.history else None,
                "final_score": self.history[-1]["overall_score"] if self.history else None,
            },
            "iterations": self.history,
        }

        try:
            with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"History saved → {self.HISTORY_FILE}")
        except Exception as e:
            self.logger.warning(f"Could not save history: {e}")
