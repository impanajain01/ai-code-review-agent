from app.diff_parser import parse_diff, should_review

SAMPLE_DIFF = """diff --git a/app/example.py b/app/example.py
index 1111111..2222222 100644
--- a/app/example.py
+++ b/app/example.py
@@ -1,2 +1,3 @@
 import os
+import sys
 def main():
@@ -10,2 +11,2 @@ def helper():
-    return 1
+    return 2
     pass
diff --git a/package-lock.json b/package-lock.json
index 3333333..4444444 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1 +1 @@
-old
+new
"""


def test_lockfiles_are_skipped():
    chunks = parse_diff(SAMPLE_DIFF)
    assert {c.filename for c in chunks} == {"app/example.py"}


def test_added_lines_carry_new_file_line_numbers():
    chunks = parse_diff(SAMPLE_DIFF)
    assert "    2 + import sys" in chunks[0].text


def test_removed_lines_have_no_line_number():
    chunks = parse_diff(SAMPLE_DIFF)
    assert "      -     return 1" in chunks[0].text


def test_large_file_is_split_into_multiple_chunks():
    added = "\n".join(f"+line {i}" for i in range(200))
    diff = (
        "diff --git a/big.py b/big.py\n"
        "new file mode 100644\n"
        "index 0000000..1111111\n"
        "--- /dev/null\n"
        "+++ b/big.py\n"
        "@@ -0,0 +1,200 @@\n"
        f"{added}\n"
    )
    chunks = parse_diff(diff, max_chars=500)
    assert len(chunks) > 1
    assert all(len(c.text) <= 600 for c in chunks)


def test_should_review_filters_generated_files():
    assert should_review("app/main.py")
    assert not should_review("static/app.min.js")
    assert not should_review("logo.png")