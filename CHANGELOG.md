# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-06-22

This release upgrades the project to a robust, portfolio-ready codebase containing professional infrastructure, test coverages, and design patterns.

### Added
- **Automated Tests**: Unit and integration test suite in `tests/` utilizing `pytest` and `pytest-mock`.
- **Project Versioning**: Set versioning base in `src/__init__.py` using SemVer standards.
- **Developer Guide**: Comprehensive [DEVELOPER_GUIDE.md](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/DEVELOPER_GUIDE.md) detailing architecture, design patterns, resource cleanups, and extension instructions.
- **Changelog Tracking**: Established this `CHANGELOG.md` for historical release tracking.
- **Logging Integration**: Configured standard Python `logging` to output timestamps and module levels.
- **Docstrings documentation**: Comprehensive Google-style docstrings added for all methods and classes.

### Changed
- **Config Decoupling**: Moved hardcoded target URL, maximum pricing budget, and check intervals from [main.py](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/src/main.py) to [.env](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/.env) variables.
- **Resource Management**: Enhanced Selenium Firefox Webdriver lifecycle inside [scraper.py](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/src/scraper.py) to guarantee termination using strict `try...finally` scopes.
- **Connection Optimization**: Configured a global `requests.Session` persistent pool inside [utils.py](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/src/utils.py) to enable TCP connection keep-alive reuse for telegram notifications.
- **Documentation Overhaul**: Revamped [README.md](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/README.md) to include visual Mermaid diagrams and full command workflows.

### Fixed
- **Unicode Token Typo**: Resolved a major connection bug where a Cyrillic character `К` was hardcoded inside the `TELEGRAM_TOKEN` within the [.env](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/.env) file.
- **Fallback Exception Safety**: Fixed missing generic `analyze_prices` parser execution in [scraper.py](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/src/scraper.py) to prevent crash hazards when executing non-Mercado Libre URL searches.
