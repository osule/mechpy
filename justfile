# Development commands for mechpy

# Build and install the package (forces clean rebuild)
dev:
    uv cache clean
    uv run maturin develop --uv

# Build release version
release:
    uv cache clean
    uv run maturin develop --release --uv

# Run tests
test:
    uv run pytest tests/

# Run benchmarks
bench:
    uv run pytest tests/bench/ --benchmark-only

# Clean build artifacts
clean:
    uv run cargo clean
    rm -f .venv/lib/python*/site-packages/mechpy/*.so
