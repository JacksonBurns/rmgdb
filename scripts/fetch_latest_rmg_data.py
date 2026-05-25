#!/usr/bin/env python3
"""
Script to update data from RMG-database repository.
This script fetches the latest data from the official RMG-database repository
and copies it to the appropriate local directories.
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error: {e.stderr}")
        raise

def clone_or_update_rmg_database(repo_url, clone_dir):
    """Clone or update the RMG-database repository."""
    print(f"Checking for RMG-database repository in {clone_dir}")

    if os.path.exists(clone_dir):
        print("Repository exists, updating...")
        # Update existing repository
        run_command("git fetch origin", cwd=clone_dir)
        run_command("git checkout main", cwd=clone_dir)
        run_command("git pull origin main", cwd=clone_dir)
    else:
        print("Repository does not exist, cloning...")
        # Clone repository
        run_command(f"git clone {repo_url} {clone_dir}")

    print("Repository is up to date.")

def copy_data_from_rmg_database(rmg_dir, local_base_dir):
    """Copy data from RMG-database repository to local directories."""
    print("Copying data from RMG-database to local directories...")

    # Define the mapping from RMG-database input directories to local directories
    mapping = {
        "input/kinetics/families": "data/rmgdatabase/kinetics/original/families",
        "input/kinetics/libraries": "data/rmgdatabase/kinetics/original/libraries",
        "input/thermo": "data/rmgdatabase/thermo/original",
        "input/solvation": "data/rmgdatabase/solvation/original",
        "input/statmech": "data/rmgdatabase/statmech/original",
        "input/transport": "data/rmgdatabase/transport/original"
    }

    for rmg_input_path, local_path in mapping.items():
        rmg_full_path = os.path.join(rmg_dir, rmg_input_path)
        local_full_path = os.path.join(local_base_dir, local_path)

        if os.path.exists(rmg_full_path):
            print(f"Copying {rmg_input_path} to {local_path}")

            # Create the local directory if it doesn't exist
            os.makedirs(os.path.dirname(local_full_path), exist_ok=True)

            # Remove existing directory/file if it exists
            if os.path.exists(local_full_path):
                if os.path.isdir(local_full_path):
                    shutil.rmtree(local_full_path)
                else:
                    os.remove(local_full_path)

            # Copy the data
            if os.path.isdir(rmg_full_path):
                shutil.copytree(rmg_full_path, local_full_path)
            else:
                shutil.copy2(rmg_full_path, local_full_path)
        else:
            print(f"Warning: {rmg_input_path} not found in RMG-database repository")

def fetch_latest_rmg_data():
    """Main function to fetch latest data from RMG-database."""
    print("Starting RMG-database data fetch process...")

    # Repository details
    repo_url = "https://github.com/ReactionMechanismGenerator/RMG-database"
    clone_dir = "temp_rmg_database"
    local_base_dir = "."

    try:
        # Clone or update the RMG-database repository
        clone_or_update_rmg_database(repo_url, clone_dir)

        # Copy data from RMG-database to local directories
        copy_data_from_rmg_database(clone_dir, local_base_dir)

        print("Data fetch process completed successfully")
        return True

    except Exception as e:
        print(f"Error during data fetch: {e}")
        return False
    finally:
        # Clean up temporary directory
        if os.path.exists(clone_dir):
            print("Cleaning up temporary directory...")
            shutil.rmtree(clone_dir)

if __name__ == "__main__":
    success = fetch_latest_rmg_data()
    sys.exit(int(not success))  # Exit with 0 for success, 1 for failure