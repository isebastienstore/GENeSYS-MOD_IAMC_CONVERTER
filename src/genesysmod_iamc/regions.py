"""Region normalization helpers used by the active converter."""


def compact_connection(value):
    """Write a shared connection hierarchy only once."""
    origin, separator, destination = str(value).partition(">")
    if separator and "|" in origin:
        hierarchy = origin.rsplit("|", 1)[0] + "|"
        if destination.startswith(hierarchy):
            destination = destination[len(hierarchy):]
    return origin + separator + destination


def normalize_region(value, prefix):
    """Prefix native regions and compact directional connections."""
    value = str(value).strip()
    if not prefix or value in {"", "World", prefix}:
        return value
    if ">" in value:
        parts = (normalize_region(part, prefix) for part in value.split(">"))
        return compact_connection(">".join(parts))
    return value if "|" in value else f"{prefix}|{value}"
