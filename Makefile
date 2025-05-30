# Capture all goals (targets) provided to make
ARGS := $(filter-out $@,$(MAKECMDGOALS))

setup:
	@echo "Installing system and python dependencies"
	sudo apt install libapr1-dev
	pip install -r requirements.txt

run:
	@echo "Running main with arguments: $(ARGS)"
	python3 src/main.py $(ARGS)

all: setup run

# Prevent make from treating arguments as targets
%:
	@: