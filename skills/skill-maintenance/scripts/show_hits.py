"""usage: python show_hits.py <package.skill> <deadpath|sandbox>
"""
import zipfile, sys

# EDIT THIS FOR YOUR SETUP. Keep these in step with scan_skills.py: that script finds
# WHICH packages have hits, this one prints the matching LINES. If the two lists drift
# apart you will chase a hit that this script cannot find.
#
# These are plain substrings, not regexes. Ships as examples; replace with your own.
PATTERNS = {
    'deadpath': ['Users\\YOURNAME\\', 'RetiredDir\\Projects', 'RetiredDir\\Scheduled'],
    'sandbox': ['YOUR_SANDBOX_FILE_API', 'outputs folder', 'outputs mount',
                'connected folder', 'connected-folder', 'truncat',
                'Operation not permitted', 'YOUR_HOSTED_TOOL_NAME', '/tmp'],
}

if len(sys.argv) < 3:
    print(__doc__.strip())
    sys.exit(2)

pkg = sys.argv[1]
keys = PATTERNS[sys.argv[2]]
z = zipfile.ZipFile(pkg)
for n in z.namelist():
    if not n.endswith(('.md', '.py', '.yaml', '.yml', '.txt')):
        continue
    for i, l in enumerate(z.read(n).decode('utf-8', errors='replace').splitlines(), 1):
        for k in keys:
            if k.lower() in l.lower():
                print(f'{n.split("/", 1)[-1]}:{i}: {l.strip()[:150]}')
                break
