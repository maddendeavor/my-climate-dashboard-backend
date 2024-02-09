SHELL := /bin/bash

# Note requires tab between function calls

install:
	.venv/bin/pip install .

develop:
	.venv/bin/pip install -e .

venv:
	virtualenv .venv 
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install --upgrade setuptools
	source .venv/bin/activate

clean:
	rm -rf .venv
	rm -rf *.egg-info
