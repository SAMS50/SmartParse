"""Unified integration layer; original SmartParse and research APIs are unchanged."""
__version__ = '0.9.0'


def analyze(source, **options):
    """Analyze one C translation unit without executing or rewriting it."""
    from .engine import analyze as implementation
    return implementation(source, **options)
