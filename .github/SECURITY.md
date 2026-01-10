# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |

## Security Considerations for Public Repository

If you're running this on a public repository, please ensure:

1. **Never commit `data/api_config.json`** - This file contains API keys and tokens
   - Already in `.gitignore`, but double-check before committing
   - Contains sensitive credentials for ARM, Pi-hole, and Plex APIs

2. **Never commit `data/slides.json`** - This file contains your slide configuration
   - Already in `.gitignore`, but verify it's not committed

3. **Configuration files** - The default config in `config.py` uses example values
   - Replace with your actual API endpoints via the web UI after installation
   - API keys/tokens should only be stored in `data/api_config.json` (which is gitignored)

4. **Test fixtures** - Already sanitized to use example data
   - No real credentials, IP addresses, or personal information

5. **Environment variables** - Consider using environment variables for sensitive data:
   - `PLEX_API_TOKEN`, `ARM_API_KEY`, `PIHOLE_API_TOKEN`
   - `.env` file is already in `.gitignore`

6. **Before pushing to public repo:**
   ```bash
   # Verify sensitive files aren't tracked
   git status
   git ls-files | grep -E "(api_config|slides\.json)"
   
   # Check for any credentials in tracked files
   git grep -i "api_key\|api_token\|password\|secret" -- '*.py' '*.js' '*.json' | grep -v ".gitignore"
   ```

## Reporting a Vulnerability

If you discover a security vulnerability, please report it via email rather than opening a public issue.
