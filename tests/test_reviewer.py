from app import reviewer
from app.diff_parser import DiffChunk
from app.reviewer import Category, Finding, ReviewResult, Severity


def _finding(line: int) -> Finding:
    return Finding(
        line=line,
        severity=Severity.high,
        category=Category.bug,
        title="t",
        explanation="e",
        suggestion="",
    )


def test_findings_are_tagged_with_filename(monkeypatch):
    monkeypatch.setattr(
        reviewer, "_call_model", lambda chunk: ReviewResult(findings=[_finding(3)])
    )
    out = reviewer.review_chunks([DiffChunk("a.py", "x")])
    assert out[0].filename == "a.py"
    assert out[0].finding.line == 3


def test_failed_chunk_is_skipped_not_fatal(monkeypatch):
    def boom(chunk):
        raise RuntimeError("api down")

    monkeypatch.setattr(reviewer, "_call_model", boom)
    assert reviewer.review_chunks([DiffChunk("a.py", "x")]) == []