# Repository Setup Guide

This document describes how to set up the `boltzfold_client` repository on GitHub and publish to PyPI.

## Repository Structure

```
boltzfold_client/
├── boltzfold_client/       # Main package code
│   ├── __init__.py         # Package exports
│   ├── client.py           # BoltzFoldClient implementations
│   ├── models.py           # Data models
│   ├── monitor.py          # Job monitoring utilities
│   ├── sequences.py        # FASTA helpers
│   └── py.typed            # Type hints marker
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   └── test_client.py
├── examples/               # Usage examples
│   ├── basic_prediction.py
│   ├── binder_batch.py
│   └── boltzgen_design.py
├── .github/
│   └── workflows/
│       └── test.yml        # CI/CD pipeline
├── .gitignore              # Git ignore rules
├── CHANGELOG.md            # Version history
├── CONTRIBUTING.md         # Contribution guidelines
├── LICENSE                 # MIT License
├── Makefile               # Development commands
├── MANIFEST.in            # Package manifest
├── pyproject.toml         # Build configuration
├── QUICKSTART.md          # Quick start guide
└── README.md              # Main documentation
```

## GitHub Setup

### 1. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `boltzfold_client`
3. Description: "Lightweight Python client for the BoltzFold protein structure prediction API"
4. Set to **Public** (or Private if preferred)
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

### 2. Push to GitHub

```bash
cd /Users/jules/Documents/code/boltzFoldAll/boltzfold_client

# Add GitHub remote (replace 'yourusername' with your GitHub username)
git remote add origin https://github.com/yourusername/boltzfold_client.git

# Push to GitHub
git push -u origin main
```

### 3. Configure Repository Settings

#### Enable Issues and Discussions
- Go to Settings → Features
- Enable "Issues"
- Enable "Discussions" (optional but recommended)

#### Add Topics
- Add relevant topics: `python`, `protein-folding`, `bioinformatics`, `api-client`, `boltzfold`

#### Set Up Branch Protection (recommended)
- Go to Settings → Branches
- Add rule for `main` branch:
  - ☑ Require pull request reviews before merging
  - ☑ Require status checks to pass before merging
  - Select: Tests, Lint

## PyPI Setup

### 1. Prepare PyPI Account

1. Create account at https://pypi.org/account/register/
2. Enable 2FA (required for publishing)
3. Create API token:
   - Go to Account Settings → API tokens
   - Create token with scope: "Entire account" or "Project: boltzfold-client"
   - Save the token (you'll only see it once)

### 2. Configure PyPI Credentials

```bash
# Install twine if not already installed
pip install twine build

# Create ~/.pypirc (optional, can also use token directly)
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your API token here
EOF

chmod 600 ~/.pypirc
```

### 3. Build and Publish

```bash
cd /Users/jules/Documents/code/boltzFoldAll/boltzfold_client

# Build distribution packages
make build
# Or: python -m build

# Check the package
twine check dist/*

# Upload to PyPI
make publish
# Or: twine upload dist/*
```

### 4. Test Installation

```bash
# In a new virtual environment
pip install boltzfold-client

# Verify it works
python -c "from boltzfold_client import BoltzFoldClient; print('Success!')"
```

## Post-Setup Tasks

### 1. Update README.md

Replace placeholder URLs in README.md:
- Change `yourusername` to your actual GitHub username
- Update repository URLs
- Update any other placeholder information

```bash
cd /Users/jules/Documents/code/boltzFoldAll/boltzfold_client

# Use sed or your favorite editor
sed -i '' 's/yourusername/YOUR_GITHUB_USERNAME/g' README.md
sed -i '' 's/yourusername/YOUR_GITHUB_USERNAME/g' pyproject.toml
sed -i '' 's/support@boltzfold.com/YOUR_EMAIL@example.com/g' pyproject.toml

git add README.md pyproject.toml
git commit -m "Update repository URLs and contact info"
git push
```

### 2. Add Badges to README

Add these badges at the top of README.md:

```markdown
[![Tests](https://github.com/yourusername/boltzfold_client/workflows/Tests/badge.svg)](https://github.com/yourusername/boltzfold_client/actions)
[![PyPI](https://img.shields.io/pypi/v/boltzfold-client.svg)](https://pypi.org/project/boltzfold-client/)
[![Python](https://img.shields.io/pypi/pyversions/boltzfold-client.svg)](https://pypi.org/project/boltzfold-client/)
[![Downloads](https://pepy.tech/badge/boltzfold-client)](https://pepy.tech/project/boltzfold-client)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

### 3. Create GitHub Release

After publishing to PyPI:

1. Go to Releases → "Create a new release"
2. Tag version: `v0.1.0`
3. Release title: `v0.1.0 - Initial Release`
4. Copy content from CHANGELOG.md
5. Publish release

### 4. Set Up Dependabot (Optional)

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Documentation Website (Optional)

Consider setting up documentation with Sphinx or MkDocs:

```bash
pip install mkdocs mkdocs-material

mkdocs new docs
# Edit docs/index.md
mkdocs serve  # Preview
mkdocs gh-deploy  # Deploy to GitHub Pages
```

## Continuous Integration

The repository includes a GitHub Actions workflow (`.github/workflows/test.yml`) that:
- Runs tests on Python 3.10, 3.11, 3.12
- Tests on Linux, macOS, and Windows
- Runs linting and type checking
- Reports coverage to Codecov

The workflow runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

## Maintenance

### Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Commit changes: `git commit -m "Bump version to X.Y.Z"`
4. Tag release: `git tag vX.Y.Z`
5. Push: `git push && git push --tags`
6. Build and publish: `make publish`
7. Create GitHub release

### Common Tasks

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Format code
make format

# Lint code
make lint

# Build package
make build

# Clean build artifacts
make clean
```

## Support

For questions or issues with setup, please:
- Open an issue on GitHub
- Contact the maintainers
- Check the documentation at https://boltzfold.com/docs

## Next Steps

After setup is complete:
1. ✅ Test the package locally
2. ✅ Push to GitHub
3. ✅ Publish to PyPI
4. ✅ Update README with actual URLs
5. ✅ Create first release
6. ✅ Announce to users
7. ✅ Monitor issues and feedback

Good luck! 🚀

