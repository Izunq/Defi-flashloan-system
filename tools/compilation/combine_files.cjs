#!/usr/bin/env node

/**
 * Project File Combiner for Artemis AI Core
 * 
 * Last Updated: June 16, 2025
 * 
 * Recent Updates:
 * - Added Python virtual environment exclusions (artemis_core/Lib, artemis_core/Scripts)
 * - Excluded development backup files (.bak, .backup, .original, .minimal)
 * - Added lock file exclusions (yarn.lock, package-lock.json)
 * - Excluded Obsidian vault files (.obsidian)
 * - Excluded mock_data and test_data directories
 * 
 * This script combines all project source files into a single text file
 * for AI analysis while excluding large binary files and dependencies.
 */

const fs = require('fs');
const path = require('path');

// Default options - Updated for selective inclusion
const options = {
  ignorePatterns: [
    '.git', 'node_modules', '__pycache__', '.pytest_cache',
    'coverage_reports', 'test_logs', 'test_results', 'performance_reports',
    'emergency_backups', 'backups', 'logs', 'temp', '.vscode', '.idea',
    'dist', 'build', '.next', '.nuxt', '.output', '.nitro',
    'bytecode', 'abi',  // Blockchain-specific generated folders
    'artemis_core\\Lib', 'artemis_core\\Scripts', // Python virtual environment (Windows paths)
    'artemis_core/Lib', 'artemis_core/Scripts', // Python virtual environment (Unix paths)
    'mock_data', 'test_data', // Test and mock data folders
    '.obsidian', // Obsidian vault files
    'ALL_PROJECT_FILES.txt', 'ALL_PROJECT_FILES_UPDATED.txt', 'ALL_PROJECT_FILES_CLEAN.txt', // Existing combined files
    // Additional exclusions for size management
    'docs/archive', 'docs/old', 'docs/backup',
    'tools/old', 'tools/backup',
    'scripts/old', 'scripts/backup'
  ],
  outputFile: 'all_files_combined.txt',
  // Only include essential file types for code analysis
  includeExtensions: [
    '.py', '.js', '.ts', '.jsx', '.tsx', '.sol', '.go', '.rs', '.java', '.c', '.cpp', '.h',
    '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini', '.env',
    '.md', '.txt', '.rst',
    '.sh', '.bat', '.ps1', '.cmd',
    '.html', '.css', '.scss', '.sass', '.less',
    '.sql', '.graphql', '.proto'
  ],
  ignoreExtensions: [
    // Binary executables and libraries
    '.bin', '.pyc', '.pyo', '.pyd', '.exe', '.dll', '.so', '.dylib',
    // Images
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.bmp', '.tiff', '.webp',
    // Fonts
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    // Other binary formats
    '.pdf', '.zip', '.gz', '.tar', '.rar', '.7z', '.jar', '.war',
    // Audio/Video
    '.mp3', '.mp4', '.wav', '.avi', '.mov', '.flv', '.wmv',
    // Database and data files
    '.db', '.sqlite', '.dat', '.sav',
    // Compiled code
    '.class', '.o', '.obj',
    // Zk-SNARK related
    '.zkey', '.wasm', '.r1cs',
    // Jupyter checkpoint files
    '.ipynb_checkpoints',
    // Lock files
    '.lock', '.yarn.lock', 'package-lock.json',
    // Log files
    '.log',
    // Development backup files
    '.bak', '.backup', '.original', '.minimal'
  ],  maxFileSizeMB: 5, // Reduced from 10MB to 5MB for better size control
  maxTotalSizeMB: 50 // Maximum total output file size in MB
};

// Parse command line arguments
const args = process.argv.slice(2);

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  
  if (arg === '--ignore' && i + 1 < args.length) {
    options.ignorePatterns = args[++i].split(',');
  } else if (arg === '--output' && i + 1 < args.length) {
    options.outputFile = args[++i];
  } else if (arg === '--ignore-ext' && i + 1 < args.length) {
    options.ignoreExtensions = args[++i].split(',');
  } else if (arg === '--include-ext' && i + 1 < args.length) {
    options.includeExtensions = args[++i].split(',');
  } else if (arg === '--max-size' && i + 1 < args.length) {
    options.maxFileSizeMB = parseFloat(args[++i]);
  } else if (arg === '--max-total' && i + 1 < args.length) {
    options.maxTotalSizeMB = parseFloat(args[++i]);
  } else if (arg === '--help') {console.log(`
Usage: node combine_files.cjs [options]

Options:
  --ignore <patterns>      Comma-separated list of patterns to ignore (default: .git,node_modules,__pycache__)
  --output <file>          Output file (default: all_files_combined.txt)
  --ignore-ext <exts>      Comma-separated list of file extensions to ignore
  --include-ext <exts>     Comma-separated list of file extensions to include (overrides default filter)
  --max-size <size>        Maximum individual file size in MB to include (default: 5)
  --max-total <size>       Maximum total output file size in MB (default: 50)
  --help                   Show this help message

Examples:
  node combine_files.cjs --output "ESSENTIAL_FILES.txt" --max-total 20
  node combine_files.cjs --include-ext ".py,.js,.sol,.md" --max-size 2
    `);
    process.exit(0);
  }
}

// Function to check if a path should be ignored
function shouldIgnore(itemPath) {
  const basename = path.basename(itemPath);
  
  // Check if the path contains any ignore pattern
  if (options.ignorePatterns.some(pattern => itemPath.includes(pattern))) {
    return true;
  }
  
  // Ignore any existing combined files to prevent recursion
  if (basename.includes('PROJECT_FILES') || basename.includes('_combined') || 
      basename.includes('COMPILATION') || basename.includes('SNAPSHOT') ||
      basename.includes('EVERYTHING') || basename.includes('MASTER_PROJECT') ||
      basename.includes('ULTIMATE_PROJECT') || basename.includes('FULL_PROJECT')) {
    return true;
  }
    // Check file extension - only include essential files
  const ext = path.extname(itemPath).toLowerCase();
  
  // If includeExtensions is specified, only include those extensions
  if (options.includeExtensions && options.includeExtensions.length > 0) {
    if (!options.includeExtensions.includes(ext)) {
      return true; // Ignore files not in the include list
    }
  }
  
  // Also check the ignore extensions list
  if (options.ignoreExtensions.includes(ext)) {
    return true;
  }
  
  // Exclude the output file itself to prevent recursion
  if (path.resolve(itemPath) === path.resolve(options.outputFile)) {
    return true;
  }
  
  return false;
}

// Function to get all files recursively
function getAllFiles(dir, fileList = []) {
  const items = fs.readdirSync(dir, { withFileTypes: true });
  
  for (const item of items) {
    const itemPath = path.join(dir, item.name);
    
    if (shouldIgnore(itemPath)) {
      continue;
    }
    
    if (item.isDirectory()) {
      getAllFiles(itemPath, fileList);
    } else {
      // Check file size
      const stats = fs.statSync(itemPath);
      const fileSizeMB = stats.size / (1024 * 1024);
      
      if (fileSizeMB <= options.maxFileSizeMB) {
        fileList.push(itemPath);
      } else {
        console.log(`Skipping large file: ${itemPath} (${fileSizeMB.toFixed(2)} MB)`);
      }
    }
  }
  
  return fileList;
}

// Function to read file content safely
function readFileContent(filePath) {
  try {
    const ext = path.extname(filePath).toLowerCase();
    // For binary-like files, just note that they exist but don't include content
    const binaryExtensions = [
      '.pdf', '.zip', '.gz', '.tar', '.rar', '.7z', '.jar', '.war',
      '.mp3', '.mp4', '.wav', '.avi', '.mov', '.flv', '.wmv',
      '.db', '.sqlite', '.dat', '.sav',
      '.class', '.o', '.obj',
      '.zkey', '.wasm', '.r1cs'
    ];
    
    if (binaryExtensions.includes(ext)) {
      return `[Binary file: ${filePath}]\n\n`;
    }
    
    // Try to detect if file might be binary despite extension
    try {
      const sample = fs.readFileSync(filePath, { encoding: 'utf8', flag: 'r', start: 0, end: 1000 });
      // Check for high concentration of null bytes or control characters
      const nullCount = (sample.match(/\0/g) || []).length;
      if (nullCount > 10) {
        return `[Likely binary file: ${filePath}]\n\n`;
      }
    } catch (e) {
      // If we can't read a sample, continue with normal processing
    }
    
    // Try to read as text
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Clean the content by removing NUL characters and other problematic control characters
    content = content
      .replace(/\0/g, '') // Remove NUL characters
      .replace(/[\x01-\x08\x0B\x0C\x0E-\x1F]/g, ''); // Remove other control characters except tab (\x09), LF (\x0A), and CR (\x0D)
    
    return `\n\n${'='.repeat(80)}\nFILE: ${filePath}\n${'='.repeat(80)}\n\n${content}\n`;
  } catch (error) {
    return `\n\n${'='.repeat(80)}\nFILE: ${filePath}\n${'='.repeat(80)}\n\n[Error reading file: ${error.message}]\n`;
  }
}

// Main execution
try {
  const rootDir = path.resolve('.');
  console.log(`Scanning directory: ${rootDir}`);
  
  const allFiles = getAllFiles(rootDir);
  console.log(`Found ${allFiles.length} files to combine`);
    let combinedContent = `COMBINED FILES FROM: ${rootDir}\nTotal files: ${allFiles.length}\nDate: ${new Date().toISOString()}\nIgnored patterns: ${options.ignorePatterns.join(', ')}\n\n`;
  combinedContent += `FILES LIST:\n${allFiles.map(f => `- ${path.relative(rootDir, f)}`).join('\n')}\n\n`;
    // Process files in batches to avoid memory issues
  const batchSize = 50; // Reduced batch size for better control
  let totalSize = 0;
  
  // Always start with a fresh file
  fs.writeFileSync(options.outputFile, combinedContent);
  totalSize += Buffer.byteLength(combinedContent, 'utf8');
  combinedContent = '';
  
  for (let i = 0; i < allFiles.length; i += batchSize) {
    const batch = allFiles.slice(i, i + batchSize);
    console.log(`Processing batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(allFiles.length/batchSize)}`);
    
    for (const file of batch) {
      const fileContent = readFileContent(file);
      const contentSize = Buffer.byteLength(fileContent, 'utf8');
      
      // Check if adding this file would exceed the total size limit
      if (options.maxTotalSizeMB && (totalSize + contentSize) / (1024 * 1024) > options.maxTotalSizeMB) {
        console.log(`Stopping: Total size limit (${options.maxTotalSizeMB}MB) would be exceeded. Current size: ${(totalSize / (1024 * 1024)).toFixed(2)}MB`);
        break;
      }
      
      combinedContent += fileContent;
      totalSize += contentSize;
    }
    
    // Append to file after each batch
    fs.appendFileSync(options.outputFile, combinedContent);
    
    // Reset combined content for next batch
    combinedContent = '';
    
    // Check if we've hit the size limit
    if (options.maxTotalSizeMB && totalSize / (1024 * 1024) > options.maxTotalSizeMB) {
      break;
    }
  }
  
  console.log(`All files combined into: ${options.outputFile}`);
  
  // Report final file size
  const finalStats = fs.statSync(options.outputFile);
  const finalSizeMB = finalStats.size / (1024 * 1024);
  console.log(`Final file size: ${finalSizeMB.toFixed(2)} MB`);
  
  if (finalSizeMB > 50) {
    console.log(`⚠️  Warning: Output file is ${finalSizeMB.toFixed(2)} MB. Consider further filtering.`);
  } else if (finalSizeMB > 20) {
    console.log(`📊 File size is manageable at ${finalSizeMB.toFixed(2)} MB`);
  } else {
    console.log(`✅ Optimal file size: ${finalSizeMB.toFixed(2)} MB`);
  }
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}