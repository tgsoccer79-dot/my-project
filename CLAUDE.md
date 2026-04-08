# CLAUDE.md

This file provides guidance for AI assistants (Claude Code and others) working in this repository.

## Repository Status

This is a newly initialized repository with no source code yet. This CLAUDE.md should be updated as the project evolves to reflect the actual stack, conventions, and workflows.

## Git Workflow

- **Default development branch**: `main` (or as configured)
- **Feature branches**: `claude/<description>-<id>` for AI-driven work; `feat/<description>` for human-driven work
- **Commit style**: Use concise imperative-mood messages (e.g., `add user auth`, `fix null pointer in parser`)
- Always commit with meaningful messages — avoid generic messages like "update files" or "fix stuff"
- Never force-push to `main` or shared branches without explicit approval
- Never skip pre-commit hooks (`--no-verify`) unless explicitly instructed

## Development Setup

> Update this section once a tech stack is chosen.

```bash
# Clone and enter the repo
git clone <repo-url>
cd my-project

# Install dependencies (update with actual commands)
# npm install       # Node.js
# pip install -e .  # Python
# cargo build       # Rust
# go mod download   # Go
```

## Build, Test, and Lint

> Update with actual commands once the project is set up.

```bash
# Build
# npm run build / make build / cargo build

# Run tests
# npm test / pytest / cargo test / go test ./...

# Lint / format
# npm run lint / ruff check . / cargo clippy / golangci-lint run
```

## Project Structure

> Update this section as directories are created.

```
my-project/
├── CLAUDE.md          # This file
└── (project files TBD)
```

## Coding Conventions

These apply regardless of language unless overridden by language-specific tooling:

- **Naming**: Use descriptive, unambiguous names. Prefer clarity over brevity.
- **Functions**: Keep functions small and single-purpose.
- **Comments**: Only comment non-obvious logic. Code should be self-documenting where possible.
- **Error handling**: Handle errors explicitly at system boundaries; don't swallow errors silently.
- **Security**: Never hardcode secrets, API keys, or credentials. Use environment variables or a secrets manager.
- **Dependencies**: Prefer well-maintained libraries. Avoid adding dependencies for trivial tasks.

## AI Assistant Guidelines

- **Read before editing**: Always read a file before modifying it.
- **Minimal changes**: Make only the changes needed to satisfy the task — no speculative refactors or "while I'm here" improvements.
- **No hallucinated APIs**: Only use APIs/functions you've confirmed exist in the codebase or official documentation.
- **No new files without reason**: Prefer editing existing files over creating new ones unless a new file is clearly warranted.
- **No generated docs**: Don't create README or documentation files unless explicitly requested.
- **Confirm destructive actions**: Always confirm before deleting files, dropping data, or force-pushing.
- **Test your changes**: Run the test suite after making changes if tests exist.
- **One concern per commit**: Keep commits focused — don't bundle unrelated changes.

## Environment Variables

> Document required environment variables here as they are introduced.

```
# Example:
# DATABASE_URL=...
# API_KEY=...
```

## Notes for Future Updates

When the project stack is chosen, update this file with:
1. Actual build/test/lint commands
2. Real project structure
3. Language-specific conventions (e.g., Python type hints, TypeScript strict mode)
4. CI/CD pipeline details
5. Deployment workflow
6. Any third-party service integrations
