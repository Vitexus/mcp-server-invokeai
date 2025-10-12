# Publishing Guide

This guide explains how to publish the InvokeAI MCP Server to PyPI and the MCP Registry.

## Prerequisites

Before publishing, ensure you have:

1. **GitHub Account**: With write access to the repository
2. **PyPI Account**: Create at https://pypi.org/account/register/
3. **Test PyPI Account**: Create at https://test.pypi.org/account/register/
4. **Git**: Latest changes committed and pushed

## Publishing Workflow

### Step 1: Prepare the Release

1. **Update Version Number**

   Edit `pyproject.toml` and update the version:
   ```toml
   version = "1.0.1"  # Increment as needed
   ```

2. **Update CHANGELOG.md**

   Document all changes in the new version:
   ```markdown
   ## [1.0.1] - 2025-MM-DD

   ### Added
   - New feature X

   ### Fixed
   - Bug fix Y
   ```

3. **Update DEVELOPMENT_STATUS.md**

   Add a summary of the release session at the top of the file.

4. **Commit Changes**
   ```bash
   git add pyproject.toml CHANGELOG.md DEVELOPMENT_STATUS.md
   git commit -m "chore: Prepare release v1.0.1"
   git push origin main
   ```

### Step 2: Test Build Locally

Before publishing, test the build locally:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the package
twine check dist/*

# Test in a clean virtual environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate
pip install dist/invokeai_mcp_server-1.0.1-py3-none-any.whl
python -c "import invokeai_mcp_server; print('Import successful')"
deactivate
rm -rf test_env
```

### Step 3: Publish to Test PyPI (Optional but Recommended)

Test the full publishing workflow on Test PyPI first:

1. **Configure PyPI Trusted Publishing**

   Go to https://test.pypi.org/manage/account/publishing/ and add:
   - **PyPI Project Name**: `invokeai-mcp-server`
   - **Owner**: `coinstax` (GitHub username/org)
   - **Repository name**: `invokeai-mcp-server`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: `testpypi`

2. **Trigger Test Publish**

   Go to GitHub Actions and manually trigger the workflow:
   - Navigate to: **Actions** → **Publish to PyPI**
   - Click **Run workflow**
   - Select environment: `testpypi`
   - Click **Run workflow**

3. **Verify on Test PyPI**

   Check https://test.pypi.org/project/invokeai-mcp-server/

4. **Test Installation from Test PyPI**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ invokeai-mcp-server
   ```

### Step 4: Publish to Production PyPI

Once testing is complete, publish to production PyPI:

1. **Configure PyPI Trusted Publishing**

   Go to https://pypi.org/manage/account/publishing/ and add:
   - **PyPI Project Name**: `invokeai-mcp-server`
   - **Owner**: `coinstax` (GitHub username/org)
   - **Repository name**: `invokeai-mcp-server`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: `pypi`

2. **Create GitHub Release**

   Create a new release on GitHub:
   ```bash
   # Create and push a tag
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```

   Or create via GitHub UI:
   - Go to **Releases** → **Draft a new release**
   - Tag: `v1.0.1`
   - Title: `v1.0.1`
   - Description: Copy from CHANGELOG.md
   - Click **Publish release**

3. **Automatic Publication**

   The GitHub Action will automatically:
   - Build the package
   - Publish to PyPI
   - Sign the artifacts with Sigstore
   - Upload artifacts to GitHub Release

4. **Verify Publication**

   - Check PyPI: https://pypi.org/project/invokeai-mcp-server/
   - Check GitHub Release: https://github.com/coinstax/invokeai-mcp-server/releases

5. **Test Installation**
   ```bash
   pip install invokeai-mcp-server
   ```

### Step 5: Publish to MCP Registry

After PyPI publication, submit to the official MCP Registry:

1. **Install MCP Publisher CLI**
   ```bash
   git clone https://github.com/modelcontextprotocol/registry.git
   cd registry
   make publisher
   ```

2. **Prepare Server Manifest**

   The `mcp-server-manifest.json` file is already prepared in the repository.
   Verify it matches the published PyPI package version.

3. **Publish to MCP Registry**
   ```bash
   ./bin/mcp-publisher publish \
     --namespace io.github.coinstax \
     --manifest ../invokeai-mcp-server/mcp-server-manifest.json
   ```

   You'll be prompted to authenticate via GitHub OAuth.

4. **Verify in MCP Registry**

   Your server should appear in:
   - Official MCP Registry: https://github.com/modelcontextprotocol/registry
   - Smithery.ai: https://smithery.ai/server/invokeai
   - GitHub MCP Registry: https://github.com/mcp-registry

### Step 6: Announce the Release

1. **Update Repository README Badge**

   Add PyPI version badge to README.md:
   ```markdown
   [![PyPI version](https://badge.fury.io/py/invokeai-mcp-server.svg)](https://badge.fury.io/py/invokeai-mcp-server)
   ```

2. **Announce on Social Media** (Optional)
   - Twitter/X
   - Reddit (r/StableDiffusion, r/LocalLLaMA)
   - Discord communities

## Troubleshooting

### Build Fails

**Issue**: `python -m build` fails

**Solutions**:
- Ensure `pyproject.toml` is valid
- Check all dependencies are listed in `requirements.txt`
- Run `pip install --upgrade build wheel setuptools`

### PyPI Trusted Publishing Not Working

**Issue**: GitHub Action fails to publish

**Solutions**:
- Verify Trusted Publishing is configured on PyPI
- Check environment names match exactly (`pypi` or `testpypi`)
- Ensure workflow has `id-token: write` permission

### MCP Registry Namespace Verification Fails

**Issue**: Cannot verify namespace ownership

**Solutions**:
- Use `io.github.{username}` format for GitHub namespaces
- Authenticate with the correct GitHub account
- For custom domains, set up DNS/HTTP verification

### Import Errors After Installation

**Issue**: `pip install` succeeds but imports fail

**Solutions**:
- Check `[tool.setuptools]` configuration in `pyproject.toml`
- Ensure `py-modules = ["invokeai_mcp_server"]` is correct
- Verify `[project.scripts]` entry point is valid

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Breaking changes
- **MINOR** (x.1.x): New features, backwards compatible
- **PATCH** (x.x.1): Bug fixes, backwards compatible

Examples:
- `1.0.0` → `1.0.1`: Bug fix
- `1.0.1` → `1.1.0`: New feature (VAE override)
- `1.1.0` → `2.0.0`: Breaking API change

## Post-Release Checklist

- [ ] PyPI package published successfully
- [ ] GitHub Release created with artifacts
- [ ] MCP Registry updated
- [ ] Installation tested from PyPI
- [ ] Installation tested via Smithery
- [ ] README badges updated
- [ ] DEVELOPMENT_STATUS.md updated
- [ ] Social media announcements (if applicable)

## Emergency: Yanking a Release

If a critical bug is discovered:

1. **Yank the PyPI Release**
   ```bash
   pip install twine
   twine upload --skip-existing --repository pypi dist/*
   # Then on PyPI web UI, click "Manage" → "Options" → "Yank this release"
   ```

2. **Delete GitHub Release** (if needed)
   - Go to Releases → Edit → Delete

3. **Fix the Bug**
   - Create hotfix branch
   - Fix and test thoroughly
   - Increment PATCH version (e.g., 1.0.1 → 1.0.2)

4. **Publish Fixed Version**
   - Follow normal publishing workflow

## Resources

- **PyPI Documentation**: https://packaging.python.org/
- **MCP Registry**: https://github.com/modelcontextprotocol/registry
- **Smithery Documentation**: https://smithery.ai/docs
- **GitHub Actions**: https://docs.github.com/en/actions
- **Semantic Versioning**: https://semver.org/
