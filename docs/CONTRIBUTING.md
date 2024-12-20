# Contributing to Vocality Nexus 🌐🤝

## Welcome Contributors! 🎉

Vocality Nexus is an open-source project dedicated to creating an inclusive, innovative voice transformation platform. We welcome contributions from developers, designers, and community members of all backgrounds.

## Code of Conduct �守

We are committed to providing a friendly, safe, and welcoming environment for all contributors. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started 🚀

### 1. Fork and Clone
1. Fork the repository on GitHub
2. Clone your forked repository
```bash
git clone https://github.com/YOUR_USERNAME/vocality-nexus.git
cd vocality-nexus
```

### 2. Development Environment Setup
#### Backend (Python)
```bash
cd src/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

#### Frontend (React)
```bash
cd src/frontend
npm install
npm install -D  # Development dependencies
```

## Contribution Workflow 🔄

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# OR
git checkout -b bugfix/issue-description
```

### 2. Commit Guidelines
- Use conventional commits: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
- Write clear, descriptive commit messages
- Reference issue numbers when applicable

Example:
```bash
git commit -m "feat: add voice profile sharing functionality #123"
```

### 3. Code Standards

#### Python (Backend)
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions
- Maintain 90%+ test coverage

#### JavaScript/React (Frontend)
- Use ESLint and Prettier
- Follow React best practices
- Write meaningful component and function names
- Use functional components with hooks

### 4. Testing
- Backend: `pytest` with coverage
- Frontend: `react-testing-library`
- Ensure all tests pass before submitting PR

```bash
# Backend testing
pytest --cov=.

# Frontend testing
npm test
```

### 5. Pull Request Process
1. Ensure your code passes all tests
2. Update documentation if needed
3. Submit a pull request with:
   - Clear title
   - Description of changes
   - Related issue numbers
   - Screenshots (if applicable)

## Contribution Areas 🌈

We welcome contributions in:
- 🖥️ Backend development
- 🎨 Frontend design
- 🧪 Testing
- 📖 Documentation
- 🌐 Internationalization
- 🔒 Security improvements
- 🎙️ Voice processing algorithms

## Reporting Issues 🐛
- Use GitHub Issues
- Provide detailed description
- Include reproduction steps
- Specify environment details

## Feature Requests 💡
- Open a GitHub Issue
- Describe the feature
- Provide use cases
- Discuss potential implementation

## Recognition 🏆
All contributors will be recognized in our:
- README.md
- CONTRIBUTORS.md
- Project website

## Questions? 💬
- Open an Issue
- Join our Discord community
- Email: contributors@vocalitynexus.com

Thank you for helping make Vocality Nexus amazing! 🚀🌈
