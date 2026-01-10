# Security Checklist for Public Repository

## ✅ Already Fixed

1. **`config.py`** - Default API URLs changed from real IPs to `localhost`
2. **Test Fixtures** - All personal information sanitized:
   - Real IP addresses replaced with example IPs (`192.168.1.100`)
   - Personal usernames replaced with `exampleuser`
   - Device names replaced with `Example Device`
   - Plex user IDs replaced with `example123456789`
   - Machine identifiers replaced with `example-machine-identifier-12345`
   - File paths sanitized

## ⚠️ Critical - Verify Before Committing

### 1. **`data/api_config.json`** - Contains Real Credentials
   - ✅ Already in `.gitignore` (line 34)
   - ⚠️ **ACTION REQUIRED**: Verify this file is NOT tracked:
     ```bash
     git ls-files | grep api_config.json
     # Should return nothing
     ```
   - If it IS tracked, remove it:
     ```bash
     git rm --cached data/api_config.json
     ```
   - **Contains**: Real Plex API token, real IP addresses, API keys

### 2. **`data/slides.json`** - Contains Your Configuration
   - ✅ Already in `.gitignore` (line 33)
   - ⚠️ **ACTION REQUIRED**: Verify this file is NOT tracked

### 3. **Verify No Credentials in Code**
   Run this check before committing:
   ```bash
   # Check for hardcoded credentials (should return minimal/no results)
   git grep -iE "(api_key|api_token|password|secret|credential)" -- '*.py' '*.js' | grep -v "\.gitignore" | grep -v "example\|placeholder\|masked"
   ```

## 📋 Additional Checks

### Files Already Protected by `.gitignore`:
- ✅ `data/api_config.json` - API credentials
- ✅ `data/slides.json` - Slide configuration
- ✅ `data/preview/` - Preview images
- ✅ `*.log` - Log files
- ✅ `.env` - Environment variables

### What to Check Before Each Commit:
1. **No API tokens/keys in code** - All credentials should be in `data/api_config.json` (gitignored)
2. **No real IP addresses** - Default configs use `localhost` or example IPs
3. **No personal information** - Test fixtures use example data
4. **Debug logs** - Ensure no credentials leak into debug logs (they're masked, but double-check)

## 🔒 Best Practices for Users

If someone forks/clones this repo, they should:

1. **Never commit `data/api_config.json`** - This file is gitignored for a reason
2. **Use environment variables** (optional but recommended):
   ```bash
   export PLEX_API_TOKEN="your-token"
   export ARM_API_KEY="your-key"
   ```
3. **Configure via web UI** - The web UI stores credentials in `data/api_config.json` (which is gitignored)

## ✅ Final Checklist Before Public Release

- [ ] Run `git ls-files` and verify `data/api_config.json` is NOT listed
- [ ] Run `git ls-files` and verify `data/slides.json` is NOT listed
- [ ] Search codebase for any hardcoded credentials (see command above)
- [ ] Verify all test fixtures use example data only
- [ ] Review `.gitignore` to ensure all sensitive files are listed
- [ ] Check git history: `git log --all --full-history -- "data/api_config.json"` (should be empty)
- [ ] Consider adding a `.env.example` file if using environment variables

## 🚨 If You've Already Committed Sensitive Data

If `data/api_config.json` was accidentally committed:

1. **Remove from git tracking** (keeps local file):
   ```bash
   git rm --cached data/api_config.json
   ```

2. **Remove from git history** (if already pushed):
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch data/api_config.json" \
     --prune-empty --tag-name-filter cat -- --all
   ```

3. **Force push** (⚠️ This rewrites history):
   ```bash
   git push origin --force --all
   ```

4. **Rotate all exposed credentials immediately** - Assume they're compromised

