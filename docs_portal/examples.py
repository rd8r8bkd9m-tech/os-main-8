"""Interactive example parsing and execution helpers."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List, Mapping

from docs_portal.safe_executor import safe_execute, SafeExecutionError


@dataclass(frozen=True, slots=True)
class Example:
    """Represents a runnable code snippet embedded in documentation."""

    identifier: str
    language: str
    code: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ExampleExecution:
    """Result of executing a documentation example."""

    stdout: str
    variables: Mapping[str, str]


class ExampleParser:
    """Extract ``Example`` entries from markdown payloads."""

    START_PREFIX = "```kolibri-example"
    END_MARKER = "```"
    SEPARATOR = "::"

    def __init__(self) -> None:
        self._header_re = re.compile(r"(?P<key>[\w-]+)=(?P<value>[\w:\-/._]+|\"[^\"]+\")")

    def parse(self, markdown: str, *, base_identifier: str) -> List[Example]:
        examples: List[Example] = []
        lines = markdown.splitlines()
        i = 0
        discovered = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith(self.START_PREFIX):
                header = line[len(self.START_PREFIX) :].strip()
                attributes = self._parse_attributes(header)
                language = attributes.get("language", "python")
                raw_identifier = attributes.get("id", str(discovered))
                description = attributes.get("description")
                buffer: List[str] = []
                i += 1
                while i < len(lines) and not lines[i].startswith(self.END_MARKER):
                    buffer.append(lines[i])
                    i += 1
                examples.append(
                    Example(
                        identifier=f"{base_identifier}{self.SEPARATOR}{raw_identifier}",
                        language=language,
                        code="\n".join(buffer).strip(),
                        description=description,
                    )
                )
                discovered += 1
            i += 1
        return examples

    def _parse_attributes(self, header: str) -> Dict[str, str]:
        attributes: Dict[str, str] = {}
        for match in self._header_re.finditer(header):
            value = match.group("value")
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            attributes[match.group("key")] = value
        return attributes


class ExampleExecutor:
    """Execute runnable examples in a controlled environment."""

    def execute(self, example: Example) -> ExampleExecution:
        """Execute an example safely using AST-based validation.
        
        Args:
            example: Example to execute
            
        Returns:
            ExampleExecution with stdout and variables
            
        Raises:
            ValueError: If example language is not Python
            SafeExecutionError: If code contains unsafe operations
        """
        if example.language.lower() != "python":
            raise ValueError("Only Python examples are executable in the portal")
        
        # Use safe execution instead of direct exec()
        try:
            stdout, variables = safe_execute(
                example.code,
                timeout=5,
                max_output_size=10000
            )
        except SafeExecutionError as e:
            # Return error in output instead of crashing
            return ExampleExecution(
                stdout=f"❌ Execution Error: {str(e)}",
                variables={}
            )
        
        return ExampleExecution(stdout=stdout, variables=variables)
