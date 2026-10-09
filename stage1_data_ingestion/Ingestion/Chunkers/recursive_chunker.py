from dataclasses import dataclass
from enum import Enum
import re
from stage1_data_ingestion.Ingestion.Chunkers.chunker import Chunker
from stage1_data_ingestion.Ingestion.models import Document, ParagraphPiece
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk 

@dataclass
class ParagraphContext:
    start_index: int = 0


class RecursiveChunker(Chunker):
    class FITNESS_DECISION(Enum):
        EXACT_MATCH = 1
        WITHIN_TOLERANCE = 2
        BELOW_TARGET = 3
        ABOVE_TARGET = 4
        WORD_OVERFLOW_SPECIAL_CASE = 5

    def __init__(
        self,
        max_chunk_size=500,
        overlap=10,
        separators="p",
        chunk_size_tolrance=20,
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.separators = separators
        self.chunk_size_tolerance = chunk_size_tolrance

    def is_text_fit_for_chunk(self, text: str):
        text_length = len(text)
        upper_limit = self.max_chunk_size + self.chunk_size_tolerance
        lower_limit = self.max_chunk_size - self.chunk_size_tolerance

        # Do not split an individual word into characters.
        if len(text.split()) == 1 and text_length > self.max_chunk_size:
            return self.FITNESS_DECISION.WORD_OVERFLOW_SPECIAL_CASE

        if text_length == self.max_chunk_size:
            return self.FITNESS_DECISION.EXACT_MATCH

        if lower_limit <= text_length <= upper_limit:
            return self.FITNESS_DECISION.WITHIN_TOLERANCE

        if text_length > upper_limit:
            return self.FITNESS_DECISION.ABOVE_TARGET

        return self.FITNESS_DECISION.BELOW_TARGET

    def _make_paragraph_piece(
        self,
        content: str,
        paragraph_start: int,
        paragraph_end: int,
        *,
        is_overlap: bool = False,
        is_residual: bool = False,
    ) -> ParagraphPiece:
        piece = ParagraphPiece()
        piece.content = content
        piece.is_overlap = is_overlap
        piece.is_residual = is_residual
        piece.start = paragraph_start
        piece.end = paragraph_end
        return piece

    def _get_overlap(self, text: str) -> str:
        if not text or self.overlap <= 0:
            return ""

        overlap_size = int(len(text) * self.overlap / 100)

        if overlap_size <= 0:
            return ""

        return text[-overlap_size:]

    def _join_overlap_and_residual(
        self,
        overlap_text: str,
        residual: str,
    ) -> str:
        if not overlap_text:
            return residual

        if not residual:
            return overlap_text

        return f"{overlap_text.rstrip()} {residual.lstrip()}"

    def sentance_lvel_text_split(
        self,
        text: str,
        paragra_start: int = 0,
        paragra_end: int | None = None,
    ):
        """
        Split oversized text at sentence boundaries first.

        Returns:
            residual_text:
                Text that has not yet been finalized.
            finalized_pieces:
                ParagraphPiece objects that have already been finalized.

        If a sentence cannot fit naturally, the current candidate is
        delegated to the word-level partitioner.
        """
        if not text.strip():
            return "", []

        if paragra_end is None:
            paragra_end = paragra_start

        # Keep the full-stop with the sentence.
        # This is intentionally a simple sentence splitter for now.
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=\.)\s+", text.strip())
            if sentence.strip()
        ]

        finalized_pieces: list[ParagraphPiece] = []
        chunk_text = ""

        index = 0

        while index < len(sentences):
            sentence = sentences[index]

            candidate = (
                sentence
                if not chunk_text
                else f"{chunk_text} {sentence}"
            )

            decision = self.is_text_fit_for_chunk(candidate)

            if decision in (
                self.FITNESS_DECISION.EXACT_MATCH,
                self.FITNESS_DECISION.WITHIN_TOLERANCE,
                self.FITNESS_DECISION.BELOW_TARGET,
            ):
                chunk_text = candidate
                index += 1
                continue

            if decision == self.FITNESS_DECISION.WORD_OVERFLOW_SPECIAL_CASE:
                # Preserve an oversized indivisible word.
                if chunk_text:
                    finalized_pieces.append(
                        self._make_paragraph_piece(
                            chunk_text,
                            paragra_start,
                            paragra_end,
                        )
                    )
                    chunk_text = ""

                finalized_pieces.append(
                    self._make_paragraph_piece(
                        sentence,
                        paragra_start,
                        paragra_end,
                    )
                )
                index += 1
                continue

            # ABOVE_TARGET:
            # Pass the whole candidate to the word-level partitioner.
            # It may produce multiple finalized chunks.
            residual_text, word_pieces = (
                self.fit_to_chunk_size_by_trimming_words(
                    candidate,
                    [],
                    paragra_start,
                    paragra_end,
                )
            )

            finalized_pieces.extend(word_pieces)

            # The current sentence has now been processed. Continue with
            # later sentences in the same paragraph instead of returning
            # early and losing them.
            chunk_text = residual_text
            index += 1

        return chunk_text, finalized_pieces

    def fit_to_chunk_size_by_trimming_words(
        self,
        current_chunk: str,
        finalized_chunks_list: list[ParagraphPiece],
        paragra_start: int = 0,
        paragra_end: int | None = None,
    ):
        """
        Recursively partition oversized text using whole-word boundaries.

        Returns:
            (residual/current_text, finalized_pieces)

        An individual word is never split into characters. If a word itself
        exceeds the target, it is preserved as an oversized special-case
        chunk.
        """
        if paragra_end is None:
            paragra_end = paragra_start

        current_chunk = current_chunk.strip()

        if not current_chunk:
            return "", finalized_chunks_list

        decision = self.is_text_fit_for_chunk(current_chunk)

        if decision in (
            self.FITNESS_DECISION.EXACT_MATCH,
            self.FITNESS_DECISION.WITHIN_TOLERANCE,
            self.FITNESS_DECISION.BELOW_TARGET,
        ):
            return current_chunk, finalized_chunks_list

        # Preserve an oversized word rather than splitting it into
        # characters and potentially destroying its meaning.
        if decision == self.FITNESS_DECISION.WORD_OVERFLOW_SPECIAL_CASE:
            finalized_chunks_list.append(
                self._make_paragraph_piece(
                    current_chunk,
                    paragra_start,
                    paragra_end,
                )
            )
            return "", finalized_chunks_list

        words = current_chunk.split()
        removed_words: list[str] = []

        while words:
            removed_words.append(words.pop())

            remaining = " ".join(words)
            remaining_decision = self.is_text_fit_for_chunk(remaining)

            if remaining_decision in (
                self.FITNESS_DECISION.EXACT_MATCH,
                self.FITNESS_DECISION.WITHIN_TOLERANCE,
                self.FITNESS_DECISION.BELOW_TARGET,
            ):
                break

        finalized_chunk = " ".join(words)

        # pop() removes words from right to left, so restore the original
        # order before constructing the residual.
        removed_words.reverse()
        residual_text = " ".join(removed_words)

        # Defensive handling for the case where the only remaining unit
        # cannot be reduced further.
        if not finalized_chunk:
            finalized_chunks_list.append(
                self._make_paragraph_piece(
                    residual_text,
                    paragra_start,
                    paragra_end,
                )
            )
            return "", finalized_chunks_list

        finalized_chunks_list.append(
            self._make_paragraph_piece(
                finalized_chunk,
                paragra_start,
                paragra_end,
            )
        )

        # Overlap is introduced only at a forced word-level boundary.
        overlap_text = self._get_overlap(finalized_chunk)

        next_current_chunk = self._join_overlap_and_residual(
            overlap_text,
            residual_text,
        )

        # The residual may itself be large after overlap is added, so the
        # recursive call partitions it again if necessary.
        return self.fit_to_chunk_size_by_trimming_words(
            next_current_chunk,
            finalized_chunks_list,
            paragra_start,
            paragra_end,
        )

    def fit_to_chunk_size_by_trimming_sentances(
        self,
        current_chunk: str,
        paragra_start: int = 0,
        paragra_end: int | None = None,
    ):
        """
        Compatibility wrapper for sentence-level trimming.
        """
        return self.sentance_lvel_text_split(
            current_chunk,
            paragra_start,
            paragra_end,
        )
    def _paragraph_pieces_to_chunks(
    self,
    paragraph_pieces: list[ParagraphPiece],
    document: Document
    ) -> list[Chunk]: 
        chunks = []

        for index, piece in enumerate(paragraph_pieces):
            chunk = Chunk(
            content=piece.content,
            document_id= document.metadata.document_id,
            chunk_id=...,
            chunk_index=index,
            metadata={...}
            )
            chunks.append(chunk)
            return chunks

    def chunk(self, document: Document):
        """
        Chunk a Document whose paragraphs have already been parsed by the
        DOCX parser.

        Flow:
            paragraphs
                -> paragraph accumulation
                -> sentence-level splitting
                -> word-level splitting when necessary
                -> finalized ParagraphPiece objects
        """
        paragraph_pieces: list[ParagraphPiece] = []
        current_piece: ParagraphPiece | None = None

        index = 0

        while index < len(document.paragraph_list):
            paragraph = document.paragraph_list[index]
            paragraph_text = paragraph.text.strip()

            if not paragraph_text:
                index += 1
                continue

            # Build the candidate without losing the paragraph boundary.
            if current_piece is None:
                candidate = paragraph_text
                candidate_start = index
            else:
                candidate = f"{current_piece.content}\n{paragraph_text}"
                candidate_start = current_piece.start
            #print('paragraph_text:',paragraph_text)
            fitness_decision = self.is_text_fit_for_chunk(candidate)

            # ---------------------------------------------------------
            # Candidate is acceptable.
            # ---------------------------------------------------------
            if fitness_decision in (
                self.FITNESS_DECISION.EXACT_MATCH,
                self.FITNESS_DECISION.WITHIN_TOLERANCE,
            ):
                paragraph_pieces.append(
                    self._make_paragraph_piece(
                        candidate,
                        candidate_start,
                        index,
                    )
                )
                current_piece = None

            # ---------------------------------------------------------
            # Candidate is below target; keep accumulating.
            # ---------------------------------------------------------
            elif fitness_decision == self.FITNESS_DECISION.BELOW_TARGET:
                if current_piece is None:
                    current_piece = self._make_paragraph_piece(
                        candidate,
                        candidate_start,
                        index,
                    )
                else:
                    current_piece.content = candidate
                    current_piece.end = index

            # ---------------------------------------------------------
            # Candidate is oversized.
            # ---------------------------------------------------------
            elif fitness_decision in (
                self.FITNESS_DECISION.ABOVE_TARGET,
                self.FITNESS_DECISION.WORD_OVERFLOW_SPECIAL_CASE,
            ):
                residual_text, pieces = self.sentance_lvel_text_split(
                    candidate,
                    candidate_start,
                    index,
                )

                paragraph_pieces.extend(pieces)

                if residual_text.strip():
                    current_piece = self._make_paragraph_piece(
                        residual_text,
                        candidate_start,
                        index,
                        is_residual=True,
                    )
                else:
                    current_piece = None

            index += 1

        # Finalize any text that remains after the last paragraph.
        if current_piece is not None and current_piece.content.strip():
            current_piece.is_residual = False
            '''current_piece.metadata['filename'] = document.metadata.file_name
            current_piece.metadata['extension'] = document.metadata.file_extension
            current_piece.metadata['owner'] = document.metadata.file_owner'''
            paragraph_pieces.append(current_piece)
    
            
        return self._paragraph_pieces_to_chunks(paragraph_pieces,document)

    def chunk_parsing_docx(self, document: Document):
        return self.chunk(document)

    def chunk_parsing_simple_text(self, document: Document):
        return self.chunk(document)
