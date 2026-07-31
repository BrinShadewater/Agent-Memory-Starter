"""Rebuild a .skill from an extracted tree and validate before install.

usage: python build_skill.py <extracted-parent-dir> <skill-name> <out.skill> [expected-file-count]

Validates the packaging contract (traps 5-6 in skill-maintenance/environment-traps.md),
which are universal across runtimes, plus the dead-path checks added 2026-07-25.
"""
import zipfile, os, re, ast, json, sys

if len(sys.argv) < 4:
    print(__doc__.strip())
    sys.exit(2)

parent, name, out = sys.argv[1], sys.argv[2], sys.argv[3]
expected = int(sys.argv[4]) if len(sys.argv) > 4 else None
src = os.path.join(parent, name)
skip = {'__pycache__', '.DS_Store'}

files = []
for root, dirs, fs in os.walk(src):
    dirs[:] = [d for d in dirs if d not in skip]
    for f in sorted(fs):
        if f.endswith('.pyc') or f in skip:
            continue
        files.append(os.path.join(root, f))

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(files):
        z.write(f, os.path.relpath(f, parent).replace(os.sep, '/'))

z = zipfile.ZipFile(out)
names = [n for n in z.namelist() if not n.endswith('/')]
ok = True

def chk(label, cond):
    global ok
    print(('  PASS  ' if cond else '  FAIL  ') + label)
    if not cond:
        ok = False

print('Rebuilt:', out)
for n in names:
    print('   ', n)
print()

chk('zip integrity', z.testzip() is None)
chk('single top-level folder == skill name', {n.split('/')[0] for n in names} == {name})
chk('SKILL.md at skill root', f'{name}/SKILL.md' in names)
if expected:
    chk(f'file count unchanged ({expected})', len(names) == expected)

t = z.read(f'{name}/SKILL.md').decode('utf-8')
chk('frontmatter opens', t.startswith('---'))
m = re.search(r'^name:\s*(\S+)', t, re.M)
chk(f'name: is exactly {name}', bool(m) and m.group(1) == name)
chk('description: present', bool(re.search(r'^description:', t, re.M)))

# Dead-path sweep across every text file in the package.
DEAD = {
    'wrong home dir Users\\YOURNAME\\': 'Users\\YOURNAME\\',
    'nonexistent Claude\\Projects\\{': 'Claude\\Projects\\{',
    'Desktop\\Projects\\Claude': 'Desktop\\Projects\\Claude',
}
for n in names:
    if not n.endswith(('.md', '.py', '.txt', '.yaml', '.yml')):
        continue
    body = z.read(n).decode('utf-8', errors='replace')
    for label, needle in DEAD.items():
        chk(f'no {label} in {n.split("/", 1)[-1]}', needle not in body)

for n in names:
    if n.endswith('.py'):
        try:
            ast.parse(z.read(n).decode('utf-8'))
            chk('py compiles: ' + n.split('/')[-1], True)
        except Exception as e:
            chk('py compiles: ' + n.split('/')[-1] + ' -> ' + str(e), False)
    if n.endswith('.json'):
        try:
            json.loads(z.read(n).decode('utf-8'))
            chk('json loads: ' + n.split('/')[-1], True)
        except Exception as e:
            chk('json loads: ' + n.split('/')[-1] + ' -> ' + str(e), False)

print()
print('RESULT:', 'ALL CHECKS PASSED' if ok else 'VALIDATION FAILED - do not install')
sys.exit(0 if ok else 1)
