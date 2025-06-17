# 🛠️ Git Tips & Commands

A collection of useful Git commands for occasional use.

---

## 🧹 Remove all local branches without remote branch
```bash
# Fetch and prune remote branches, then delete local branches marked as [gone]
git fetch -p && for branch in $(git for-each-ref --format '%(refname) %(upstream:track)' refs/heads | awk '$2 == "[gone]" {sub("refs/heads/", "", $1); print $1}'); do git branch -D $branch; done
```

## 🏷️ Remove all local tags
```bash
# Delete all local tags & fetch them again
git tag -d $(git tag -l) && git fetch
```

## 🔐 Enable GPG signing
```bash
# Enable GPG signing for all commits
git config commit.gpgsign true
```

## 📁 Enable long filename support (Windows)
```bash
# Enable support for long paths (Windows only)
git config --global core.longpaths true
```

## 🔄 Check out PR from fork (GitHub)
```bash
# Check out PR #123 from the upstream (GitHub-style)
git fetch origin pull/123/head:pr-123 && git checkout pr-123

# Alternative version
pr=123 && git fetch origin pull/$pr/head:pr-$pr && git checkout pr-$pr
```