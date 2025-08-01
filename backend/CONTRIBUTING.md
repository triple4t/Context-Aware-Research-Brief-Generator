# Contributing to Context-Aware Research Brief Generator

Thank you for your interest in contributing to the Context-Aware Research Brief Generator! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Git
- API keys for OpenAI, Anthropic, and Tavily (for testing)

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/your-username/research-brief-generator.git
   cd research-brief-generator/backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

5. **Run tests to verify setup**:
   ```bash
   pytest
   ```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all functions and classes
- Keep functions focused and single-purpose

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── schemas.py         # Pydantic models
│   ├── llm_setup.py      # LLM configuration
│   ├── tools.py           # Search and scraping tools
│   ├── state.py           # Graph state definition
│   ├── nodes.py           # Graph nodes
│   ├── graph.py           # LangGraph assembly
│   ├── storage.py         # Data storage
│   ├── main.py            # FastAPI application
│   └── cli.py             # CLI interface
├── tests/
│   ├── test_schemas.py    # Schema tests
│   └── test_graph.py      # Graph execution tests
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Testing

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use pytest for testing
- Mock external dependencies in tests

### Example Test Structure

```python
def test_new_feature():
    """Test description."""
    # Arrange
    input_data = {...}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result.expected_property == expected_value
```

## 🔧 Making Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, focused commits
- Use descriptive commit messages
- Keep commits atomic and logical

### 3. Add Tests

- Write unit tests for new functions
- Write integration tests for new features
- Ensure all tests pass

### 4. Update Documentation

- Update README.md if needed
- Add docstrings to new functions
- Update API documentation if applicable

### 5. Run Quality Checks

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Check code style (if you have flake8 installed)
flake8 app/

# Type checking (if you have mypy installed)
mypy app/
```

### 6. Submit a Pull Request

1. Push your branch to your fork
2. Create a pull request
3. Fill out the PR template
4. Request review from maintainers

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment details**: OS, Python version, dependencies
2. **Steps to reproduce**: Clear, step-by-step instructions
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Error messages**: Full error traceback
6. **Additional context**: Any relevant information

## 💡 Feature Requests

When requesting features, please include:

1. **Problem description**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Use cases**: Examples of how it would be used
4. **Alternatives considered**: Other approaches you've considered

## 📋 Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass

## Documentation
- [ ] README updated
- [ ] API docs updated
- [ ] Code comments added

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code is commented
- [ ] Documentation is updated
```

## 🏷️ Versioning

We use [Semantic Versioning](https://semver.org/) for version numbers:

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## 📞 Communication

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Code Review**: All changes require review before merging

## 🎯 Areas for Contribution

### High Priority
- Performance optimizations
- Additional LLM providers
- Enhanced error handling
- More comprehensive tests

### Medium Priority
- Additional search tools
- Caching improvements
- User analytics
- Advanced filtering options

### Low Priority
- Documentation improvements
- Code style improvements
- Minor bug fixes
- Test coverage improvements

## 🚨 Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Help others learn and grow
- Welcome newcomers

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Context-Aware Research Brief Generator! 🚀 