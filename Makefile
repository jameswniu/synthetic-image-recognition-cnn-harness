PY := uv run python
NAME := hv_takehome_james_niu

.PHONY: sync serve test claims claims-fresh eval eval-classifier reports policy-demo telemetry compare dashboard preview deck deck-render walkthrough overlays cards docker-build docker-run smoke zip

sync:
	uv sync --extra dev

serve:
	uv run uvicorn scripts.serve:app --host 127.0.0.1 --port 8000

# --extra dev so this works after a bare `uv sync`, which is what the README's quickstart runs.
# Caught by running the zip end to end from a fresh unzip: pytest lives in the dev extra, so
# without this flag `make test` fails to spawn for anyone who followed the instructions.
test:
	uv run --extra dev pytest -q

# The README badge wall makes four hard-coded claims: tests, F1, queue share, model size.
# Two layers keep them honest. `claims` is the consistency layer: badges against the reports
# committed at HEAD, plus the advertised 61-page corpus. `claims-fresh` is the behavior layer:
# run after `make synth && make reports` so a code change that moves F1 or the flag population
# fails even though it touched no report. --with onnx because counting weights needs the parser.
claims:
	uv run --with onnx --extra dev --extra train python tools/check_claims.py committed

claims-fresh:
	uv run --with onnx --extra dev --extra train python tools/check_claims.py fresh

eval:
	HV_CLASSIFIER=off $(PY) scripts/evaluate.py --report reports/eval_report.json

# Rebuild the machine-generated deck inputs in one go. gold_report.json is not here on purpose:
# it is the frozen record of a person's rulings on the crops, an input, never regenerated.
reports: eval telemetry compare

# Needs the train extra for onnxruntime: uv sync --extra train. Fails loudly rather than quietly
# reporting rule-only numbers under a classifier heading.
eval-classifier:
	$(PY) scripts/evaluate.py --require-classifier --report reports/eval_report_classifier.json

# Same code, same pages, two definitions of what counts as a mark. Prints what moved and why.
policy-demo:
	HV_CLASSIFIER=off $(PY) scripts/compare_policies.py

# Every page in the repo through the pipeline, both classifier modes, with per-reason-code counts.
telemetry:
	uv run --extra train python scripts/telemetry.py --out reports/telemetry.json

# The three-reader verdict table on the brief's answer key: rules, the CNN alone, both together.
compare:
	uv run --extra train python scripts/compare_readers.py

# The operator view, built from reports/telemetry.json. Self-contained, opens with no server.
dashboard:
	$(PY) tools/make_dashboard.py

# The README's screenshot of that view, photographed off the real dashboard.html by offscreen
# headless chromium, then gated: a pixel of a retired accent palette fails the build. Not folded
# into `dashboard` because CI regenerates the page and has no chromium; the preview is a local
# artifact, committed like the figures.
preview: dashboard
	$(PY) tools/make_preview.py

# The deck for the review meeting, every number read from the repo's own reports.
deck:
	uv run --with python-pptx python tools/make_deck.py

# The code walkthrough for the review meeting, a Word document in the same theme as the deck.
walkthrough:
	uv run --with python-docx python tools/make_walkthrough.py

# Render every slide to PNG so layout defects are visible instead of inferred. Reading shape
# geometry says a connector with no arrowhead is an arrow, that a grey header on a dark blue fill
# is legible, and that an index shifted by one still points at the right box. Looking says none of
# that. Needs LibreOffice: brew install --cask libreoffice. Its binary is not on PATH.
SOFFICE := $(shell ls -d /opt/homebrew/Caskroom/libreoffice/*/LibreOffice.app/Contents/MacOS/soffice 2>/dev/null | tail -1)
deck-render: deck
	@test -n "$(SOFFICE)" || (echo "LibreOffice not found. brew install --cask libreoffice" && exit 1)
	rm -rf build/slides && mkdir -p build/slides
	@# Fail on the first deck that does not render, not on the last. A shell for-loop returns the
	@# status of its final iteration, so without the exits a broken deck early in the list passed
	@# whenever the last one rendered. Then count: every slide in every deck must have a PNG.
	for f in deliverables/checkbox-*.pptx; do \
	  b=$$(basename "$$f" .pptx); \
	  "$(SOFFICE)" --headless --norestore --convert-to pdf --outdir build/slides "$$f" || exit 1; \
	  pdftoppm -png -r 90 "build/slides/$$b.pdf" "build/slides/$$b" || exit 1; done
	@exp=$$(uv run --with python-pptx python -c 'import glob; from pptx import Presentation; print(sum(len(Presentation(f).slides) for f in glob.glob("deliverables/checkbox-*.pptx")))' 2>/dev/null) \
	  || { echo "cannot count the slides: a file matching deliverables/checkbox-*.pptx is not a deck"; exit 1; }; \
	 got=$$(ls build/slides/*.png | wc -l | tr -d " "); \
	 test "$$got" -eq "$$exp" || { echo "rendered $$got slides, the decks hold $$exp"; exit 1; }; \
	 echo "slides rendered to build/slides: $$got of $$exp"

overlays:
	$(PY) scripts/evaluate.py --overlays data/overlays

cards:
	$(PY) tools/make_cards.py

synth:
	$(PY) scripts/synth.py --seed 11

train:
	uv sync --extra train --extra dev && $(PY) scripts/train.py

bench:
	$(PY) scripts/bench.py --url http://127.0.0.1:8000/detect --report reports/bench_report.json

figures:
	$(PY) tools/draw_figures.py --write

figures-check:
	$(PY) tools/draw_figures.py --check

mine:
	$(PY) scripts/mine_edges.py

docker-build:
	docker build -t hv-checkbox .

docker-run:
	docker run --rm -p 8000:8000 hv-checkbox

smoke:
	curl -s http://127.0.0.1:8000/healthz && echo && curl -s -F file=@data/samples/sample_1.jpg http://127.0.0.1:8000/detect | head -c 300 && echo

zip:
	cd .. && rm -f $(NAME).zip && zip -qr $(NAME).zip $(NAME) -x '$(NAME)/.venv/*' '$(NAME)/.git/*' '*/__pycache__/*' '*.pyc' '$(NAME)/reports/eval_report_classifier.json' '$(NAME)/reports/eval_report_model.json' '$(NAME)/.pytest_cache/*' '$(NAME)/data/synth/*' '$(NAME)/data/overlays/*' '$(NAME)/data/holdout/*' '$(NAME)/build/*' '$(NAME)/~$$*' && ls -la $(NAME).zip
