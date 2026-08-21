from app.ai.context_builder import chunk_text


def test_chunk_text_splits_on_sentence_boundary():
    """With a small chunk_size, text should split at sentence ends."""
    text = "First sentence here. Second sentence here. Third sentence here."
    chunks = chunk_text(text, chunk_size=30, overlap=5)

    # Every chunk should end with a sentence terminator
    for chunk in chunks:
        assert chunk[-1] in ".!?"


def test_chunk_text_overlap_preserved():
    """Consecutive chunks should share overlapping text."""
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    chunks = chunk_text(text, chunk_size=40, overlap=10)

    if len(chunks) >= 2:
        # The end of chunk 0 should appear somewhere at the start of chunk 1
        tail = chunks[0][-10:]
        assert tail in chunks[1]


def test_chunk_text_no_data_loss():
    """Every sentence from the original should appear in at least one chunk."""
    text = "Alpha sentence. Beta sentence. Gamma sentence. Delta sentence."
    chunks = chunk_text(text, chunk_size=35, overlap=5)

    all_text = " ".join(chunks)
    assert "Alpha sentence." in all_text
    assert "Beta sentence." in all_text
    assert "Gamma sentence." in all_text
    assert "Delta sentence." in all_text


def test_chunk_text_empty_string():
    assert chunk_text("") == []


def test_chunk_text_single_long_sentence():
    """A sentence longer than chunk_size must not be dropped."""
    long_sentence = "A" * 1000 + "."
    chunks = chunk_text(long_sentence, chunk_size=100, overlap=10)

    assert len(chunks) > 0
    assert long_sentence in "".join(chunks)