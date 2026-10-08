# ASD-STE100 verified: Short sentences. Direct imperative verbs.
import ast
import re
import unittest
from pathlib import Path


class TestThemeTokensConsistency(unittest.TestCase):
    """Verify that interactive_menu.py uses semantic theme tokens instead of bare color tags."""

    def test_no_bare_color_markup_in_interactive_menu(self):
        file_path = Path(__file__).resolve().parent.parent / "ctf_downloader" / "interactive_menu.py"
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Disallowed bare Rich markup color tags per AGENTS.md zero-hardcoding rule
        bare_color_pattern = re.compile(
            r"\[/?(bold )?(cyan|green|yellow|red|white|magenta|blue)\]",
            re.IGNORECASE,
        )

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                match = bare_color_pattern.search(node.value)
                if match:
                    violations.append((node.lineno, match.group(0), node.value))

        msg = (
            f"Found bare color tags in interactive_menu.py:\n"
            + "\n".join(f"Line {line}: {tag} in {text!r}" for line, tag, text in violations)
        )
        self.assertEqual(len(violations), 0, msg)
