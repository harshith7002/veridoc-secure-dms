def chunk_text(text: str, max_words: int = 200, overlap_words: int = 30) -> list[str]:
    """Splits on whitespace into overlapping word windows. Overlap means a fact split across
    a chunk boundary (e.g. a name mentioned right at the cut point) still appears whole in at
    least one chunk, instead of being silently lost from search."""
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [text.strip()]

    chunks = []
    start = 0
    step = max_words - overlap_words
    while start < len(words):
        chunk_words = words[start:start + max_words]
        chunks.append(" ".join(chunk_words))
        if start + max_words >= len(words):
            break
        start += step
    return chunks
