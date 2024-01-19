DEFAULT_OPTIONS = {
    "numpy": {
        "allow_section_blank_line": True,
    }
}


def get_parser_defaults(name: str):
    return DEFAULT_OPTIONS.get(name, {})
