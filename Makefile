.PHONY: download build legal results test validate all handoff

download:
	python3 code/00_download_cms.py

build:
	python3 code/01_build_cms_panel.py
	python3 code/03_build_market_panel.py
	python3 code/04_build_premium_panel.py
	python3 code/05_build_analysis_panel.py

legal:
	python3 legislation/validate_legal_audit.py
	python3 code/06_export_legal_inventory.py

results:
	python3 code/07_initial_results.py

test:
	python3 -m unittest discover -s tests -v

validate:
	python3 code/02_validate_outputs.py

all: download build legal results validate test

# Fast coauthor audit using the committed processed panel. `make all` performs
# the full download and rebuild when network access is available.
handoff: legal results validate test
