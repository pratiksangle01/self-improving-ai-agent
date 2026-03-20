# 🤖 Self-Improving AI Agent

> **Autonomous Response Quality Optimizer** — A multi-agent system that generates, critiques, and iteratively improves its own output until a high-quality result is achieved.

---

## 🧠 What It Does

This system demonstrates core AI concepts like **self-reflection**, **iterative improvement**, and **autonomous quality optimization** using a pipeline of three specialized agents:

```
User Prompt
    │
    ▼
┌──────────────┐
│  GENERATOR   │  ← Creates initial response
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    CRITIC    │  ← Evaluates quality (0–10) across 5 dimensions
└──────┬───────┘
       │
       ├── Score ≥ threshold? → STOP ✅
       │
       ▼
┌──────────────┐
│   IMPROVER   │  ← Refines response based on critic feedback
└──────┬───────┘
       │
       └── Loop back to CRITIC (up to N iterations)
```

---

## 📁 Project Structure

```
self-improving-ai-agent/
├── main.py                    ← Entry point — run this
├── agents/
│   ├── __init__.py
│   ├── generator_agent.py     ← Produces initial response
│   ├── critic_agent.py        ← Scores and critiques responses
│   └── improver_agent.py      ← Applies targeted improvements
├── core/
│   ├── __init__.py
│   └── loop_controller.py     ← Orchestrates the full pipeline
├── utils/
│   ├── __init__.py
│   └── logger.py              ← Colorful terminal output
├── output/
│   └── history.json           ← Auto-generated improvement log
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone / Download the project

```bash
cd self-improving-ai-agent
```

### 2. Install dependencies

**Rule-Based Mode** (no API key needed — works out of the box):
```bash
# No installation needed! Python standard library only.
python main.py --mode rule --demo
```

**API Mode** (optional — for real AI-powered improvement):
```bash
pip install anthropic          # For Claude
# OR
pip install openai             # For OpenAI

export ANTHROPIC_API_KEY=your_key_here
python main.py --mode api
```

---

## 💻 Usage

```bash
# Interactive mode (prompts for mode and input)
python main.py

# Rule-based mode with a demo prompt
python main.py --mode rule --demo

# API mode with custom settings
python main.py --mode api --iterations 5 --threshold 8.5

# Force 2 iterations, stop at score 7.0
python main.py --mode rule --iterations 2 --threshold 7.0
```

### Command-Line Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `--mode` | `rule` or `api` | Interactive | Operating mode |
| `--iterations` | int | `3` | Max improvement cycles |
| `--threshold` | float | `8.0` | Quality score to stop early |
| `--demo` | flag | off | Use built-in demo prompt |

---

## 📊 Scoring System

The **Critic Agent** evaluates responses across **5 dimensions**, each scored 0–10:

| Dimension | Weight | What it measures |
|---|---|---|
| **Completeness** | 30% | Coverage, depth, word count |
| **Clarity** | 25% | Readability, sentence variety, absence of vague language |
| **Logic** | 20% | Structure, transitions, sound reasoning |
| **Specificity** | 15% | Examples, statistics, concrete details |
| **Tone** | 10% | Professional language, appropriate register |

**Final Score** = Weighted average of all dimensions

**Grade Scale:**
- A+ (9.0–10.0) — Exceptional
- A  (8.0–8.9)  — High Quality ← default stop threshold
- B  (7.0–7.9)  — Good
- C  (6.0–6.9)  — Acceptable
- D  (5.0–5.9)  — Needs Work
- F  (0–4.9)    — Poor

---

## 📋 Example Output

```
══════════════════════════════════════════════════════════════════════
  🤖  SELF-IMPROVING AI AGENT  v1.0
  Autonomous Response Quality Optimizer
══════════════════════════════════════════════════════════════════════

──────────────────────────────────────────────────────────────────────
  STARTING IMPROVEMENT LOOP
──────────────────────────────────────────────────────────────────────
  ℹ Prompt: "Explain machine learning to a complete beginner..."
  ℹ Mode: RULE  |  Max Iterations: 3  |  Threshold: 8.0/10

  ▶ PHASE 1  Initial Generation

  [GENERATOR] Creating initial response...
  ✓ Initial response generated (94 words)

  ▶ PHASE 2  Initial Evaluation

  [CRITIC] Evaluating response quality...
  ✓ Evaluation complete — Score: 4.8/10 (D)
     Clarity        [████░░░░░░]  4.5/10
     Completeness   [███░░░░░░░]  3.5/10
     Logic          [████░░░░░░]  4.5/10
     Tone           [█████░░░░░]  5.0/10
     Specificity    [███░░░░░░░]  3.0/10

  ▶ ITERATION 1  Improvement Cycle

  [IMPROVER] Applying improvements (iteration 1)...
  ✓ Improvement applied — 94 → 287 words (+193)

  [CRITIC] Re-evaluating improved response...
  ✓ Evaluation complete — Score: 7.2/10 (B)
  ℹ Score change: 4.8 → 7.2 (+2.40)

  ▶ ITERATION 2  Improvement Cycle

  [IMPROVER] Applying improvements (iteration 2)...
  ✓ Improvement applied — 287 → 412 words (+125)

  [CRITIC] Re-evaluating improved response...
  ✓ Evaluation complete — Score: 8.1/10 (A)
  ℹ Score change: 7.2 → 8.1 (+0.90)

  ✓ Quality threshold reached (8.1 ≥ 8.0)! Stopping early.

──────────────────────────────────────────────────────────────────────
  FINAL RESULT
──────────────────────────────────────────────────────────────────────
  ✓ Best response achieved (Score: 8.1/10):

  [Improved response printed here...]

  ℹ Total iterations completed: 2
  ℹ History saved to: output/history.json
```

---

## 📂 Output: history.json

Every session saves a complete audit trail:

```json
{
  "session_metadata": {
    "timestamp": "2024-01-15T14:32:10.123456",
    "prompt": "Explain machine learning...",
    "mode": "rule",
    "initial_score": 4.8,
    "final_score": 8.1,
    "total_iterations": 3
  },
  "iterations": [
    {
      "iteration": 0,
      "label": "Initial Response",
      "overall_score": 4.8,
      "scores": {"clarity": 4.5, "completeness": 3.5, ...},
      "weaknesses": ["Response is too brief (94 words)..."],
      "response": "..."
    },
    {
      "iteration": 1,
      "label": "Iteration 1",
      "overall_score": 7.2,
      ...
    }
  ]
}
```

---

## 🔧 Extending the System

### Add a new scoring dimension (Critic Agent)
1. Add key to `WEIGHTS` dict in `critic_agent.py` (ensure weights sum to 1.0)
2. Add scoring logic in `_evaluate_rule_based()`
3. Add feedback logic in `_generate_feedback()`

### Add a new improvement strategy (Improver Agent)
1. Add a case to `_apply_fix()` matching your new dimension
2. Implement `_fix_<your_dimension>()` method

### Swap in a different AI model (API mode)
- Edit `_call_anthropic()` in both `generator_agent.py` and `critic_agent.py`
- Change the `model=` parameter to your preferred model

---

## 🧩 Architecture: Dual Mode Design

```
┌────────────────────────────────────────────────────────┐
│                    LoopController                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Generator   │  │    Critic    │  │   Improver   │ │
│  │              │  │              │  │              │ │
│  │  Rule Mode:  │  │  Rule Mode:  │  │  Rule Mode:  │ │
│  │  Templates + │  │  Heuristics  │  │  Pattern-    │ │
│  │  heuristics  │  │  + metrics   │  │  based fixes │ │
│  │              │  │              │  │              │ │
│  │  API Mode:   │  │  API Mode:   │  │  API Mode:   │ │
│  │  Claude/GPT  │  │  Structured  │  │  Guided      │ │
│  │  completion  │  │  JSON eval   │  │  rewriting   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────────────────────────────────────────┘
```

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

*Built to demonstrate AI concepts: self-reflection, iterative improvement, and autonomous quality optimization.*
