pytest --nbmake ./docs/source/guides/examples/accountant.ipynb

pytest --nbmake ./docs/source/guides/examples/algorithm.ipynb

pytest --nbmake ./docs/source/guides/examples/gp.ipynb

pytest --nbmake ./docs/source/guides/examples/interceptor.ipynb

pytest --nbmake ./docs/source/guides/examples/lgp.ipynb

pytest --nbmake ./docs/source/guides/examples/onemax.ipynb

pytest --nbmake ./docs/source/guides/examples/selector.ipynb

python -m mypy ./evokit
