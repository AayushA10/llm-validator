def normalize_county_name(s: str) -> str:
    if s is None:
        return ""
    s = s.strip().lower()
    s = s.replace(".", "")
    s = " ".join(s.split())
    return s


def resolve_county_alias(normalized: str) -> str:
    aliases = {
        "s clara": "santa clara"
    }
    return aliases.get(normalized, normalized)