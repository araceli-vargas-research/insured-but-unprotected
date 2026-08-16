.PHONY: download build validate all

download:
	python3 code/00_download_cms.py

build:
	python3 code/01_build_cms_panel.py
	python3 code/03_build_market_panel.py
	python3 code/04_build_premium_panel.py
	python3 code/05_build_analysis_panel.py

validate:
	python3 code/02_validate_outputs.py

all: download build validate
