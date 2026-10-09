"""
pdf_chunker.py — a tutorial-commented PDF -> RAG chunk pipeline.

Usage:
    python pdf_chunker.py input.pdf --out chunks.jsonl --chunk-size 500 --overlap 75

Each line of chunks.jsonl is one JSON chunk record:
    {"id": "...", "text": "...", "page_start": 3, "page_end": 3,
     "token_count": 487, "source": "input.pdf"}

This file is written to be read top-to-bottom as a mini-course on PDF
parsing for RAG, not just as a tool. The comments explain *why* each
step exists, what can go wrong, and where you'd extend it toward
semantic chunking. Skip the prose once you know it; it's here so you
can come back to it.
"""

# =====================================================================
# PART 0 — Why PDF parsing is harder than it looks
# =====================================================================
#
# A PDF is not a text file with formatting on top (like .docx or HTML).
# It's a page-description format: a list of drawing instructions —
# "place glyph 'T' at x=72.0, y=710.3 using font Helvetica-Bold 14pt",
# repeated for every character on the page. There is no <p> tag, no
# reading order, no concept of "this is a heading" or "this is a table
# cell" baked into the format. Two consequences matter a lot for RAG:
#
# 1. "Extracting text" really means: collect glyphs + their (x, y)
#    positions, then *infer* reading order and word/line boundaries
#    from geometry (glyphs that are close together and roughly on the
#    same baseline get grouped into a word/line). This inference is
#    where most extraction bugs come from — multi-column layouts,
#    headers/footers interleaved with body text, and tables are all
#    cases where "sort by position" gets the order wrong.
#
# 2. There's no ground truth for structure. Headings are usually just
#    "bigger/bolder font", not a semantic tag. If you need structure
#    (headings, tables, reading order across columns) you either lean
#    on font-size/position heuristics yourself, or reach for a layout
#    model (e.g. unstructured.io, LayoutParser, or a vision-based
#    parser) that's been trained to recognize these patterns visually.
#
# This script uses pdfplumber, which does the geometric grouping for
# you (glyphs -> words -> lines) and exposes each character's
# position if you ever want to build your own layout heuristics on
# top. pypdf (used elsewhere in the docx/pdf toolchain) is faster but
# does *less* geometric reasoning, so it's fine for simple single-
# column PDFs but degrades faster on complex layouts.

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import pdfplumber

# ---------------------------------------------------------------------
# PART 1 — Token counting
# ---------------------------------------------------------------------
# Chunk *size* limits in RAG pipelines are almost always token limits
# (your embedding model has a max input length, e.g. 8191 tokens for
# OpenAI text-embedding-3, and your LLM's context window is priced and
# limited in tokens too) — not character or word limits. A token is
# roughly a sub-word unit produced by the model's tokenizer (e.g. BPE);
# "chunking" -> ["chunk", "ing"] is a typical split. Counting tokens
# instead of characters matters because token-to-character ratio
# varies a lot: dense code or CJK text can be ~1 token per character,
# while normal English prose is closer to 1 token per 4 characters.
#
# tiktoken is OpenAI's tokenizer library and cl100k_base is the
# encoding used by GPT-4/3.5 and OpenAI's embedding models — a
# reasonable default even if you're not using OpenAI, since most
# modern tokenizers land in a similar ballpark for English text. Its
# encoding tables are downloaded on first use, so we fall back to a
# word-count heuristic (~1.3 tokens/word for English) when there's no
# network access. Swap in your actual embedding model's tokenizer
# (e.g. `AutoTokenizer` from `transformers` for an open-source model)
# if you need exact counts.
try:
    import tiktoken

    ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:
    ENCODING = None


def count_tokens(text: str) -> int:
    if ENCODING is not None:
        return len(ENCODING.encode(text))
    return int(len(text.split()) * 1.3)


@dataclass
class Chunk:
    id: str
    text: str
    page_start: int
    page_end: int
    token_count: int
    source: str
    # Extend this dataclass as you go deeper: a `section_title` field
    # once you add heading detection, a `bbox` field if you track
    # where on the page the text sat (useful for highlighting the
    # source region in a UI), etc.


# =====================================================================
# PART 2 — Extraction
# =====================================================================

def extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...], 1-indexed, skipping empty pages.

    page.extract_text() is pdfplumber doing the glyph -> word -> line ->
    paragraph inference described in PART 0. Under the hood it clusters
    characters by y-position into lines, then by x-gap into words, using
    tunable tolerances (x_tolerance, y_tolerance) you can pass in if the
    default grouping misreads your PDF's spacing.

    Worth exploring on your own PDFs:
        page.extract_words()   -> list of words with bounding boxes
        page.chars              -> every character with x0/x1/top/bottom
        page.extract_tables()   -> table detection via ruling lines/gaps
    Printing page.chars for a tricky page is the fastest way to see
    *why* extraction went wrong on a given document.
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = clean_text(text)
            if text.strip():
                pages.append((i, text))
    return pages


def clean_text(text: str) -> str:
    """Fix common PDF-extraction artifacts before chunking.

    Why these specific fixes:

    - De-hyphenation: PDFs hard-wrap justified text, so a word at a
      line boundary is often split with a visible hyphen ("informa-\\n
      tion"). Left alone, this pollutes your embeddings with fake
      tokens like "informa-" and breaks keyword/BM25 search for
      "information". The regex only merges hyphen+newline pairs
      between two word characters, so it won't eat genuine hyphenated
      words like "state-of-the-art" that don't sit at a line break.

    - Line-wrap collapsing: extract_text() preserves each visual line
      as its own "\\n", including mid-sentence wraps. We collapse
      single newlines to spaces so a sentence reads as one line, but
      *keep* double newlines, which pdfplumber tends to emit at real
      paragraph gaps (extra vertical whitespace) — that distinction is
      what split_into_units() below relies on to find paragraph
      boundaries.

    - Whitespace collapsing: justified text and table remnants can
      leave runs of spaces/tabs; collapsed for cleanliness.

    This is intentionally conservative. Two things it does NOT handle,
    which are worth trying on messy real-world PDFs:
      * headers/footers/page numbers repeating on every page (strip by
        detecting text that recurs at the same position across pages)
      * ligatures / encoding glitches from bad font embedding (e.g. "fi"
        rendering as a private-use-area codepoint) — a symptom that a
        PDF needs OCR instead of direct text extraction.
    """
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# =====================================================================
# PART 3 — Chunking strategies
# =====================================================================
#
# There's a spectrum of chunking strategies, roughly in order of
# effort vs. retrieval quality:
#
#   1. Fixed-size splitting: cut every N characters/tokens, ignoring
#      content. Simple, fast, but routinely slices sentences and even
#      words in half, which hurts embedding quality (an embedding of a
#      half-sentence is a noisy representation of nothing in
#      particular) and looks bad in retrieved snippets shown to users.
#
#   2. Recursive / structure-aware splitting (what this script does):
#      respect natural boundaries — paragraphs, then sentences, then
#      words — as a fallback hierarchy, packing units up to a token
#      budget. This is the "recursive character/text splitter" pattern
#      popularized by LangChain. It's cheap (no model calls) and
#      avoids mid-sentence cuts almost always.
#
#   3. Semantic chunking: split where *meaning* shifts, not just where
#      punctuation allows it. A long document section can be one
#      grammatically-fine paragraph that actually covers two unrelated
#      topics (or vice versa: many short paragraphs that are one
#      continuous idea) — structure-aware splitting can't see that,
#      only an embedding of the content can. This is the natural next
#      step for you to build; see the stub and notes at the bottom of
#      this file.
#
#   4. Layout/structure-driven chunking: use detected headings/sections
#      (from font-size heuristics or a layout model) as hard chunk
#      boundaries, so a chunk never spans two sections. Often combined
#      with #2 or #3 *within* each section.
#
# This script implements #2, with pointers to #3.


def split_into_units(text: str) -> list[str]:
    """Split page text into paragraph-level units, falling back to
    sentences for any paragraph that's unusually long (>300 tokens) —
    a long paragraph would otherwise force a mid-paragraph cut later
    with no natural boundary to cut on.

    The sentence split here is a regex lookbehind for ., !, ? followed
    by whitespace — good enough for most prose, but it *will*
    misfire on abbreviations ("Dr. Smith"), decimal numbers ("3.14"),
    and ellipses. A more robust version would use a real sentence
    tokenizer (`nltk.sent_tokenize`, or spaCy's sentencizer) which
    handles those cases with an abbreviation list / trained model
    instead of a single regex.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    units = []
    for para in paragraphs:
        if count_tokens(para) <= 300:
            units.append(para)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            units.extend(s for s in sentences if s.strip())
    return units


def chunk_pages(
    pages: list[tuple[int, str]],
    chunk_size: int = 500,
    overlap: int = 75,
    source: str = "document.pdf",
) -> list[Chunk]:
    """Greedily pack paragraph/sentence units into ~chunk_size-token
    windows, carrying `overlap` tokens of trailing context into the
    next chunk, and tracking which page(s) each chunk spans.

    Why overlap at all: if a fact-bearing sentence lands right at a
    chunk boundary, a non-overlapping split can leave the *question*'s
    best-matching context split across two chunks, neither of which
    alone is a great embedding match. A small overlap (10-20% of
    chunk_size is a common starting point) means the sentence before a
    cut still has some of its surrounding context in the *next* chunk
    too, at the cost of mild duplication in your vector store.

    This is a greedy packer, not a global optimizer — it never looks
    ahead to see if a slightly smaller/larger chunk would align better
    with a paragraph boundary. That's a fine trade-off for speed; if
    you want tighter alignment, packing per-paragraph first and only
    falling back to mid-paragraph splitting when a single paragraph
    exceeds chunk_size is the refinement to try.
    """
    # Flatten to a stream of (unit_text, page_number) so page tracking
    # survives the packing step below regardless of how units land in
    # chunks.
    stream: list[tuple[str, int]] = []
    for page_num, text in pages:
        for unit in split_into_units(text):
            stream.append((unit, page_num))

    chunks: list[Chunk] = []
    buffer: list[tuple[str, int]] = []
    buffer_tokens = 0
    chunk_idx = 0

    def flush():
        nonlocal buffer, buffer_tokens, chunk_idx
        if not buffer:
            return
        text = " ".join(u for u, _ in buffer)
        page_start = buffer[0][1]
        page_end = buffer[-1][1]
        chunk_idx += 1
        chunks.append(
            Chunk(
                id=f"{Path(source).stem}_p{page_start}-{page_end}_c{chunk_idx}",
                text=text,
                page_start=page_start,
                page_end=page_end,
                token_count=count_tokens(text),
                source=source,
            )
        )

    for unit, page_num in stream:
        unit_tokens = count_tokens(unit)

        # A single unit (e.g. one very long sentence) bigger than the
        # whole chunk budget: emit it as its own chunk rather than
        # trying to sub-split it further. This is the "give up
        # gracefully" branch of the recursive-splitter pattern — real
        # implementations (e.g. LangChain's RecursiveCharacterTextSplitter)
        # go one level deeper here and fall back to a hard character
        # split; left as an exercise if you hit it in practice.
        if unit_tokens > chunk_size:
            flush()
            buffer, buffer_tokens = [], 0
            chunk_idx += 1
            chunks.append(
                Chunk(
                    id=f"{Path(source).stem}_p{page_num}_c{chunk_idx}",
                    text=unit,
                    page_start=page_num,
                    page_end=page_num,
                    token_count=unit_tokens,
                    source=source,
                )
            )
            continue

        if buffer_tokens + unit_tokens > chunk_size:
            flush()
            # Build the overlap: walk backward through the buffer we
            # just flushed, keeping trailing units until we've
            # accumulated ~`overlap` tokens, and seed the new buffer
            # with them.
            carry, carry_tokens = [], 0
            for u, p in reversed(buffer):
                t = count_tokens(u)
                if carry_tokens + t > overlap:
                    break
                carry.insert(0, (u, p))
                carry_tokens += t
            buffer, buffer_tokens = carry, carry_tokens

        buffer.append((unit, page_num))
        buffer_tokens += unit_tokens

    flush()
    return chunks


# =====================================================================
# PART 4 — Where semantic chunking would plug in (for your own build)
# =====================================================================
#
# The idea (this is the "embedding-based" or "Text Tiling"-style
# approach; see Greg Kamradt's "5 Levels of Text Splitting" for a
# widely-referenced writeup, and the original TextTiling paper by
# Hearst 1997 for the classic non-embedding version):
#
#   1. Split the document into small atomic units — sentences, or
#      sliding windows of a few sentences (split_into_units() above
#      already gets you paragraph/sentence units to start from).
#   2. Embed every unit with your embedding model (batch it — one API
#      call per sentence is slow and expensive).
#   3. Walk through consecutive units computing cosine similarity
#      between each unit's embedding and the next. A big drop in
#      similarity signals a topic shift — that's a candidate chunk
#      boundary.
#   4. Pick actual boundaries by thresholding that similarity curve
#      (e.g. split wherever similarity drops more than N standard
#      deviations below the local average — a fixed threshold doesn't
#      generalize well across documents with different overall
#      "chattiness").
#   5. Merge tiny resulting chunks into neighbors and split
#      oversized ones, same as chunk_pages() already does here —
#      semantic chunking decides *where* to cut, but you still want a
#      token-budget safety net afterward.
#
# A minimal stub, so the shape is here when you're ready to fill it in
# (needs an embedding function you supply — e.g. sentence-transformers'
# `all-MiniLM-L6-v2` locally, or a call to your embedding API):
#
#   def semantic_chunk(units: list[str], embed_fn, threshold: float = 0.75):
#       embeddings = embed_fn(units)                # shape: (n, dim)
#       boundaries = [0]
#       for i in range(1, len(units)):
#           sim = cosine_similarity(embeddings[i - 1], embeddings[i])
#           if sim < threshold:
#               boundaries.append(i)                # start a new chunk here
#       boundaries.append(len(units))
#       return [
#           " ".join(units[boundaries[j]:boundaries[j + 1]])
#           for j in range(len(boundaries) - 1)
#       ]
#
# Trade-off to know going in: this costs one embedding call per unit
# *before* you even start building your retrieval index, roughly
# doubling embedding spend for the corpus, and the threshold is a
# hyperparameter you'll want to tune per document type. It tends to
# pay off most on long, topic-diverse documents (e.g. meeting
# transcripts, books) and least on already-structured documents
# (e.g. API docs, contracts) where paragraph/section boundaries
# already align with topic boundaries — for those, part 3's
# structure-aware split usually gets you most of the benefit for free.


# =====================================================================
# PART 5 — CLI
# =====================================================================

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf_path", help="Path to input PDF")
    ap.add_argument("--out", default="chunks.jsonl", help="Output JSONL path")
    ap.add_argument("--chunk-size", type=int, default=500, help="Target tokens per chunk")
    ap.add_argument("--overlap", type=int, default=75, help="Overlap tokens between consecutive chunks")
    args = ap.parse_args()

    pages = extract_pages(args.pdf_path)
    if not pages:
        raise SystemExit(
            "No extractable text found. If this is a scanned PDF (i.e. pages "
            "are images, not real text), extract_text() will always return "
            "nothing — you'd need OCR first (pytesseract + pdf2image: render "
            "each page to an image, then OCR it) before any of this applies."
        )

    chunks = chunk_pages(
        pages,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        source=Path(args.pdf_path).name,
    )

    with open(args.out, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

    total_tokens = sum(c.token_count for c in chunks)
    print(f"Extracted {len(pages)} pages -> {len(chunks)} chunks ({total_tokens} tokens total)")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
