all: build doc


build-sdist:
	python3 -m build --sdist

build-wheel:
	python3 -m build --wheel

# Build the source code
build:
	python -m build .

# Submit version
submit: build
	twine upload dist/*

# Build documentation
doc: doc-clear
	./docs/update.bat
# Actually how to do this thing 

# Clear documentation
doc-clear:
	rm ./docs/build/* -r

