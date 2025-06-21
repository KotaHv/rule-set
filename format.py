from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Optional, Union
from dataclasses import dataclass, field
import ipaddress

RULE_TYPES = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-SET",
    "DOMAIN-WILDCARD",
    "IP-CIDR",
    "IP-CIDR6",
    "GEOIP",
    "IP-ASN",
    "USER-AGENT",
    "URL-REGEX",
    "PROCESS-NAME",
    "SUBNET",
    "DEST-PORT",
    "IN-PORT",
    "SRC-PORT",
    "SRC-IP",
    "PROTOCOL",
    "SCRIPT",
    "CELLULAR-RADIO",
    "DEVICE-NAME",
    "RULE-SET",
    "AND",
    "NOT",
    "OR",
]

COMMENTS = ["#", ";", "//"]


@dataclass(frozen=True)
class Rule:
    """Represents a rule item"""

    rule_type: str
    content: str
    is_commented: bool = False

    def __str__(self) -> str:
        rule_str = f"{self.rule_type},{self.content}"
        return f"# {rule_str}" if self.is_commented else rule_str

    def __hash__(self) -> int:
        # Deduplication ignores comment status, only considers type and content
        return hash((self.rule_type, self.content))

    def __eq__(self, other) -> bool:
        if not isinstance(other, Rule):
            return False
        return self.rule_type == other.rule_type and self.content == other.content


@dataclass
class Section:
    """Represents a rule section"""

    comment: Optional[str] = None
    rules: Set[Rule] = field(default_factory=set)

    def add_rule(self, rule: Rule) -> None:
        """Add rule with automatic deduplication"""
        # If same rule exists but with different comment status, keep non-commented version
        existing_rule = next((r for r in self.rules if r == rule), None)
        if existing_rule:
            if existing_rule.is_commented and not rule.is_commented:
                self.rules.remove(existing_rule)
                self.rules.add(rule)
        else:
            self.rules.add(rule)

    def has_content(self) -> bool:
        """Check if section has content"""
        return self.comment is not None or bool(self.rules)

    def get_sorted_rules(self) -> Dict[str, List[Rule]]:
        """Group and sort rules by type"""
        grouped: Dict[str, List[Rule]] = defaultdict(list)

        for rule in self.rules:
            grouped[rule.rule_type].append(rule)

        # Sort rules for each type
        for rule_type, rules in grouped.items():
            grouped[rule_type] = self._sort_rules_by_type(rule_type, rules)

        return dict(grouped)

    def _sort_rules_by_type(self, rule_type: str, rules: List[Rule]) -> List[Rule]:
        """Sort rules by type"""
        if rule_type == "IP-CIDR":
            return sorted(
                rules,
                key=lambda r: (
                    ipaddress.IPv4Network(r.content).network_address,
                    r.is_commented,
                ),
            )
        elif rule_type == "IP-CIDR6":
            return sorted(
                rules,
                key=lambda r: (
                    ipaddress.IPv6Network(r.content).network_address,
                    r.is_commented,
                ),
            )
        elif rule_type == "IP-ASN":
            return sorted(rules, key=lambda r: (int(r.content), r.is_commented))
        else:
            return sorted(rules, key=lambda r: (r.content.lower(), r.is_commented))


class Format:
    def __init__(self, filepath: Union[str, Path]) -> None:
        self.filepath = Path(filepath) if isinstance(filepath, str) else filepath
        self.sections: List[Section] = []
        self._original_count = 0

    def _read_file(self) -> List[str]:
        """Read file content"""
        with self.filepath.open(encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def _is_comment(self, line: str) -> bool:
        """Check if line is a comment"""
        return any(line.startswith(comment) for comment in COMMENTS)

    def _parse_rule(self, line: str, is_commented: bool = False) -> Optional[Rule]:
        """Parse rule line"""
        original_line = line

        if is_commented:
            # Remove comment symbols
            for comment in COMMENTS:
                if line.startswith(comment):
                    line = line[len(comment) :].strip()
                    break

        line = line.strip()
        if not line:
            return None

        parts = line.split(",", 1)
        if len(parts) < 2:
            raise ValueError(
                f"Invalid rule format: '{original_line}' - Rule must contain type and content separated by comma"
            )

        rule_type = parts[0].strip().upper()
        if rule_type not in RULE_TYPES:
            raise ValueError(
                f"Unknown rule type: '{rule_type} in '{original_line}' - Supported types: {', '.join(RULE_TYPES)}"
            )

        content = parts[1].strip()
        if not content:
            raise ValueError(f"Rule content cannot be empty: '{original_line}'")

        return Rule(rule_type=rule_type, content=content, is_commented=is_commented)

    def _parse_lines(self, lines: List[str]) -> None:
        """Parse all lines"""
        current_section = Section()

        for line in lines:
            if self._is_comment(line):
                # Try to parse as commented rule
                try:
                    rule = self._parse_rule(line, is_commented=True)
                    if rule:
                        current_section.add_rule(rule)
                        self._original_count += 1
                except ValueError:
                    # Parse failed means it's a regular comment, start new section
                    if current_section.has_content():
                        self.sections.append(current_section)
                    current_section = Section(comment=line)
            else:
                # Regular rule, parsing failure should raise error
                rule = self._parse_rule(line)
                if rule:
                    current_section.add_rule(rule)
                    self._original_count += 1

        # Add the last section
        if current_section.has_content():
            self.sections.append(current_section)

    def _generate_output(self) -> List[str]:
        """Generate output content"""
        output_lines: List[str] = []

        for i, section in enumerate(self.sections):
            # Add empty line between sections
            if i > 0:
                output_lines.append("")

            # Add comment
            if section.comment:
                output_lines.append(section.comment)

            # Output rules in RULE_TYPES order
            grouped_rules = section.get_sorted_rules()
            for rule_type in RULE_TYPES:
                if rule_type in grouped_rules:
                    for rule in grouped_rules[rule_type]:
                        output_lines.append(str(rule))

        return output_lines

    def _write_file(self, lines: List[str]) -> None:
        """Write to file"""
        with self.filepath.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _calculate_stats(self) -> None:
        """Calculate and print statistics"""
        rule_counts: Dict[str, int] = defaultdict(int)
        commented_counts: Dict[str, int] = defaultdict(int)
        total_rules = 0

        for section in self.sections:
            for rule in section.rules:
                if rule.is_commented:
                    commented_counts[rule.rule_type] += 1
                else:
                    rule_counts[rule.rule_type] += 1
                total_rules += 1

        duplicates_removed = self._original_count - total_rules

        print("=" * 50)
        print("Formatting completed!")
        print("=" * 50)
        print(f"Total rules: {total_rules}")
        print(f"Sections: {len(self.sections)}")
        print(f"Duplicates removed: {duplicates_removed}")

        if rule_counts:
            print("\nActive rules statistics:")
            for rule_type in sorted(rule_counts.keys()):
                print(f"  {rule_type}: {rule_counts[rule_type]}")

        if commented_counts:
            print("\nCommented rules statistics:")
            for rule_type in sorted(commented_counts.keys()):
                print(f"  {rule_type}: {commented_counts[rule_type]}")

        print("=" * 50)

    def format(self) -> None:
        """Main formatting method"""
        try:
            # Read and parse file
            lines = self._read_file()
            self._parse_lines(lines)

            # Generate output content
            output_lines = self._generate_output()

            # Write to file
            self._write_file(output_lines)

            # Print statistics
            self._calculate_stats()

        except Exception as e:
            print(f"Formatting failed: {e}")
            raise


if __name__ == "__main__":
    parent_dir = Path(__file__).parent
    for format_dir in [parent_dir / "my-rules", parent_dir / "sources"]:
        for pattern in ("*.txt", "*.list"):
            for filepath in format_dir.rglob(pattern):
                print(filepath)
                f = Format(filepath)
                f.format()
