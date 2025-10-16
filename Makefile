CONTAINER_ENGINE ?= $(shell which podman >/dev/null 2>&1 && echo podman || echo docker)

.PHONY: format
format:
	uv run ruff check
	uv run ruff format
	terraform fmt module/

#.PHONY: image_tests
#image_tests:
#	[ -f "hooks/post_plan.py" ]

.PHONY: code_tests
code_tests:
	uv run ruff check --no-fix
	uv run ruff format --check
	uv run mypy
	uv run pytest -vv --cov=er_aws_s3 --cov-report=term-missing --cov-report xml

.PHONY: terraform_tests
terraform_tests:
	terraform fmt -check -diff module/

.PHONY: test
test: code_tests terraform_tests

.PHONY: build_test
build_test:
	$(CONTAINER_ENGINE) build --progress plain --target test -t er-aws-s3:test .

.PHONY: build
build:
	$(CONTAINER_ENGINE) build --progress plain --target prod -t er-aws-s3:prod .

.PHONY: dev
dev:
	uv sync
