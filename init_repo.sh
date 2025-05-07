#!/bin/bash
# Initialize Git repository and push to GitHub

# Check if git is installed
if ! [ -x "$(command -v git)" ]; then
  echo 'Error: git is not installed.' >&2
  exit 1
fi

# Initialize git repository
git init

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
  echo "Creating .gitignore file..."
  cat > .gitignore << EOF
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Environment variables
.env
.env.local
.env.development
.env.production

# Virtual environments
venv/
env/
ENV/

# IDE specific files
.idea/
.vscode/
*.swp

# Logs
*.log

# Database
*.db
*.sqlite3
EOF
fi

# Add all files
git add .

# Initial commit
git commit -m "Initial commit"

# Rename master branch to main
git branch -M main

# Check if origin remote already exists
if ! git remote | grep -q "origin"; then
  echo "Enter your GitHub username:"
  read username
  
  echo "Enter your repository name:"
  read repo
  
  git remote add origin "https://github.com/$username/$repo.git"
  echo "Remote 'origin' added: https://github.com/$username/$repo.git"
else
  echo "Remote 'origin' already exists."
fi

# Push to GitHub
echo "Do you want to push to GitHub now? (y/n)"
read answer

if [ "$answer" == "y" ]; then
  git push -u origin main
  echo "Successfully pushed to GitHub!"
else
  echo "Changes are committed locally but not pushed to GitHub."
  echo "To push later, run: git push -u origin main"
fi

echo "Repository initialization complete!" 