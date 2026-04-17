DEFAULT_OPTIONS = {
    "numpy": {
    }
}


def get_parser_defaults(name: str):
    return DEFAULT_OPTIONS.get(name, {})
