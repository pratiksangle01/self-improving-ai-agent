"""
Logger Utility
==============
Provides consistent, colorful, and structured terminal output for the
Self-Improving AI Agent system.

All output styling is centralized here so the rest of the codebase
can focus on logic rather than formatting.

Color Codes Used (ANSI escape sequences):
    CYAN    = Agent headers and banners
    GREEN   = Success messages and scores
    YELLOW  = Warnings and phase titles
    MAGENTA = Previews and details
    BLUE    = Info messages
    RED     = Errors
    BOLD    = Section headings
"""


class Logger:
    """
    Centralized terminal output handler with color and structure support.
    
    Uses ANSI escape codes for color. Falls back gracefully in terminals
    that don't support color (codes are invisible but text remains readable).
    """

    # ── ANSI Color Codes ─────────────────────────────────────────────────────
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    # Foreground colors
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"

    # ── Layout Constants ──────────────────────────────────────────────────────
    WIDTH = 70   # Terminal width for banners and dividers
    PREVIEW_LINES = 4  # Number of lines to show in response previews

    def banner(self):
        """Print the application welcome banner."""
        print()
        print(f"{self.CYAN}{self.BOLD}{'═' * self.WIDTH}{self.RESET}")
        print(f"{self.CYAN}{self.BOLD}  🤖  SELF-IMPROVING AI AGENT  v1.0{self.RESET}")
        print(f"{self.CYAN}{self.BOLD}  Autonomous Response Quality Optimizer{self.RESET}")
        print(f"{self.CYAN}{self.BOLD}{'═' * self.WIDTH}{self.RESET}")
        print()

    def footer(self):
        """Print the application footer."""
        print()
        print(f"{self.CYAN}{self.BOLD}{'═' * self.WIDTH}{self.RESET}")
        print(f"{self.CYAN}  ✅  Session Complete{self.RESET}")
        print(f"{self.CYAN}{self.BOLD}{'═' * self.WIDTH}{self.RESET}")
        print()

    def section(self, title: str):
        """
        Print a section header.
        
        Args:
            title (str): Section title text.
        """
        print()
        print(f"{self.BOLD}{self.WHITE}{'─' * self.WIDTH}{self.RESET}")
        print(f"{self.BOLD}{self.WHITE}  {title}{self.RESET}")
        print(f"{self.BOLD}{self.WHITE}{'─' * self.WIDTH}{self.RESET}")

    def divider(self):
        """Print a thin divider line."""
        print(f"{self.GRAY}{'· ' * (self.WIDTH // 2)}{self.RESET}")

    def phase(self, phase_label: str, description: str):
        """
        Print a phase marker (e.g., PHASE 1 / ITERATION 2).
        
        Args:
            phase_label (str): Short label like "PHASE 1" or "ITERATION 2"
            description (str): Description of what this phase does.
        """
        print()
        print(f"  {self.YELLOW}{self.BOLD}▶ {phase_label}{self.RESET}  {self.YELLOW}{description}{self.RESET}")
        print()

    def agent(self, agent_name: str, message: str):
        """
        Print a message from a named agent.
        
        Args:
            agent_name (str): Agent identifier (e.g., "GENERATOR")
            message (str): What the agent is doing.
        """
        colors = {
            "GENERATOR": self.BLUE,
            "CRITIC":    self.MAGENTA,
            "IMPROVER":  self.GREEN,
        }
        color = colors.get(agent_name.upper(), self.CYAN)
        badge = f"{color}{self.BOLD}[{agent_name}]{self.RESET}"
        print(f"  {badge} {message}")

    def success(self, message: str):
        """
        Print a success/positive message.
        
        Args:
            message (str): Success message.
        """
        print(f"  {self.GREEN}✓ {message}{self.RESET}")

    def info(self, message: str):
        """
        Print a neutral informational message.
        
        Args:
            message (str): Info message.
        """
        print(f"  {self.BLUE}ℹ {message}{self.RESET}")

    def warning(self, message: str):
        """
        Print a warning message.
        
        Args:
            message (str): Warning message.
        """
        print(f"  {self.YELLOW}⚠  {message}{self.RESET}")

    def error(self, message: str):
        """
        Print an error message.
        
        Args:
            message (str): Error message.
        """
        print(f"  {self.RED}✗ ERROR: {message}{self.RESET}")

    def detail(self, message: str):
        """
        Print a detailed/secondary message (dimmer styling).
        
        Args:
            message (str): Detail text.
        """
        print(f"  {self.GRAY}{message}{self.RESET}")

    def preview(self, text: str, max_lines: int = None):
        """
        Print a truncated preview of a long text (e.g., a generated response).
        
        Args:
            text (str): Full text to preview.
            max_lines (int): Override default line limit.
        """
        limit = max_lines or self.PREVIEW_LINES
        lines = text.strip().split('\n')
        preview_lines = lines[:limit]

        print()
        print(f"  {self.MAGENTA}{self.DIM}{'┄' * (self.WIDTH - 4)}{self.RESET}")
        for line in preview_lines:
            # Truncate very long lines
            display = (line[:self.WIDTH - 8] + "…") if len(line) > self.WIDTH - 8 else line
            print(f"  {self.MAGENTA}│ {self.RESET}{display}")
        if len(lines) > limit:
            print(f"  {self.GRAY}│  … ({len(lines) - limit} more lines){self.RESET}")
        print(f"  {self.MAGENTA}{self.DIM}{'┄' * (self.WIDTH - 4)}{self.RESET}")
        print()
