# IFRS18-ORAS before-pilot checklist

1. Repository technically ready?
   `PASS` Local repository checks confirm the required files are present, the working branch is based on current `origin/main`, and the methodological-review script and documents are added without changing scoring logic.

2. CI green?
   `WARNING` Local lint, format, tests, and codebook validation passed, but remote GitHub Actions status was not yet externally confirmed at the time of this checklist.

3. Codebook v0.1.1 present and default?
   `PASS` `config/codebook_v0.1.1.json` is present and `src/ifrs18_oras/cli.py` still defaults to that codebook.

4. v0.1.0 preserved?
   `PASS` `config/codebook_v0.1.0.json` remains present for reproducibility of earlier pilot runs.

5. Stale XHTML fallback imports absent?
   `PASS` `src/ifrs18_oras/extraction.py` no longer contains the obsolete `import importlib.util` or `from html.parser import HTMLParser` lines.

6. Is `lxml_html.HTMLParser(...)` still present?
   `PASS` `parser = lxml_html.HTMLParser(encoding="utf-8", remove_comments=True)` is still present in `src/ifrs18_oras/extraction.py`.

7. Is `--preferred-format` available?
   `PASS` The CLI help still exposes `--preferred-format {all,xhtml,pdf}`.

8. Are XHTML context-window fields present?
   `PASS` `XHTML_CONTEXT_WINDOW_BLOCKS` remains present in `src/ifrs18_oras/detection.py`, supporting deterministic context-window logic.

9. Are Scopus methodological precedents documented?
   `PASS` The review script, summary outputs, full methodological-positioning note, and concise precedent table were created from the three supplied Scopus exports.

10. Can we proceed to the EU pilot?
    `WARNING` The repository appears locally ready for a controlled pilot run, but empirical use should remain conditional on remote CI confirmation, evidence-log review, and manual validation of a subsample.

11. What remains to be done before using results in the paper?
    `WARNING` Complete remote CI review, inspect the PR checks, review evidence logs from the first pilot run, conduct manual validation on a subsample, and keep interpretation limited to observable documentary alignment rather than legal compliance.
