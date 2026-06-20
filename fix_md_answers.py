#!/usr/bin/env python3
"""扫描并修复下册MD文件中答案格式不一致的问题"""
import os, re

BASE = '/Users/wodediannao/huzhiyang/ai_plugs/Accounting_Drills '
lower_files = [
    os.path.join(BASE, 'file_json/MinerU_markdown_1_PDFsam_会计（下）_2067951849765175296.md'),
    os.path.join(BASE, 'file_json/MinerU_markdown_126_PDFsam_会计（下）_2067951995529822208.md'),
]

for fpath in lower_files:
    with open(fpath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fname = os.path.basename(fpath)
    print(f'\n=== {fname} ({len(lines)} lines) ===', flush=True)
    
    fixes = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n')
        
        # Pattern 0: ## N. （答案 | X） (pipe with closing paren - remove pipe)
        m = re.match(r'^(#{1,3}\s*\d+\.\s*)[（(]\s*答案\s*\|\s*([A-H]+)\s*[)）]\s*$', line)
        if m:
            fixed = f'{m.group(1)}（答案 {m.group(2)}）'
            fixes.append((i+1, line.strip(), fixed))
            i += 1; continue
        
        # Pattern 1: ## N. （答案 | X  (missing closing paren with pipe)
        m = re.match(r'^(#{1,3}\s*\d+\.\s*)[（(]\s*答案\s*\|\s*([A-H]+)\s*$', line)
        if m:
            fixed = f'{m.group(1)}（答案 {m.group(2)}）'
            fixes.append((i+1, line.strip(), fixed))
            i += 1; continue
        
        # Pattern 2: ## N.（答案 XXX  or ## N. (答案 XXX  (missing closing paren, no pipe)
        m = re.match(r'^(#{1,3}\s*\d+[\.\s]+)[（(]\s*答案\s+([A-H]{1,8})\s*$', line)
        if m:
            fixed = f'{m.group(1)}（答案 {m.group(2)}）'
            fixes.append((i+1, line.strip(), fixed))
            i += 1; continue
        
        # Pattern 3: ## N.\n\n## 答案\n\n## XX  (3-line split)
        # Current line is just "## N." with nothing after
        m1 = re.match(r'^#{1,3}\s*(\d+)\.\s*$', line)
        if m1 and i+2 < len(lines):
            # Look ahead: skip blank lines, find "## 答案" then "## XX"
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and re.match(r'^#{1,3}\s*答案\s*$', lines[j].rstrip('\n')):
                k = j + 1
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines):
                    m3 = re.match(r'^#{1,3}\s*([A-H]{1,8})\s*$', lines[k].rstrip('\n'))
                    if m3:
                        prefix = re.match(r'^(#{1,3})\s*', line).group(1)
                        fixed = f'{prefix} {m1.group(1)}. （答案 {m3.group(1)}）'
                        fixes.append((i+1, f'{line.strip()} / {lines[j].strip()} / {lines[k].strip()}', fixed))
                        # Mark lines j and k for deletion
                        fixes.append((j+1, f'DELETE: {lines[j].strip()}', 'DELETE'))
                        fixes.append((k+1, f'DELETE: {lines[k].strip()}', 'DELETE'))
                        i = k + 1; continue
        
        # Pattern 4: N.\n\n答案\n\nXX  (plain num, standalone 答案, letter on next)
        m1 = re.match(r'^(\d+)\.\s*$', line)
        if m1 and not line.startswith('#') and i+2 < len(lines):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and re.match(r'^答案\s*$', lines[j].rstrip('\n')):
                k = j + 1
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines):
                    m3 = re.match(r'^([A-H]{1,8})\s*$', lines[k].rstrip('\n'))
                    if m3:
                        fixed = f'{m1.group(1)}. （答案 {m3.group(1)}）'
                        fixes.append((i+1, f'{line.strip()} / {lines[j].strip()} / {lines[k].strip()}', fixed))
                        fixes.append((j+1, f'DELETE: {lines[j].strip()}', 'DELETE'))
                        fixes.append((k+1, f'DELETE: {lines[k].strip()}', 'DELETE'))
                        i = k + 1; continue
        
        # Pattern 5: ## N.\n\n## 答案 | XX  (answer with pipe on next heading line)
        if m1 and i+2 < len(lines):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                m2 = re.match(r'^#{1,3}\s*答案\s*\|\s*([A-H]{1,8})\s*$', lines[j].rstrip('\n'))
                if m2:
                    hm = re.match(r'^(#{1,3})\s*', line)
                    prefix = hm.group(1) if hm else ''
                    if prefix:
                        fixed = f'{prefix} {m1.group(1)}. （答案 {m2.group(1)}）'
                    else:
                        fixed = f'{m1.group(1)}. （答案 {m2.group(1)}）'
                    fixes.append((i+1, f'{line.strip()} / {lines[j].strip()}', fixed))
                    fixes.append((j+1, f'DELETE: {lines[j].strip()}', 'DELETE'))
                    i = j + 1; continue
        
        i += 1
    
    real_fixes = [f for f in fixes if f[2] != 'DELETE']
    print(f'  Found {len(real_fixes)} fixes', flush=True)
    for ln, old, new in real_fixes:
        print(f'  Line {ln}: "{old}" → "{new}"', flush=True)
    
    # Apply fixes
    if real_fixes:
        delete_lines = set(ln for ln, _, new in fixes if new == 'DELETE')
        replace_map = {ln: new for ln, _, new in fixes if new != 'DELETE'}
        
        new_lines = []
        for i, line in enumerate(lines):
            ln = i + 1
            if ln in delete_lines:
                continue  # skip deleted lines
            if ln in replace_map:
                new_lines.append(replace_map[ln] + '\n')
            else:
                new_lines.append(line)
        
        # Backup original
        backup = fpath + '.bak'
        if not os.path.exists(backup):
            import shutil
            shutil.copy2(fpath, backup)
            print(f'  Backup: {backup}', flush=True)
        
        with open(fpath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f'  ✅ Fixed {len(real_fixes)} entries, deleted {len(delete_lines)} lines, wrote {len(new_lines)} lines', flush=True)
