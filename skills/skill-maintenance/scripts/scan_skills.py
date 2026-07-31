import zipfile, glob, re, os, collections

# ============================ EDIT THIS FOR YOUR SETUP ============================
# Two defect classes worth scanning a skill library for. Both dicts ship as EXAMPLES
# from one specific environment; replace them with your own or the scan is noise.
#
# SANDBOX: markers of a skill making single-runtime claims. See check_scoped.py, which
#          asks the sharper question (does it name BOTH runtimes?).
# DEADPATH: paths you have actually retired. Every entry should be a location that no
#          longer exists on this machine, or the check cries wolf.
#
# NOTE: this script COUNTS MENTIONS. Correctly scoping a trap makes its count go UP.
# It is a LOCATOR, not a health metric - it tells you where to look, never whether
# anything is wrong. Do not wire it into a pass/fail gate.
SANDBOX = {
    'sandbox-only file API': r'YOUR_SANDBOX_FILE_API',
    'outputs mount':         r'outputs\s*(folder|mount|/)',
    'connected folder':      r'connected[- ]folder|connected folders',
    'ephemeral tmp':         r'sandbox[- ]native\s*/tmp|/tmp.*wiped|wiped between turns',
    'mount truncation':      r'truncat\w+',
    'read-only to bash':     r'read-only to (the )?bash|Operation not permitted',
    'hosted file tool':      r'YOUR_HOSTED_TOOL_NAME',
}
# NOTE: these are regex patterns matched against file text, so backslashes are
# doubled. A raw string cannot END in a backslash, which is why the first entry is
# written as a normal string.
DEADPATH = {
    'wrong home dir':  'Users\\\\YOURNAME\\\\',
    'retired dir A':   r'RetiredDir\\Projects',
    'retired dir B':   r'RetiredDir\\Scheduled',
}
# ==================================================================================

rows = []
for pkg in sorted(glob.glob('*.skill')):
    z = zipfile.ZipFile(pkg)
    hits = collections.Counter()
    dead = collections.Counter()
    for n in z.namelist():
        if not n.endswith(('.md', '.py', '.txt', '.yaml', '.yml')):
            continue
        body = z.read(n).decode('utf-8', errors='replace')
        for label, pat in SANDBOX.items():
            c = len(re.findall(pat, body, re.I))
            if c:
                hits[label] += c
        for label, pat in DEADPATH.items():
            c = len(re.findall(pat, body))
            if c:
                dead[label] += c
    rows.append((pkg, sum(hits.values()), sum(dead.values()), hits, dead))

rows.sort(key=lambda r: -(r[1] + r[2] * 10))
print(f'{"package":36} {"sandbox":>8} {"deadpath":>9}')
print('-' * 56)
for pkg, s, d, hits, dead in rows:
    flag = '  <<<' if (s or d) else ''
    print(f'{pkg:36} {s:>8} {d:>9}{flag}')

print()
print('=== detail for flagged packages ===')
for pkg, s, d, hits, dead in rows:
    if not (s or d):
        continue
    print(f'\n-- {pkg} --')
    if dead:
        print('   DEAD PATHS:', dict(dead))
    if hits:
        print('   sandbox markers:', dict(hits))
