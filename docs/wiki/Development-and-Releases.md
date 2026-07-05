# Development and Releases

This page is for maintainers.

## Branching

Use feature branches for work. Keep `main` publishable.

For Codex-generated branches in this workspace, the branch prefix is usually:

```text
codex/
```

## Local Verification

Run before pushing:

```bash
python tests/verify_repo.py
python -m unittest discover -s tests -p "test_*.py"
npm test
npm run smoke
npm run check:install-surfaces
node tests/test_mcp_shrink.js
npm pack --dry-run --json
```

## Package Verification

Check important files are included:

```bash
npm pack --dry-run --json
```

The package should include:

- `bin/`
- `src/`
- `skills/`
- `plugins/`
- `commands/`
- `benchmarks/`
- `evals/`
- `docs/`

It should not include:

- `__pycache__`
- `.pyc`

## Sync Rules

When editing mirrored content, sync copies:

| Source | Mirror |
|---|---|
| `agents/` | `plugins/signaltrim/agents/` |
| `skills/signaltrim-compress/` | `plugins/signaltrim/skills/signaltrim-compress/` |
| `skills/signaltrim/` | `plugins/signaltrim/skills/signaltrim/` |

Run:

```bash
python tests/verify_repo.py
```

## Cloudflare Pages

The launch site is static under:

```text
docs/
```

Deploy:

```bash
npx wrangler pages deploy docs --project-name signaltrim --branch main
```

Verify:

```bash
npx wrangler pages deployment list --project-name signaltrim
```

Live URL:

```text
https://signaltrim.pages.dev/
```

## GitHub Wiki

The wiki is a separate git repository:

```text
https://github.com/karurikwao/signaltrim.wiki.git
```

Clone after first publish:

```bash
git clone https://github.com/karurikwao/signaltrim.wiki.git
```

Pages are plain Markdown files. `Home.md` is the landing page. `_Sidebar.md` controls navigation.

Publish or sync the live Wiki tab:

```bash
tmp="$(mktemp -d)"
git clone https://github.com/karurikwao/signaltrim.wiki.git "$tmp"
cp docs/wiki/*.md "$tmp"/
git -C "$tmp" status --short
git -C "$tmp" add *.md
git -C "$tmp" commit -m "docs: sync wiki"
git -C "$tmp" push origin HEAD
```

After pushing, verify:

- `https://github.com/karurikwao/signaltrim/wiki`
- `_Sidebar.md` navigation.
- `_Footer.md` privacy footer.
- Links to repo docs under `docs/`.

## Release Checklist

Use the full maintainer checklist:

```text
docs/RELEASE-CHECKLIST.md
```

The automated release workflow is:

```text
.github/workflows/release.yml
```

It builds the npm tarball, source archives, checksums, and platform launch bundles for Windows, macOS, and Linux.

The recurring verification workflow is:

```text
.github/workflows/scheduled-verification.yml
```

Manual launch checks still matter:

1. Confirm worktree clean before release prep.
2. Run full test matrix.
3. Run package dry-run.
4. Search for stale public links and old install commands.
5. Push `main`.
6. Sync the GitHub Wiki from `docs/wiki/`.
7. Deploy Cloudflare Pages from `docs/`.
8. Verify live page and GIF.
9. Confirm GitHub install path:

```bash
npx -y github:karurikwao/signaltrim -- --dry-run --list
```

## Stale Reference Audit

Before release, search shipped docs for:

- Old domains.
- Bare npm commands that are not published.
- Numbered issue URLs used as public documentation links.
- Legacy upstream names or old repo commands.

The only acceptable hits should be test strings or historical git history, not shipped public docs.

## Commit Style

Use concise, conventional-ish subjects:

```text
fix: harden installer dry-run
docs: publish wiki
chore: sync skill mirrors
```
