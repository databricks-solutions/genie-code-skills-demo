# Branch Conventions

This repository has GitHub rulesets that enforce branch naming and merge policies.

## Branch Naming

All branches must match the pattern: `^(feature|bugfix)\/[a-z0-9-]+`

- `feature/<lowercase-kebab>` for new features (e.g., `feature/add-ml-skills`)
- `bugfix/<lowercase-kebab>` for bug fixes (e.g., `bugfix/fix-deploy-script`)

No other prefixes are allowed. Names must be lowercase with hyphens only (no underscores, no uppercase).

## Main Branch Protection

- No direct pushes to `main`.
- All changes require a pull request.
- PRs require at least 1 approving review.
- Stale reviews are dismissed on new pushes.
- All review threads must be resolved before merge.
- Branch deletion and non-fast-forward pushes are blocked on `main`.
