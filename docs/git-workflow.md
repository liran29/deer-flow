# Git Workflow for deer-flow Development

## Repository Architecture

The deer-flow project follows a three-tier Git repository structure:

```
upstream (https://github.com/bytedance/deer-flow.git)
    ↓
fork (https://github.com/liran29/deer-flow.git)
    ↓
local (your local repository)
```

## Branch Management Strategy

### main Branch
- **Purpose**: Synchronization only, no local modifications
- **Flow**: `upstream/main` → `fork/main` → `local/main`
- **Usage**: Used exclusively to sync updates from upstream to development branches
- **Important**: Never make direct commits to the main branch locally

### Development Branches
- **a-assist**: Active development branch
- **m-assist**: Alternative development branch
- **Flow**: Local development → Push to fork repository only
- **Note**: Development branches are never pushed directly to upstream

## Workflow Commands

### 1. Initial Setup
```bash
# Clone your fork
git clone https://github.com/liran29/deer-flow.git
cd deer-flow

# Add upstream remote
git remote add upstream https://github.com/bytedance/deer-flow.git
```

### 2. Sync main Branch with Upstream
```bash
# Checkout main branch
git checkout main

# Fetch upstream changes
git fetch upstream

# Merge upstream changes (no local changes on main)
git merge upstream/main

# Push to fork
git push origin main
```

### 3. Update Development Branches
```bash
# Switch to development branch
git checkout a-assist

# Merge latest main branch
git merge main

# Continue development...
```

### 4. Push Development Work
```bash
# Push to fork repository only
git push origin a-assist
```

## Important Notes

1. **Never modify main branch locally** - It should always be a clean mirror of upstream
2. **All development work happens in a-assist or m-assist branches**
3. **Development branches are pushed to fork repository only**
4. **Regularly sync main branch with upstream to stay updated**
5. **Merge main into development branches to incorporate upstream changes**

## Branch Protection Rules

To maintain this workflow:
- Consider setting main branch as protected in your fork
- Use pull requests for any contributions to upstream
- Keep development branches separate from synchronization branches