# Public Repository Compliance

This is a **Completely Public** repository in the `databricks-solutions` GitHub organization. Every file is subject to external review. Treat every line of code, every comment, and every configuration value as if a customer will read it.

## Hard Rules

- **No non-public information.** No customer data, PII, or proprietary information of any kind.
- **No credentials.** No access tokens, PATs, passwords, API keys, or secrets in any file -- including examples, comments, and documentation.
- **No internal references.** Never include workspace URLs, catalog names, schema names, CLI profile names, email addresses, usernames, team names, secret scope names, or connection names that identify an internal Databricks deployment.
- **Synthetic data only.** All data in this repository must be synthetically generated using tools like `dbldatagen`, Faker, or standard random generation libraries. Never use real data.
- **Third-party attribution.** All third-party code or assets must be acknowledged with their license in the repository.
- **Peer review required.** All published content must be peer reviewed by at least one team member before merging to main.
- **Annual review.** This repository will be reviewed annually by the repo owners and archived if no longer needed.
- **Security reporting.** If any security or legal violations are identified, repo owners will take timely action to remediate.

## Before Every Commit

Ask yourself:
1. Does this file contain any real workspace URL, catalog, schema, or profile name?
2. Does this file contain any token, password, or secret -- even in a comment?
3. Does this file reference any internal project, team, or person by name?
4. Could any data in this file be traced back to a real person or organization?

If the answer to any of these is yes, **do not commit**.
