# MinuteTrader Code Workflow

## Branch Strategy
- `main` — production-ready code. Protected. Only merged via PR.
- `feature/*` — feature branches for new strategies, modules, and fixes.

## Workflow
1. Create a feature branch from `main`: `git checkout -b feature/description`
2. Commit work with clear, descriptive messages
3. Push branch and open a Pull Request to `main`
4. The lead reviews the PR using `gh pr review` / `merge_pr`
5. Approved PRs are squash-merged to keep history clean

## Standards
- All new strategies must subclass `BaseStrategy` and return `Signal` objects
- Include tests for every new strategy under `tests/`
- Run `pytest tests/` before opening a PR
- Don't commit API keys — they go in `.env` or environment variables
- Update `requirements.txt` when adding new dependencies