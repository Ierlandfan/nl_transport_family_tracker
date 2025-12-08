# Contributing to Dutch Public Transport Family Tracker

Thank you for your interest in contributing! 

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/nl_transport_family_tracker/issues)
2. If not, create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Home Assistant version
   - Integration version
   - Relevant logs

### Feature Requests

1. Check [existing feature requests](https://github.com/yourusername/nl_transport_family_tracker/issues?q=is%3Aissue+label%3Aenhancement)
2. Create a new issue describing:
   - The feature you'd like
   - Why it would be useful
   - How you envision it working

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/nl_transport_family_tracker.git
cd nl_transport_family_tracker

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements_dev.txt

# Run tests
pytest tests/
```

### Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to functions
- Keep functions focused and small
- Write tests for new features

### Testing

Before submitting a PR:
- Test the integration in a real Home Assistant instance
- Verify config flow works correctly
- Check that existing functionality isn't broken
- Test with different station types (bus, tram, train)

## Questions?

Feel free to ask in [Discussions](https://github.com/yourusername/nl_transport_family_tracker/discussions)
