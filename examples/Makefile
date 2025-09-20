# Makefile for building the example Vault plugin shared library

# Default target
.PHONY: all
all: build

# Build the Go shared library
.PHONY: build
build:
	@echo "Building Go shared library..."
	go build -buildmode=c-shared -o vault_plugin.so example_vault_plugin.go
	@echo "Built vault_plugin.so successfully"
	@echo ""
	@echo "Generated files:"
	@ls -la vault_plugin.so vault_plugin.h
	@echo ""
	@echo "You can now run the Python example:"
	@echo "  python example_usage.py"

# Clean generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	rm -f vault_plugin.so vault_plugin.h
	@echo "Clean complete"

# Check prerequisites
.PHONY: check
check:
	@echo "Checking prerequisites..."
	@go version || (echo "Error: Go not found. Please install Go 1.18 or later." && exit 1)
	@python3 --version || (echo "Error: Python3 not found." && exit 1)
	@echo "Prerequisites check passed"

# Run the Python example (requires the shared library to be built first)
.PHONY: run
run: build
	@echo "Running Python example..."
	python3 example_usage.py

# Show help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build   - Build the Go shared library (default)"
	@echo "  clean   - Remove generated files"
	@echo "  check   - Check prerequisites (Go and Python)"
	@echo "  run     - Build and run the Python example"
	@echo "  help    - Show this help message"