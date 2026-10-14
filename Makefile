.PHONY: deals rebuild test serve

deals:
	python3 scripts/gear_run.py

rebuild:
	python3 scripts/gear_run.py --offline

test:
	python3 -m unittest discover tests

serve:
	@echo "Open http://127.0.0.1:8000/ski-deals/"
	python3 -m http.server 8000 --bind 127.0.0.1
