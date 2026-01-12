---
allowed-tools: Bash, Read, Grep, Glob
description: Create a git commit following the project's commit message style
---

# Commit Command

Create a git commit following the project's commit message conventions.

## Commit Message Format

```
[Verb] [brief description]. [Verb] [brief description]. ...
```

## Guidelines

- **Keep it short and concise** - Brief, action-oriented statements
- **Use simple present tense** - "Add", "Fix", "Improve", not "Added" or "Adding"
- **Multiple changes** - Separate with periods, list main changes only
- **Focus on what, not why** - Describe the change, not the reason
- **No detailed explanations** - Save details for PR descriptions

## Common Verbs

| Verb     | Use For                                    |
|----------|--------------------------------------------|
| Add      | New features, files, or functionality      |
| Fix      | Bug fixes, corrections                     |
| Improve  | Enhancements to existing features          |
| Update   | Modifications, version bumps               |
| Remove   | Deletions, cleanup                         |
| Refactor | Code restructuring without behavior change |
| Move     | File/directory relocations                 |
| Rename   | Name changes                               |

## Examples

**Single change:**

```
Add hunt mode
Fix draw handler
Improve codebase
```

**Multiple changes:**

```
Add hunt overview. Fix countdown regex. Improve hunt scheduling. Fix icon colors.
Update theme colors, enhance UI components, and modify configuration files for version 1.8
Enhance image handling and modal management in bot operations
```

## Anti-Patterns

- Don't use past tense ("Added", "Fixed")
- Don't use present continuous ("Adding", "Fixing")
- Don't include issue numbers unless required
- Don't write multi-line commit messages for routine changes
- Don't explain implementation details in commit message

## Workflow

1. Run `git status` to see changes
2. Run `git diff --staged` to review staged changes (or `git diff` for unstaged)
3. Run `git log -3 --oneline` to see recent commit style
4. Analyze changes and draft a commit message following the format above
5. Stage files with `git add` if needed
6. Create commit using HEREDOC format:

```bash
git commit -m "$(cat <<'EOF'
[Your commit message here]

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```
