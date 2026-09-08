import os

def fix_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    changed = False
    has_typing_extensions = False
    
    for i, line in enumerate(lines):
        if line.startswith('from typing import') and 'Self' in line:
            line = line.replace(', Self', '').replace('Self, ', '').replace(' Self', '')
            if line.strip() == 'from typing import':
                lines[i] = ''
            else:
                lines[i] = line
            changed = True
        elif 'from typing_extensions import Self' in line:
            has_typing_extensions = True

    if changed:
        if not has_typing_extensions:
            lines.insert(0, 'from typing_extensions import Self\n')
        with open(filepath, 'w') as f:
            f.writelines(lines)

for root, dirs, files in os.walk('/Users/viktorkorladinov/micka/backend'):
    if '.venv' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))
