import json
import sys
from pathlib import Path

import tinycss2


# These at-rules contain nested CSS rules.
GROUPING_AT_RULES = {
    "media",
    "supports",
    "layer",
    "container",
    "document",
}


def parse_css(css_text):
    """
    Convert CSS source text into structured Python dictionaries.
    Extract selectors, declarations, source lines and media context.
    """

    stylesheet = tinycss2.parse_stylesheet(
        css_text,
        skip_comments=True,
        skip_whitespace=True,
    )

    results = []

    def process_rules(rules, context=None):
        for rule in rules:

            # Handle @media, @supports, and similar grouping rules.
            if rule.type == "at-rule":
                if (
                    rule.lower_at_keyword in GROUPING_AT_RULES
                    and rule.content is not None
                ):
                    condition = tinycss2.serialize(rule.prelude).strip()

                    nested_context = (
                        f"@{rule.at_keyword} {condition}"
                    )

                    process_rules(
                        tinycss2.parse_rule_list(
                            rule.content,
                            skip_comments=True,
                            skip_whitespace=True,
                        ),
                        context=nested_context,
                    )

                # Other at-rules are intentionally not extracted.
                continue

            # Ignore invalid or unexpected top-level syntax.
            if rule.type != "qualified-rule":
                continue

            selector = tinycss2.serialize(rule.prelude).strip()

            declarations = tinycss2.parse_declaration_list(
                rule.content,
                skip_comments=True,
                skip_whitespace=True,
            )

            properties = []

            for declaration in declarations:
                if declaration.type != "declaration":
                    continue

                properties.append({
                    "property": declaration.name,
                    "value": tinycss2.serialize(
                        declaration.value
                    ).strip(),
                    "important": declaration.important,
                })

            results.append({
                "selector": selector,
                "line": rule.source_line,
                "context": context,
                "declarations": properties,
            })

    process_rules(stylesheet)

    return results


def main():
    # Use a supplied filename or default to sample.css.
    css_file = Path(
        sys.argv[1] if len(sys.argv) > 1 else "sample.css"
    )

    if not css_file.is_file():
        print(f"Error: CSS file not found: {css_file}")
        sys.exit(1)

    try:
        css_text = css_file.read_text(encoding="utf-8")
        parsed_data = parse_css(css_text)

        output_file = Path("parsed_output.json")
        output_file.write_text(
            json.dumps(parsed_data, indent=2),
            encoding="utf-8",
        )

        print(json.dumps(parsed_data, indent=2))
        print(f"\nSaved structured output to {output_file}")

    except (OSError, UnicodeError) as error:
        print(f"Error reading or processing the file: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
