.DEFAULT_GOAL := run

run:
	@if [ -n "$(ARGS)" ]; then \
		docker run --rm -v .:/usr/src/app jbops python3 $(ARGS); \
	else \
		echo "No script passed! Example: make ARGS='utility/library_growth.py'"; \
	fi

build:
	docker build -t jbops .