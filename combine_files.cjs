#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Default options
const options = {
  ignorePatterns: ['.git', 'node_modules', '__pycache__'],
  outputFile: 'all_files_combined.txt',
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
    '.zkey', '.wasm', '.r1cs'
  ],
  maxFileSizeMB: 10 // Skip files larger than this size
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
  } else if (arg === '--max-size' && i + 1 < args.length) {
    options.maxFileSizeMB = parseFloat(args[++i]);
  } else if (arg === '--help') {
    console.log(`
Usage: node combine_files.cjs [options]

Options:
  --ignore <patterns>      Comma-separated list of patterns to ignore (default: .git,node_modules,__pycache__)
  --output <file>          Output file (default: all_files_combined.txt)
  --ignore-ext <exts>      Comma-separated list of file extensions to ignore
  --max-size <size>        Maximum file size in MB to include (default: 10)
  --help                   Show this help message
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
  
  // Check file extension
  const ext = path.extname(itemPath).toLowerCase();
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
  
  let combinedContent = `COMBINED FILES FROM: ${rootDir}\nTotal files: ${allFiles.length}\nDate: ${new Date().toISOString()}\n\n`;
  combinedContent += `FILES LIST:\n${allFiles.map(f => `- ${f}`).join('\n')}\n\n`;
  
  // Process files in batches to avoid memory issues
  const batchSize = 100;
  
  // Always start with a fresh file
  fs.writeFileSync(options.outputFile, combinedContent);
  combinedContent = '';
  
  for (let i = 0; i < allFiles.length; i += batchSize) {
    const batch = allFiles.slice(i, i + batchSize);
    console.log(`Processing batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(allFiles.length/batchSize)}`);
    
    for (const file of batch) {
      combinedContent += readFileContent(file);
    }
    
    // Append to file after each batch
    fs.appendFileSync(options.outputFile, combinedContent);
    
    // Reset combined content for next batch
    combinedContent = '';
  }
  
  console.log(`All files combined into: ${options.outputFile}`);
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}