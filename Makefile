all: build doc

install-editable:
	pip install -e . --config-settings editable_mode=strict

build-sdist:
	python3 -m build --sdist

build-wheel:
	python3 -m build --wheel

# Build the source code
build:
	python -m build .

install:
	pip install --no-build-isolation -e . --config-settings editable_mode=strict

# Submit version
submit: build-sdist build-wheel
	twine upload dist/*

# Build documentation
doc:
	make doc-clear -i
	sphinx-apidoc -f -E -o ./docs/source ./evokit
	make -C ./docs/ html

# Clear documentation
doc-clear:
	rm ./docs/build/* -r -f

