#!/usr/bin/env python
"""
Script to push code to GitHub repository.
For first-time setup, run this in your terminal manually:

```
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/schuttebj/ampro.git
git push -u origin main
```

This script is for subsequent pushes.
"""

import os
import subprocess
import sys
import argparse

def run_command(command, error_message):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(command, check=True, shell=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {error_message}")
        print(f"Command output: {e.output}")
        print(f"Command stderr: {e.stderr}")
        return False

def push_to_github(commit_message):
    """Push changes to GitHub with the specified commit message."""
    # Add all changes
    if not run_command("git add .", "Failed to add files to git staging"):
        return False
    
    # Commit changes
    if not run_command(f'git commit -m "{commit_message}"', "Failed to commit changes"):
        return False
    
    # Push to GitHub
    if not run_command("git push origin main", "Failed to push to GitHub"):
        return False
    
    print("Successfully pushed changes to GitHub!")
    return True

def main():
    """Main function to parse arguments and execute git push."""
    parser = argparse.ArgumentParser(description="Push code to GitHub")
    parser.add_argument("--message", "-m", required=True, help="Commit message")
    args = parser.parse_args()
    
    if push_to_github(args.message):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 