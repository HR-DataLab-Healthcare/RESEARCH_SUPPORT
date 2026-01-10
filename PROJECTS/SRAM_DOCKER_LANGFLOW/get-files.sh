#!/bin/bash

# 1. Create and move into the target directory
mkdir -p ~/LANGFLOW
cd ~/LANGFLOW

# 2. Initialize a new git repo locally
git init

# 3. Add the remote repository URL
git remote add -f origin https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT.git

# 4. Enable Sparse Checkout feature
git config core.sparseCheckout true

# 5. Define the specific path you want to download
echo "PROJECTS/SRAM_DOCKER_LANGFLOW/*" >> .git/info/sparse-checkout

# 6. Pull the files from the main branch
git pull origin main

# 7. Move files up to the root of ~/LANGFLOW and clean up
mv PROJECTS/SRAM_DOCKER_LANGFLOW/* .
rm -rf PROJECTS
rm -rf .git  # Removes git history so it's just a clean folder of files

echo "------------------------------------------"
echo "Success! Contents of SRAM_DOCKER_LANGFLOW are now in ~/LANGFLOW"
ls -la
