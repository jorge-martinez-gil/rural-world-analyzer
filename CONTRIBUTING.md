# Contributing to Rural World Analyzer

Thank you for your interest in improving Rural World Analyzer. Contributions that strengthen the app, documentation, reproducibility, and academic usefulness are welcome.

## Reporting Bugs

- Search the existing issue tracker before opening a new bug report.
- Include the operating system, Python version, and package versions from `requirements.txt`.
- Describe the expected behavior, actual behavior, and clear steps to reproduce the issue.
- When relevant, include coordinates, radius settings, amenity filters, and screenshots.

## Suggesting Features

- Open an issue describing the research or user need that motivates the feature.
- Explain how the proposed enhancement improves usability, reproducibility, or scholarly impact.
- If possible, include interface sketches, references, or example workflows.

## Development Setup

```bash
git clone https://github.com/jorge-martinez-gil/rural-world-analyzer.git
cd rural-world-analyzer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
- Prefer clear, small helper functions over deeply nested logic.
- Keep user-facing text concise, informative, and suitable for academic audiences.
- Ensure new features handle empty datasets gracefully.

## Pull Request Process

1. Create a focused branch for your change.
2. Keep pull requests scoped to a single improvement or tightly related set of improvements.
3. Update documentation when changing user-visible behavior or repository metadata.
4. Describe how you validated the change, including manual checks for Streamlit UI updates.
5. Ensure no secrets, credentials, or generated artifacts are committed.

By contributing, you agree that your submissions will be released under the project's [MIT License](LICENSE).
