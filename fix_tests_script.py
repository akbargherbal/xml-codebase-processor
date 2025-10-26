# FILE PATH: fix_all_tests.py
# LOCATION: Root directory (temporary helper script)
# DESCRIPTION: Automatically add "include": [] to all params dictionaries in tests

"""
Helper script to automatically fix test files by adding "include": [] to params dicts.
Run this from the project root directory.
"""

import re
from pathlib import Path


def fix_params_dict(content: str) -> tuple[str, int]:
    """
    Add "include": [] to params dictionaries that don't have it.
    Returns (fixed_content, num_changes)
    """
    changes = 0
    lines = content.split('\n')
    result_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        result_lines.append(line)
        
        # Check if this line starts a params dict
        if re.match(r'\s*params\s*=\s*\{', line):
            # Check if "include" is already in the dict
            dict_content = [line]
            j = i + 1
            brace_count = line.count('{') - line.count('}')
            
            while j < len(lines) and brace_count > 0:
                dict_content.append(lines[j])
                brace_count += lines[j].count('{') - lines[j].count('}')
                j += 1
            
            full_dict = '\n'.join(dict_content)
            
            # If "include" not in dict, add it
            if '"include"' not in full_dict and "'include'" not in full_dict:
                # Find the line with "ignore_patterns" and add "include" after it
                for k in range(i + 1, j):
                    if '"ignore_patterns"' in lines[k] or "'ignore_patterns'" in lines[k]:
                        # Get indentation
                        indent = len(lines[k]) - len(lines[k].lstrip())
                        # Add "include" line after this one
                        result_lines.append(' ' * indent + '"include": [],')
                        changes += 1
                        # Add remaining lines
                        result_lines.extend(lines[k+1:j])
                        i = j - 1
                        break
                else:
                    # If no ignore_patterns found, just add the remaining lines
                    result_lines.extend(lines[i+1:j])
                    i = j - 1
            else:
                # "include" already exists, add remaining lines as-is
                result_lines.extend(lines[i+1:j])
                i = j - 1
        
        i += 1
    
    return '\n'.join(result_lines), changes


def main():
    """Fix all test files in the tests/ directory."""
    test_dir = Path('tests')
    
    if not test_dir.exists():
        print("Error: tests/ directory not found. Run this from project root.")
        return
    
    total_files = 0
    total_changes = 0
    
    # Find all Python test files
    for test_file in test_dir.rglob('test_*.py'):
        print(f"\nProcessing: {test_file}")
        
        try:
            content = test_file.read_text(encoding='utf-8')
            fixed_content, changes = fix_params_dict(content)
            
            if changes > 0:
                # Backup original
                backup_file = test_file.with_suffix('.py.bak')
                backup_file.write_text(content, encoding='utf-8')
                
                # Write fixed version
                test_file.write_text(fixed_content, encoding='utf-8')
                
                print(f"  ✓ Fixed {changes} params dict(s)")
                print(f"  ✓ Backup saved to: {backup_file}")
                total_files += 1
                total_changes += changes
            else:
                print(f"  • No changes needed")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files modified: {total_files}")
    print(f"  Total changes: {total_changes}")
    print(f"{'='*60}")
    
    if total_files > 0:
        print("\nNext steps:")
        print("1. Review the changes (backups saved as .py.bak)")
        print("2. Run: pytest tests/ -v")
        print("3. If tests pass, delete .bak files")
        print("4. If tests fail, restore from backups")


if __name__ == '__main__':
    main()
