# 🤝 Contributing to ServeBeer IPFS CDN

Thank you for your interest in contributing to ServeBeer! This project is part of the **NFTomczain Universe** - a philosophy of technological resistance and decentralized infrastructure.

## 🌟 Code of Conduct

We believe in:
- **Decentralization over centralization**
- **Privacy over surveillance** 
- **Community over corporations**
- **Open source over proprietary**
- **Accessibility for all**

Be respectful, inclusive, and constructive in all interactions.

## 🚀 Getting Started

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/servebeer-ipfs.git
   cd servebeer-ipfs
   ```

2. **Run Setup Script**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

3. **Activate Environment**
   ```bash
   source venv/bin/activate
   ```

4. **Start Development Server**
   ```bash
   python app.py
   ```

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make Changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Test Everything**
   ```bash
   # Run tests
   python -m pytest
   
   # Check formatting
   black --check .
   
   # Check linting
   flake8 .
   
   # Test manually
   python app.py
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   git push origin feature/amazing-feature
   ```

5. **Create Pull Request**
   - Describe what your PR does
   - Link any related issues
   - Add screenshots if UI changes

## 📋 Types of Contributions

### 🐛 Bug Reports
- Use GitHub Issues template
- Include steps to reproduce
- Provide system information
- Add logs if relevant

### 💡 Feature Requests  
- Describe the problem you're solving
- Explain your proposed solution
- Consider alternatives
- Think about implementation impact

### 🔧 Code Contributions

**Priority Areas:**
- IPFS integration improvements
- Security enhancements
- Performance optimizations
- Mobile responsiveness
- Multi-language support
- Documentation improvements

**Architecture Guidelines:**
- Keep it simple and maintainable
- Follow Flask best practices
- Minimize dependencies
- Prioritize security
- Consider Raspberry Pi constraints

### 📚 Documentation
- Fix typos and unclear sections
- Add examples and tutorials
- Improve API documentation
- Translate to other languages

## 🎯 Development Guidelines

### Code Style
```python
# Use Black formatter (automatic)
black .

# Follow PEP 8 guidelines
flake8 .

# Write descriptive variable names
user_storage_limit = get_user_tier_limit(user_id)

# Add docstrings for functions
def pin_ipfs_content(cid: str, user_id: int) -> dict:
    """Pin IPFS content to local node.
    
    Args:
        cid: IPFS Content Identifier
        user_id: Database user ID
        
    Returns:
        dict: Pin operation result
    """
```

### Testing
```python
# Write tests for new functions
def test_pin_valid_cid():
    """Test pinning valid IPFS CID."""
    result = pin_ipfs_content("QmTest123", user_id=1)
    assert result["success"] == True

# Test edge cases
def test_pin_invalid_cid():
    """Test pinning invalid CID fails gracefully."""
    result = pin_ipfs_content("invalid", user_id=1)
    assert "error" in result
```

### Security Considerations
- Never commit secrets or API keys
- Validate all user inputs
- Use prepared SQL statements
- Implement rate limiting
- Log security events
- Follow least privilege principle

### Performance
- Optimize IPFS API calls
- Cache frequently accessed data
- Minimize database queries
- Consider Raspberry Pi limitations
- Profile before optimizing

## 🏗️ Project Structure

```
servebeer-ipfs/
├── app.py              # Main Flask application
├── config/             # Configuration management
├── static/             # CSS, JS, images
├── templates/          # HTML templates
├── tests/              # Test files
├── scripts/            # Setup and deployment scripts
├── docs/               # Documentation
└── database/           # SQLite database
```

## 🧪 Testing

### Running Tests
```bash
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_ipfs.py

# With coverage
python -m pytest --cov=app

# Integration tests
python -m pytest tests/test_integration.py
```

### Writing Tests
- Test both success and failure cases
- Mock external IPFS calls
- Use pytest fixtures for setup
- Test security boundaries
- Include performance tests for critical paths

## 📦 Release Process

1. **Update Version Numbers**
   - Update in app.py
   - Update in setup.py if exists
   - Update in documentation

2. **Update Changelog**
   - Document new features
   - List bug fixes
   - Note breaking changes

3. **Create Release**
   - Tag with semantic version
   - Create GitHub release
   - Update Docker images

## 🎨 UI/UX Guidelines

- **Mobile-first design**
- **Dark theme default** (guerrilla aesthetic)
- **Cyberpunk elements** (fits NFTomczain universe)
- **Accessibility features** (screen readers, keyboard navigation)
- **Fast loading** (consider slow connections)

### Design Colors
- Primary: `#4ECDC4` (teal)
- Secondary: `#2C3E50` (dark blue)
- Accent: `#F39C12` (orange)
- Success: `#27AE60` (green)
- Warning: `#E67E22` (orange)
- Error: `#E74C3C` (red)

## 🌍 Internationalization

Help make ServeBeer accessible worldwide:

**Priority Languages:**
- Polish (native)
- English (global)
- Spanish (Latin America)
- French (Europe/Africa)
- Portuguese (Brazil)
- Chinese (Asia)
- Russian (Eastern Europe)

## 💰 Financial Contributions

Support the guerrilla infrastructure:

- **Cryptocurrency donations** (see README.md for addresses)
- **Sponsor hosting costs** 
- **Fund development hardware**
- **Support community events**

## 🔗 Community

- **GitHub Issues:** Bug reports and features
- **GitHub Discussions:** General questions
- **Discord:** Real-time chat (coming soon)
- **Matrix:** Decentralized chat (coming soon)

## 🏆 Recognition

Contributors get:
- **GitHub credit** in all commits
- **Mentions in releases**
- **Special badges** on community platforms
- **Beta access** to new features
- **Swag** for major contributions (stickers, t-shirts)

## 📜 Philosophy Integration

Remember that ServeBeer is part of a larger movement:

- **NFTomczain:** Personal technology survival
- **NetNeroJes:** Global decentralization resistance  
- **Pi-Grade:** Practical infrastructure development

Your contributions support not just a project, but a **philosophy of technological resistance**.

## 🚨 Emergency Contact

For security issues or urgent matters:
- Create **private GitHub issue**
- Email: `security@[domain-when-ready].com` 
- Matrix: `@nftomczain:matrix.org` (coming soon)

---

## 🙏 Thank You

Every contribution matters in building the **ghost layer** - the decentralized infrastructure that exists parallel to corporate systems.

**"🔥 We are the fire beneath the ashes. 🌍 We build the ghost layer."**

*Welcome to the resistance. Welcome to ServeBeer.*