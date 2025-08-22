# Contributing to Code Analysis Bot

Thank you for your interest in contributing to Code Analysis Bot! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenSearch 2.3.0 or higher
- Git
- API keys for at least one LLM service (OpenAI, Perplexity, or Ollama)

### Development Setup

1. **Fork and clone the repository**:
```bash
git clone https://github.com/yourusername/on_call_bot.git
cd on_call_bot
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. **Setup environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Run tests**:
```bash
pytest
```

## 🏗️ Project Structure

```
on_call_bot/
├── core/               # Core business logic
├── services/           # Service layer (embeddings, search, analysis)
├── factories/          # Factory pattern implementations
├── models/             # Data models and schemas
├── ui/                 # Streamlit user interface
├── config/             # Configuration and settings
├── utils/              # Utility functions
├── docs/               # Documentation
├── demos/              # Demo data and examples
└── tests/              # Test files
```

## 📋 Contributing Guidelines

### Code Style

- Follow PEP 8 Python style guide
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

### Testing

- Write unit tests for all new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage
- Include integration tests for new services

### Pull Request Process

1. **Create a feature branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**:
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**:
```bash
pytest
black --check .
flake8
```

4. **Commit your changes**:
```bash
git add .
git commit -m "feat: add your feature description"
```

5. **Push and create pull request**:
```bash
git push origin feature/your-feature-name
```

### Commit Message Format

Use conventional commit messages:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

## 📝 Documentation

- Update README.md for major changes
- Add docstrings to new functions and classes
- Update API documentation in docs/API.md
- Include examples for new features

## 🐛 Bug Reports

When reporting bugs, please include:

1. Python version and OS
2. Steps to reproduce the issue
3. Expected vs actual behavior
4. Error messages and stack traces
5. Configuration details (anonymized)

## 💡 Feature Requests

For new features:

1. Check existing issues first
2. Describe the feature and use case
3. Explain why it would be valuable
4. Consider implementation complexity

## 🔄 Adding New Services

To add a new LLM or embedding service:

1. Create service class in `services/`
2. Add factory implementation in `factories/`
3. Update configuration in `config/settings.py`
4. Add tests and documentation
5. Update README with new service info

## 📞 Getting Help

- Open an issue for bugs or feature requests
- Check existing documentation first
- Ask questions in issue discussions

Thank you for contributing! 🙏
+