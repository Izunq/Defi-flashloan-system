import os
import re
from pathlib import Path
import time

# --- Configuration & Heuristics (The "AI Brain") ---
# This section contains rules to help the script understand the project structure.
VAULT_STRUCTURE = {
    "01_Contracts": "contracts/",
    "02_AI_Core": "ai/",
    "03_Backend_Services": "backend/src/",
    "04_Data_&_Sim": ["simulation/", "data/"],
    "05_Orchestration": "orchestration/",
    "06_Security": "security/",
    "utils": "utils/"
}

PURPOSE_HEURISTICS = {
    "Engine": "A core logic engine that drives a major process.",
    "Executor": "A component responsible for executing actions, likely on-chain.",
    "Synthesizer": "Generates new protocols, code, or strategies.",
    "Guardian": "A security or compliance-focused component.",
    "Simulator": "Simulates market conditions or protocol behavior.",
    "Service": "A backend microservice, likely running continuously.",
    "Client": "A client for interacting with an external API.",
    "Manager": "Manages other components or resources.",
    "Agent": "An autonomous agent performing tasks.",
    "Vault": "A smart contract designed to hold assets.",
    "Factory": "A smart contract that creates other contracts.",
    "Strategy": "A component defining a specific financial strategy.",
    "test_": "A test script for verifying functionality.",
    "abi/": "Application Binary Interface (ABI) for a smart contract."
}

KNOWN_DEPENDENCIES = {
    "CausalityEngine.py": ["DataIngestionService.py", "ProtocolSynthesizer.py", "Market Inefficiency"],
    "ProtocolSynthesizer.py": ["LLMManager.py", "StrategyTemplate", "Claude 3.5 Sonnet"],
    "WorldModelSimulator.py": ["DataIngestionService.py", "ReinforcementLearningAgent.py"],
    "ArbitrageExecutorV33.py": ["ArbitrageVaultERC4626.sol", "Alchemy"],
    "LLMManager.py": ["OpenAIClient.py", "AnthropicClient.py"],
    "EthicalGuardian.py": ["ProtocolSynthesizer.py"],
    "sentinel_architecture": ["AnomalyDetection.py", "ThreatIntelligenceAgent.py"],
    "ProtocolGenesisEngine.sol": ["Human-AISymbiote.sol"]
}

# Directories and file patterns to ignore during the scan
IGNORE_PATTERNS = [
    "__pycache__",
    "node_modules",
    ".git",
    ".venv",
    "venv",
    ".vscode",
    ".pytest_cache"
]
IGNORE_EXTENSIONS = [
    '.pyc', '.pyo', '.pyd', '.exe', '.dll', '.so', '.o', '.a', '.lib',
    '.DS_Store', '.log', '.tmp', '.bak', '.swp', '.zip', '.tar', '.gz',
    '.png', '.jpg', '.jpeg', '.gif', '.svg' # Ignore common image formats
]


# --- Note Templates ---

COMPONENT_TEMPLATE = """---
tags: {tags}
aliases: []
project_path: "{project_path}"
last_sync: {timestamp}
---

# [[{filename}]]

**Purpose:** {purpose}

---
### Dependencies & Links
{dependencies}

---
### Key Functions / Data
*This section is for your manual edits. The synchronizer will not overwrite this.*

---
### Questions & To-Do
*Your notes here.*
"""

ARCHIVE_NOTICE = """
---
tags: #archived
---
# ARCHIVED - {filename}
This note has been archived because the corresponding file in the project could no longer be found during the last sync on {timestamp}.

The original content is preserved below for your reference.

---
{original_content}
"""

# --- Main Synchronizer Class ---

class ObsidianSynchronizer:
    """A class to synchronize a project directory with an Obsidian vault."""

    def __init__(self, project_root_path, vault_name="My_System_Vault"):
        self.project_root_path = Path(project_root_path)
        self.vault_path = Path(vault_name)
        self.archive_path = self.vault_path / "99_Archive"
        self.project_files = {}  # {relative_path: absolute_path}
        self.vault_notes = {}    # {relative_path: {note_path, last_sync}}

    def scan_project_files(self):
        """Scans the source project directory, ignoring specified patterns."""
        print(f"Scanning project directory: '{self.project_root_path}'...")
        all_found_files = list(self.project_root_path.rglob("*"))
        
        for p in all_found_files:
            if not p.is_file():
                continue

            # Check if any part of the path is in the ignore list
            path_parts = set(p.parts)
            if any(part in IGNORE_PATTERNS for part in path_parts):
                continue

            # Check if the file extension should be ignored
            if p.suffix in IGNORE_EXTENSIONS:
                continue

            # Check against ignore patterns as strings
            str_path = str(p)
            if any(pattern in str_path for pattern in IGNORE_PATTERNS):
                 continue

            relative_path = p.relative_to(self.project_root_path)
            self.project_files[relative_path] = p
        
        print(f"Found {len(self.project_files)} relevant project files.")

    def scan_vault_notes(self):
        """Scans the existing Obsidian vault to see what's already mapped."""
        print("Scanning existing Obsidian vault...")
        if not self.vault_path.exists():
            print("No existing vault found. A new one will be created.")
            return

        for md_file in self.vault_path.rglob("*.md"):
            if self.archive_path in md_file.parents:
                continue

            content = md_file.read_text(encoding='utf-8')
            proj_path_match = re.search(r'project_path:\s*"(.*?)"', content)
            
            if proj_path_match:
                # Store path as a Path object for consistent comparison
                proj_path = Path(proj_path_match.group(1))
                self.vault_notes[proj_path] = {"note_path": md_file}
        print(f"Found {len(self.vault_notes)} existing notes in the vault.")

    def get_category_folder(self, relative_path):
        """Determines the correct vault subfolder for a given relative file path."""
        for folder_name, path_prefixes in VAULT_STRUCTURE.items():
            prefixes = path_prefixes if isinstance(path_prefixes, list) else [path_prefixes]
            for prefix in prefixes:
                # Use os.sep for cross-platform compatibility
                if str(relative_path).startswith(prefix.replace('/', os.sep)):
                    return folder_name
        return None

    def create_note_if_needed(self, relative_path):
        """Creates a new note only if it doesn't already exist."""
        absolute_path = self.project_files[relative_path]
        category_folder = self.get_category_folder(relative_path)
        if not category_folder:
            return "skipped_no_category"

        note_filename = f"{absolute_path.name}.md"
        output_path = self.vault_path / category_folder / note_filename
        
        # --- The Core "Don't Create If Exists" Logic ---
        if output_path.exists():
            return "skipped_exists"

        # --- Content Generation ---
        filename = absolute_path.name
        tags = ["#component", f"#{absolute_path.suffix.replace('.', '') if absolute_path.suffix else ''}", f"#{category_folder.split('_')[1].lower()}"]
        purpose = next((desc for key, desc in PURPOSE_HEURISTICS.items() if key.lower() in filename.lower()), "A component of the system.")
        dependencies = {dep for key, deps in KNOWN_DEPENDENCIES.items() if key in filename for dep in deps}
        dep_links = "\n".join(f"* `[[{dep}]]`" for dep in sorted(list(dependencies))) or "* *No explicit dependencies found.*"
        
        note_content = COMPONENT_TEMPLATE.format(
            tags=' '.join(tags),
            project_path=str(relative_path).replace('\\', '/'),
            timestamp=time.time(),
            filename=filename,
            purpose=purpose,
            dependencies=dep_links
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(note_content, encoding='utf-8')
        return "created"

    def archive_stale_notes(self):
        """Moves notes for deleted project files to an archive folder."""
        stale_count = 0
        project_paths_in_vault = set(self.vault_notes.keys())
        current_project_paths = set(self.project_files.keys())
        
        stale_paths = project_paths_in_vault - current_project_paths
        
        if not stale_paths:
            return 0
        
        self.archive_path.mkdir(exist_ok=True)
        
        for stale_path in stale_paths:
            stale_count += 1
            note_info = self.vault_notes[stale_path]
            note_path = note_info["note_path"]
            
            original_content = note_path.read_text(encoding='utf-8')
            archived_content = ARCHIVE_NOTICE.format(
                filename=note_path.name,
                timestamp=time.ctime(),
                original_content=original_content
            )
            
            archive_file_path = self.archive_path / note_path.name
            archive_file_path.write_text(archived_content, encoding='utf-8')
            note_path.unlink()
            
        return stale_count

    def synchronize(self):
        """Runs the complete synchronization process."""
        print("--- Starting Obsidian Vault Synchronization ---")
        self.scan_project_files()
        self.scan_vault_notes()
        
        for folder in VAULT_STRUCTURE:
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)
        (self.vault_path / "07_Concepts").mkdir(exist_ok=True)
        (self.vault_path / "08_Processes").mkdir(exist_ok=True)

        created, skipped = 0, 0
        for relative_path in self.project_files:
            status = self.create_note_if_needed(relative_path)
            if status == "created":
                created += 1
            else:
                skipped +=1

        print(f"\nProcessed project files: {created} new notes created, {skipped} existing notes skipped.")

        archived = self.archive_stale_notes()
        if archived > 0:
            print(f"Archived {archived} stale notes for deleted project files.")

        print("\n--- Synchronization Complete ---")
        print(f"✅ Your vault '{self.vault_path}' is now up-to-date with your project.")

if __name__ == '__main__':
    # --- IMPORTANT ---
    # Update this path to the root folder of your project.
    project_root_path = 'C:/Users/mahia/New_Flashloan'
    
    if not os.path.isdir(project_root_path):
        print(f"ERROR: The project directory '{project_root_path}' was not found.")
        print("Please update the 'project_root_path' variable in the script to the correct location.")
    else:
        synchronizer = ObsidianSynchronizer(project_root_path)
        synchronizer.synchronize()
