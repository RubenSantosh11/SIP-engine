"""Evidence-span verification: every coded value must quote the source verbatim."""
from sip.common import normalise


def span_in_text(span: str | None, text: str) -> bool:
    """True if the span appears in the text after whitespace + case normalisation only."""
    if not span or not span.strip():
        return False
    return normalise(span) in normalise(text)
