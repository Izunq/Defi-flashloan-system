# Project Compilation Tools

This directory contains tools and scripts for combining all project files into comprehensive text documents for analysis, backup, or sharing purposes.

## ️ Main Tools

### `combine_files.cjs`
The primary Node.js script that combines all project files into a single text document.

**Features:**
- Scans entire project directory recursively
- Filters out binary files, build artifacts, and temporary files
- Handles large projects efficiently with batch processing
- Generates detailed file listings and metadata
- Customizable ignore patterns and file extensions

**Usage:**
```bash
node combine_files.cjs [options]

Options:
  --ignore <patterns>      Comma-separated list of patterns to ignore
  --output <file>          Output file name (default: all_files_combined.txt)
  --ignore-ext <exts>      Comma-separated list of file extensions to ignore
  --max-size <size>        Maximum file size in MB to include (default: 10)
  --help                   Show help message
```

### Update Scripts

#### `update_combined_file.ps1` (PowerShell)
Enhanced PowerShell script that:
- Changes to project root directory automatically
- Runs the combine script from the correct location
- Provides detailed progress reporting
- Shows file location and timestamp

#### `update_combined_file.bat` (Batch)
Batch file equivalent of the PowerShell script for compatibility.

## 🎯 Quick Start

### From Project Root
The easiest way to update the combined file is to use the scripts in the project root:

1. **Double-click** `Update_Combined_File.url` shortcut
2. **Run** `update_project_compilation.bat`
3. **PowerShell** `update_project_compilation.ps1`

All of these will generate `ALL_PROJECT_FILES.txt` in the project root.

### From This Directory
```bash
# PowerShell
.\update_combined_file.ps1

# Batch
.\update_combined_file.bat

# Direct Node.js (limited to this directory only)
node combine_files.cjs
```

## 📊 Current Status

### Latest Compilation: ALL_PROJECT_FILES.txt
- **Location**: Project root directory
- **Files included**: 676 files
- **File size**: ~9.69 MB
- **Total lines**: ~255,917 lines
- **Last updated**: Automatically updated when scripts are run

### Ignored Patterns
The script automatically ignores:
- `.git`, `node_modules`, `__pycache__`, `.pytest_cache`
- `coverage_reports`, `test_logs`, `test_results`, `performance_reports`
- `emergency_backups`, `backups`, `logs`, `temp`
- IDE directories: `.vscode`, `.idea`
- Build directories: `dist`, `build`, `.next`, `.nuxt`
- Blockchain artifacts: `bytecode`, `abi`

### Ignored File Types
- Binary executables: `.exe`, `.dll`, `.so`, `.dylib`
- Images: `.jpg`, `.png`, `.gif`, `.svg`, `.ico`
- Audio/Video: `.mp3`, `.mp4`, `.wav`, `.avi`
- Archives: `.zip`, `.gz`, `.tar`, `.rar`, `.7z`
- Blockchain specific: `.zkey`, `.wasm`, `.r1cs`
- Python cache: `.pyc`, `.pyo`, `.pyd`
- Log files: `.log`

## � Configuration

The `combine_files.cjs` script can be customized by modifying the options object at the top of the file:

```javascript
const options = {
  ignorePatterns: [...],      // Directories to ignore
  ignoreExtensions: [...],    // File extensions to ignore
  maxFileSizeMB: 10,         // Maximum file size limit
  outputFile: 'filename.txt' // Default output filename
};
```

## 📝 File Structure

```
tools/compilation/
├── combine_files.cjs           # Main combination script
├── update_combined_file.ps1    # PowerShell wrapper
├── update_combined_file.bat    # Batch wrapper
├── folder2txt.cjs             # Folder structure converter
├── folder2txt.js              # JS folder converter
├── README.md                  # This file
└── [Generated files]          # Various compiled outputs
```

## ⚠️ Important Notes

1. **Run from Project Root**: The update scripts automatically change to the project root to scan the entire project, not just this directory.

2. **File Size**: Combined files can be quite large (5-10 MB) as they contain the entire project.

3. **Recursion Prevention**: The script automatically ignores existing combined files to prevent infinite recursion.

4. **Performance**: Large projects are processed in batches to prevent memory issues.

5. **Binary Files**: Binary files are detected and excluded, with only a reference line included in the output.

### Compilation Scripts
- **combine_files.cjs**: Main combination logic
- **folder2txt.js/cjs**: Folder structure extraction
- **update_combined_file.***: Automation scripts for regenerating compilations

## 🔧 Maintenance

### Regenerating Files
When project files change significantly, regenerate the compilation files:

1. Run the update scripts to create new compilations
2. Archive old compilation files if needed
3. Update this README with new file information

### File Management
- Keep only the most recent 2-3 compilation files
- Archive older compilations to prevent directory bloat
- Update file descriptions when new compilation types are added

## 📝 Notes

- These files are primarily for backup, analysis, and sharing purposes
- Large compilation files (like ALL_PROJECT_FILES.txt) should be handled carefully due to size
- Use these tools when you need to:
  - Create project snapshots
  - Share complete project context
  - Perform project-wide analysis
  - Create backups before major changes

## 🔗 Integration

These tools integrate with:
- Project documentation system
- Backup procedures
- Code analysis workflows
- Project sharing mechanisms

---
*Location: `tools/compilation/`*
*Purpose: Project compilation and combination utilities*
