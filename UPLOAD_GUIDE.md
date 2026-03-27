# Upload Guide

This folder is the upload-ready copy of the site.

Current path:

`C:\Users\25472\projects\methods\mokaoai.com-private-upload`

What was intentionally left out:

- `database/`
- `AAAAAA/`
- `A------MCP/`
- `_next/`
- local logs and scratch inspection files

What is included:

- site pages and assets
- `mock-data/`
- scripts used by this project
- current `WORKLOG.md`

## First push to a private GitHub repository

1. Create a new private repository on GitHub.
2. Do not add a README, license, or `.gitignore` there.
3. In PowerShell:

```powershell
cd C:\Users\25472\projects\methods\mokaoai.com-private-upload
git init
git add .
git commit -m "Initial private upload"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git
git push -u origin main
```

## Later updates

```powershell
cd C:\Users\25472\projects\methods\mokaoai.com-private-upload
git add .
git commit -m "update"
git push
```
