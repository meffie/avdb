.PHONY: help lint test package sdist wheel install install-user remove clean

help:
	@echo "usage: make <target> [<target> ...]"
	@echo "targets:"
	@echo "  help         - display targets"
	@echo "  lint         - run python linter"
	@echo "  test         - run unit tests"
	@echo "  package      - build distribution files"
	@echo "  sdist        - create source distribution file"
	@echo "  wheel        - create wheel distribution file"
	@echo "  install      - install package, global (requires root)"
	@echo "  install-user - install package, user"
	@echo "  install-dev  - install package, development"
	@echo "  remove       - uninstall package"
	@echo "  clean        - remove generated files"

avdb/__version__.py:
	echo "VERSION = '$$(git describe --tags | sed 's/^v//')'" > avdb/__version__.py

lint:
	pyflakes avdb/*.py

test:
	#python -m test.test_<name> -v

package: sdist wheel

sdist: avdb/__version__.py
	python setup.py sdist

wheel: avdb/__version__.py
	python setup.py bdist_wheel

install: avdb/__version__.py
	pip install --upgrade --no-index .

install-user: avdb/__version__.py
	pip install --user --upgrade --no-index .

install-dev: avdb/__version__.py
	pip install --user -e .

remove:
	pip uninstall -y avdb

clean:
	-rm -f *.pyc test/*.pyc avdb/*.pyc avdb/__version__.py
	-rm -fr avdb.egg-info/ build/ dist/ MANIFEST
