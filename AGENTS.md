# AGENTS.md - investAssis

## Project Overview

- **Project name**: investAssis (投资分析助手)
- **Type**: Python project / Openclaw plugin
- **Python version**: 3.9+ (see `.python-version`)
- **Package manager**: pyproject.toml (PEP 517/518)
- **Description**: Investment analysis assistant system integrated with Openclaw platform

## Project Structure

```
investAssis/
├── .venv/                  # Virtual environment (gitignored)
├── .env                    # Environment variables (gitignored)
├── .python-version         # Python version (3.9)
├── pyproject.toml          # Project configuration
├── docker-compose.yaml     # Openclaw container setup
├── README.md               # Project documentation
├── research-workspace/     # Research agent workspace
│   ├── knowledge/          # Knowledge base files
│   └── skills/             # Research skills
├── trading-workspace/      # Trading agent workspace
│   ├── skills/             # Trading skills
│   └── trading-logs/       # Trading logs
├── reflection-workspace/   # Reflection/feedback workspace
├── mcp-servers/            # MCP server configurations
├── scripts/                # Utility scripts
└── data/                   # Data files
```

## Build Commands

### Python Environment
```bash
# Create virtual environment (if not exists)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e .

# Install dev dependencies (when added)
pip install -e ".[dev]"
```

### Docker
```bash
# Start openclaw container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down
```

### Testing
**No tests currently exist.** When adding tests, use pytest:

```bash
# Run all tests
pytest

# Run single test file
pytest tests/test_file.py

# Run single test function
pytest tests/test_file.py::test_function_name

# Run with coverage
pytest --cov=src --cov-report=html
```

### Linting & Formatting
**No linting/formatting config currently exists.** When adding, use:

```bash
# ruff (recommended - fast, all-in-one)
ruff check .
ruff format .

# mypy type checking
mypy src/

# pytest for testing
pytest
```

## Code Style Guidelines

Since this is a greenfield project, follow these conventions for any new Python code:

### Imports
```python
# Standard library first
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

# Third-party packages
import pandas as pd
from pydantic import BaseModel

# Local imports (relative)
from . import utils
from .models import User

# No wildcard imports
from module import *  # NEVER
```

### Formatting
- **Line length**: 100 characters max
- **Indentation**: 4 spaces (no tabs)
- **Blank lines**: 2 between top-level definitions, 1 between functions
- **Trailing whitespace**: Never

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`
- **Type aliases**: `TypeName`

```python
# Good
class InvestmentReport:
    def calculate_returns(self, principal: float, rate: float) -> float:
        """Calculate investment returns."""
        _internal_cache = {}
        MAX_POSITION_SIZE = 100000

# Bad
class investment_report:  # Classes should be PascalCase
    def CalculateReturns(self):  # Functions should be snake_case
        pass
```

### Types
- **Always use type hints** for function signatures
- **Use Pydantic** for data validation models
- **Avoid `Any`** - be as specific as possible
- **Use Optional** instead of `| None`

```python
# Good
def process_stock_data(symbol: str, prices: List[float]) -> Optional[Dict[str, Any]]:
    pass

# Avoid
def process_stock_data(symbol, prices):  # No type hints
    pass

def process_stock_data(symbol: Any, prices: Any) -> Any:  # Too general
    pass
```

### Error Handling
- **Use custom exceptions** for domain-specific errors
- **Never swallow exceptions silently**
- **Log errors** before re-raising
- **Use context managers** for resource management

```python
# Good
class InsufficientDataError(Exception):
    """Raised when not enough data to perform analysis."""
    pass

def analyze_stock(symbol: str) -> AnalysisResult:
    try:
        data = fetch_data(symbol)
        if not data:
            raise InsufficientDataError(f"No data available for {symbol}")
        return AnalysisResult.process(data)
    except InsufficientDataError:
        raise  # Re-raise domain errors
    except Exception as e:
        logger.error(f"Failed to analyze {symbol}: {e}")
        raise  # Or handle appropriately

# Bad
def analyze_stock(symbol: str):
    try:
        return AnalysisResult.process(fetch_data(symbol))
    except:  # Never bare except
        pass  # Silent swallowing
```

### Documentation
- **All public functions** need docstrings (Google or NumPy style)
- **Complex logic** needs inline comments explaining why, not what
- **Classes** should have docstrings describing purpose

```python
def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """Calculate the Sharpe ratio for a series of returns.

    Args:
        returns: List of periodic returns (e.g., daily or monthly).
        risk_free_rate: Annual risk-free rate (default 2%).

    Returns:
        Sharpe ratio as a float. Higher is better.

    Raises:
        ValueError: If returns list is empty or has zero variance.

    Example:
        >>> returns = [0.01, 0.02, -0.01, 0.03]
        >>> calculate_sharpe_ratio(returns)
        1.25
    """
```

### Project-Specific Conventions

1. **Workspace files**: All workspace content (knowledge, skills) goes in respective subdirectories
2. **Environment variables**: Store in `.env`, never commit secrets
3. **Logging**: Use structured logging with appropriate levels
4. **Configuration**: Use Pydantic BaseSettings for config management

## Git Conventions

- **Commits**: Use clear, concise commit messages describing what and why
- **Branches**: `feature/description` or `fix/description` format
- **Never commit**: `.env`, `*.pyc`, `__pycache__/`, `.venv/`, secrets

## Cursor/Copilot Rules

No Cursor or Copilot rules found in this repository.

## Notes for Agents

1. This is a **greenfield project** - no existing code to reference
2. The project is designed as an **Openclaw plugin** - code should follow Openclaw's conventions
3. **Test first** when adding significant functionality
4. **Keep it simple** - this is an investment analysis tool, not a framework
5. **Document decisions** - add comments explaining investment logic
