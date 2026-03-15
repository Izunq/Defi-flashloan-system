# PowerShell script to compile all project files into one text file
$outputFile = "c:/Users/mahia/New_Flashloan/COMPLETE_PROJECT_COMPILATION.txt"
$projectRoot = "c:/Users/mahia/New_Flashloan"

# Define file categories and their patterns
$categories = @{
    "PYTHON_MAIN" = @("*.py");
    "SOLIDITY" = @("*.sol");
    "CONFIG" = @("*.yaml", "*.yml", "*.json");
    "FRONTEND" = @("*.tsx", "*.ts", "*.js", "*.css");
    "DOCS" = @("*.md", "*.txt")
}

# Files to exclude
$excludePatterns = @("*node_modules*", "*__pycache__*", "*COMPLETE_PROJECT_COMPILATION*", "*compile_project*")

function Add-FileContent {
    param($filePath, $category)
    
    $relativePath = $filePath.Replace($projectRoot, "").TrimStart('\')
    $separator = "=" * 80
    
    Add-Content $outputFile "`n$separator"
    Add-Content $outputFile "FILE: $relativePath"
    Add-Content $outputFile "CATEGORY: $category"
    Add-Content $outputFile "SIZE: $((Get-Item $filePath).Length) bytes"
    Add-Content $outputFile $separator
    Add-Content $outputFile ""
    
    try {
        $content = Get-Content $filePath -Raw -ErrorAction Stop
        Add-Content $outputFile $content
    } catch {
        Add-Content $outputFile "ERROR: Could not read file - $($_.Exception.Message)"
    }
    
    Add-Content $outputFile "`n"
}

# Get all relevant files
$allFiles = Get-ChildItem -Path $projectRoot -File -Recurse | Where-Object {
    $file = $_
    $include = $false
    
    # Check if file matches any category pattern
    foreach ($category in $categories.Keys) {
        foreach ($pattern in $categories[$category]) {
            if ($file.Name -like $pattern) {
                $include = $true
                break
            }
        }
        if ($include) { break }
    }
    
    # Exclude unwanted files
    if ($include) {
        foreach ($excludePattern in $excludePatterns) {
            if ($file.FullName -like $excludePattern) {
                $include = $false
                break
            }
        }
    }
    
    return $include
}

# Sort files by category and name
$sortedFiles = $allFiles | Sort-Object Extension, Name

Write-Host "Found $($sortedFiles.Count) files to compile..."

# Process each category
foreach ($category in $categories.Keys) {
    $categoryFiles = $sortedFiles | Where-Object {
        $file = $_
        $match = $false
        foreach ($pattern in $categories[$category]) {
            if ($file.Name -like $pattern) {
                $match = $true
                break
            }
        }
        return $match
    }
    
    if ($categoryFiles.Count -gt 0) {
        $separator = "=" * 80
        Add-Content $outputFile "`n`n$separator"
        Add-Content $outputFile "CATEGORY: $category"
        Add-Content $outputFile "FILES COUNT: $($categoryFiles.Count)"
        Add-Content $outputFile $separator
        
        foreach ($file in $categoryFiles) {
            Add-FileContent $file.FullName $category
            Write-Host "Added: $($file.Name)"
        }
    }
}

Write-Host "Compilation complete! Output saved to: $outputFile"