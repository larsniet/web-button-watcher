#!/usr/bin/env bash
# Script to automate the release process for Web button watcher

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Display usage information
function show_usage {
  echo -e "${BLUE}Usage:${NC} $0 <new-version>"
  echo "Example: $0 1.0.1"
  exit 1
}

# Check if version is provided
if [ $# -ne 1 ]; then
  echo -e "${RED}Error: Version number is required${NC}"
  show_usage
fi

NEW_VERSION=$1

# Validate version format (simple check)
if ! [[ $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo -e "${RED}Error: Version should be in format X.Y.Z (e.g., 1.0.1)${NC}"
  show_usage
fi

echo -e "${BLUE}Starting release process for version ${GREEN}v$NEW_VERSION${NC}..."

# Ensure we're on the main branch and up-to-date
echo -e "\n${YELLOW}Checking git status...${NC}"
git checkout main
git pull

# Run tests to ensure everything is working
echo -e "\n${YELLOW}Running tests...${NC}"
python3 -m pytest
if [ $? -ne 0 ]; then
  echo -e "${RED}Tests failed. Fix the issues before releasing.${NC}"
  exit 1
fi

# Update version in __init__.py using platform-specific approach
echo -e "\n${YELLOW}Updating version to $NEW_VERSION in __init__.py...${NC}"

# For macOS compatibility
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS requires an empty string after -i
  sed -i "" "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" webbuttonwatcher/__init__.py
else
  # Linux doesn't need the empty string
  sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" webbuttonwatcher/__init__.py
fi

# Commit version change
echo -e "\n${YELLOW}Committing version change...${NC}"
git add webbuttonwatcher/__init__.py
git commit -m "Bump version to $NEW_VERSION"

# Push to main
echo -e "\n${YELLOW}Pushing to main branch...${NC}"
git push origin main

# Create and push tag
echo -e "\n${YELLOW}Creating and pushing tag v$NEW_VERSION...${NC}"
git tag "v$NEW_VERSION"
git push origin "v$NEW_VERSION"

echo -e "\n${GREEN}Release process started successfully!${NC}"
echo -e "${BLUE}GitHub Actions will now build and publish the release.${NC}"
echo -e "${BLUE}You can monitor the progress at:${NC}"
echo -e "${YELLOW}https://github.com/larsniet/web-button-watcher/actions${NC}"
echo -e "\n${GREEN}Don't forget to update the README or documentation with any new features or changes!${NC}" 