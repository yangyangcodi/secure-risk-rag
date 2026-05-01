from app.services.chunker import chunk_text


def test_short_text_single_chunk():
    text = "This is a short sentence."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_empty_text_returns_empty():
    assert chunk_text("") == []


def test_long_text_creates_multiple_chunks():
    # 600 words → should produce more than 1 chunk with chunk_size=512
    text = " ".join(["word"] * 600)
    chunks = chunk_text(text, chunk_size=512, overlap=64)
    assert len(chunks) > 1


def test_overlap_is_applied():
    # 20 words, chunk_size=10, overlap=3 → chunks start at 0, 7, 14
    words = [str(i) for i in range(20)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=10, overlap=3)
    # Second chunk should start with word at index 7
    assert chunks[1].startswith("7")


def test_no_empty_chunks():
    text = " ".join(["word"] * 100)
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert all(len(c) > 0 for c in chunks)
