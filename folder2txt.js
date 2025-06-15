#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Default options
const options = {
  maxDepth: Infinity,
  ignorePatterns: ['.git', 'node_modules'],
  outputFile: null,
  showHidden: false
};

// Parse command line arguments
const args = process.argv.slice(2);
let targetDir = '.';

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  
  if (arg === '--max-depth' && i + 1 < args.length) {
    options.maxDepth = parseInt(args[++i], 10);
  } else if (arg === '--ignore' && i + 1 < args.length) {
    options.ignorePatterns = args[++i].split(',');
  } else if (arg === '--output' && i + 1 < args.length) {
    options.outputFile = args[++i];
  } else if (arg === '--show-hidden') {
    options.showHidden = true;
  } else if (arg === '--help') {
    console.log(`
Usage: node folder2txt.js [directory] [options]

Options:
  --max-depth <number>     Maximum depth to traverse
  --ignore <patterns>      Comma-separated list of patterns to ignore
  --output <file>          Output file (if not specified, prints to console)
  --show-hidden            Show hidden files and directories
  --help                   Show this help message
    `);
    process.exit(0);
  } else if (!arg.startsWith('--')) {
    targetDir = arg;
  }
}

// Function to scan directory recursively
function scanDirectory(dir, depth = 0, prefix = '') {
  if (depth > options.maxDepth) return '';
  
  let output = '';
  const items = fs.readdirSync(dir, { withFileTypes: true });
  
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const isLast = i === items.length - 1;
    
    // Skip hidden files unless showHidden is true
    if (!options.showHidden && item.name.startsWith('.')) continue;
    
    // Skip ignored patterns
    if (options.ignorePatterns.some(pattern => item.name.includes(pattern))) continue;
    
    const itemPath = path.join(dir, item.name);
    const connector = isLast ? '└── ' : '├── ';
    const newPrefix = prefix + (isLast ? '    ' : '│   ');
    
    output += `${prefix}${connector}${item.name}\n`;
    
    if (item.isDirectory()) {
      output += scanDirectory(itemPath, depth + 1, newPrefix);
    }
  }
  
  return output;
}

// Main execution
try {
  const absolutePath = path.resolve(targetDir);
  const result = `${absolutePath}\n${scanDirectory(absolutePath)}`;
  
  if (options.outputFile) {
    fs.writeFileSync(options.outputFile, result);
    console.log(`Output written to ${options.outputFile}`);
  } else {
    console.log(result);
  }
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}