# Sorry that this Makefile is a bit of a disaster.


PYTHON ?= $(shell which python3 python 2>/dev/null | head -n1)
PYTHON := $(PYTHON)


PROJECT := $(shell $(PYTHON) ./setup.py --name)
VERSION := $(shell $(PYTHON) ./setup.py --version)

ARCHIVE := $(PROJECT)-$(VERSION).tar.gz


##@ Basic Targets
default: quick-test	## Runs the quick-test target


help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


report-python:
	@echo "Using python" $(PYTHON)
	@$(PYTHON) -VV


##@ Local Build and Install
build: clean-built report-python flake8	## Produces a wheel using the default system python
	@$(PYTHON) setup.py bdist_wheel


install: build ## Installs using the default python for the current user
	@$(PYTHON) -B -m pip.__main__ \
		install --no-deps --user -I \
		dist/$(PROJECT)-$(VERSION)-py3-none-any.whl


##@ Cleanup
tidy:	## Removes stray eggs and .pyc files
	@rm -rf *.egg-info
	@find -H . \
		\( -iname '.tox' -o -iname '.eggs' -prune \) -o \
		\( -type d -iname '__pycache__' -exec rm -rf {} + \) -o \
		\( -type f -iname '*.pyc' -exec rm -f {} + \)


clean-built:
	@rm -rf build/* dist/*
	@if [ -f ./"$(ARCHIVE)" ] ; then rm -f ./"$(ARCHIVE)" ; fi


clean: clean-built tidy	## Removes built content, test logs, coverage reports
	@rm -rf .coverage* htmlcov/* logs/*


##@ Containerized RPMs
packaging-build: $(ARCHIVE)	## Launches all containerized builds
	@./tools/launch-build.sh


packaging-test: packaging-build	## Launches all containerized tests
	@rm -rf logs/*
	@./tools/launch-test.sh


##@ Testing
test: clean	## Launches tox
	@tox


bandit: ## Launches bandit via tox
	@tox -e bandit


flake8:	## Launches flake8 via tox
	@tox -e flake8


mypy:	## Launches mypy via tox
	@tox -e mypy


quick-test: build	## Launches nosetest using the default python
	@$(PYTHON) -B setup.py test


##@ RPMs
srpm: $(ARCHIVE)	## Produce an SRPM from the archive
	@rpmbuild \
		--define "_srcrpmdir dist" \
		--define "dist %{nil}" \
		-ts "$(ARCHIVE)"


rpm: $(ARCHIVE)		## Produce an RPM from the archive
	@rpmbuild --define "_rpmdir dist" -tb "$(ARCHIVE)"


archive: $(ARCHIVE)	## Extracts an archive from the current git commit


# newer versions support the --format tar.gz but we're intending to work all
# the way back to RHEL 6 which does not have that.
$(ARCHIVE):
	@git archive HEAD \
		--format tar --prefix "$(PROJECT)-$(VERSION)/" \
		| gzip > "$(ARCHIVE)"


.PHONY: archive build clean clean-built default flake8 help mypy packaging-build packaging-test quick-test rpm srpm test tidy


# The end.
