PYTHON ?= python3

.PHONY: help check-python test portfolio verify quality visuals

help:
	@echo "High-Stakes Analytics & Decision Lab"
	@echo "  make test       Run the standalone regression suite"
	@echo "  make portfolio  Rebuild and compare all fifteen projects"
	@echo "  make verify     Run tests and the complete portfolio rebuild"
	@echo "  make quality    Run Ruff, mypy, and codespell"
	@echo "  make visuals    Regenerate canonical README, report, and case visuals"

check-python:
	@$(PYTHON) -c 'import sys; sys.exit("Python 3.11 or newer is required") if sys.version_info < (3, 11) else None'

test: check-python
	$(PYTHON) -m unittest discover -s tests -v

portfolio: check-python
	$(PYTHON) scripts/verify_portfolio_reproducibility.py

verify: test portfolio

quality:
	ruff check scripts tests examples/real-data-cases/projects/_shared/safe_external_io.py
	mypy
	codespell --config .codespellrc README.md CHANGELOG.md CONTRIBUTING.md SECURITY.md VERSIONING.md docs references scripts tests

visuals: check-python
	$(PYTHON) scripts/build_readme_visuals.py
	$(PYTHON) scripts/build_terminal_decision_reports.py
	$(PYTHON) scripts/build_case_examples.py
