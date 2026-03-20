"""
Self-Improving AI Agent - Main Entry Point
==========================================
This is the main entry point for the Self-Improving AI Agent system.
Run this file to start the interactive improvement loop.

Usage:
    python main.py                    # Interactive mode (prompts for input)
    python main.py --mode rule        # Force rule-based mode
    python main.py --mode api         # Force API mode (requires API key)
    python main.py --demo             # Run with a built-in demo prompt
"""

import argparse
import os
import sys

# Add project root to path so all modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.loop_controller import LoopController
from utils.logger import Logger


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Self-Improving AI Agent - Iterative Response Optimizer"
    )
    parser.add_argument(
        "--mode",
        choices=["rule", "api"],
        default=None,
        help="Operating mode: 'rule' (no API needed) or 'api' (uses Claude/OpenAI)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Maximum number of improvement iterations (default: 3)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a built-in demo without interactive input"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=8.0,
        help="Quality score threshold to stop early (0-10, default: 8.0)"
    )
    return parser.parse_args()


def select_mode(forced_mode=None):
    """
    Determine whether to use rule-based or API mode.
    
    Args:
        forced_mode: If provided, skip interactive selection.
    
    Returns:
        str: 'rule' or 'api'
    """
    if forced_mode:
        return forced_mode

    logger = Logger()
    logger.section("MODE SELECTION")
    print("  [1] Rule-Based Mode  (no API key required, simulated logic)")
    print("  [2] API Mode         (uses Claude Anthropic API)")
    print()

    while True:
        choice = input("  Select mode (1 or 2): ").strip()
        if choice == "1":
            return "rule"
        elif choice == "2":
            return "api"
        else:
            print("  ⚠  Please enter 1 or 2.")


def get_user_prompt(demo_mode=False):
    """
    Get the user's input prompt.
    
    Args:
        demo_mode: If True, return a pre-set demo prompt.
    
    Returns:
        str: The user's topic/question.
    """
    if demo_mode:
        demo_prompt = (
            "Explain the concept of machine learning to a complete beginner, "
            "covering what it is, how it works, and why it matters."
        )
        print(f"\n  📋 Demo prompt: \"{demo_prompt}\"\n")
        return demo_prompt

    logger = Logger()
    logger.section("INPUT")
    print("  Enter the topic or question you want the AI to respond to.")
    print("  (Press Enter twice or type 'END' on a new line to finish multi-line input)\n")

    lines = []
    while True:
        line = input("  > ")
        if line.strip().upper() == "END":
            break
        lines.append(line)
        # Allow single-line input with just Enter
        if len(lines) == 1 and line.strip():
            # Check if next line is empty (user pressed Enter again)
            follow_up = input("  > (press Enter to confirm, or continue typing) ")
            if follow_up.strip() == "":
                break
            lines.append(follow_up)

    prompt = " ".join(lines).strip()
    if not prompt:
        print("  ⚠  No input provided. Using default demo prompt.")
        return "Explain the importance of clean code in software development."
    return prompt


def main():
    """Main function - orchestrates the entire self-improving agent flow."""
    args = parse_args()
    logger = Logger()

    # ── Welcome Banner ──────────────────────────────────────────────────────
    logger.banner()

    # ── Mode Selection ──────────────────────────────────────────────────────
    mode = select_mode(args.mode)
    logger.info(f"Operating Mode: {mode.upper()}")

    # ── API Key Check (for API mode) ─────────────────────────────────────────
    api_key = None
    if mode == "api":
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning(
                "No API key found in environment variables.\n"
                "  Set ANTHROPIC_API_KEY or OPENAI_API_KEY, or switching to rule-based mode."
            )
            mode = "rule"
            logger.info("Falling back to Rule-Based Mode.")

    # ── Get User Prompt ──────────────────────────────────────────────────────
    user_prompt = get_user_prompt(demo_mode=args.demo)

    # ── Initialize and Run Controller ───────────────────────────────────────
    controller = LoopController(
        mode=mode,
        max_iterations=args.iterations,
        quality_threshold=args.threshold,
        api_key=api_key
    )

    result = controller.run(user_prompt)

    # ── Final Summary ────────────────────────────────────────────────────────
    logger.section("FINAL RESULT")
    logger.success(f"Best response achieved (Score: {result['final_score']:.1f}/10):")
    print()
    print(result["final_response"])
    print()
    logger.info(f"Total iterations completed: {result['iterations_run']}")
    logger.info(f"History saved to: output/history.json")
    logger.footer()


if __name__ == "__main__":
    main()
