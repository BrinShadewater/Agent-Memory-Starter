"""Verify every skill that mentions a sandbox-only trap also names the host case.

The bulk scanner counts *mentions*, so correctly scoping a trap makes its count go UP.
Do not use mention counts as a pass/fail gate. This checks the thing that matters:
if a package talks about the mount/sandbox at all, does it say which runtime applies?
"""
import zipfile, glob, sys, re

# ============================ EDIT THIS FOR YOUR SETUP ============================
# These two lists are the whole configuration, and they ship as EXAMPLES from one
# specific environment. They are worthless - worse, actively misleading - until they
# describe yours.
#
# SANDBOX_TERMS: vocabulary a skill uses when it makes a claim about ONE runtime
#   (a sandbox, a mount, a hosted tool). Put your runtime's giveaway words here.
# HOST_TERMS:    vocabulary a skill uses when it names the OTHER case explicitly.
#
# The check is simply: if a package speaks the first vocabulary, does it also speak
# the second? A skill written inside a sandbox otherwise presents sandbox constraints
# as facts about the world, and an agent running on the host follows rules that do not
# apply to it.
#
# WORD BOUNDARIES ARE MANDATORY. A plain substring test for "mount" matched "paramount"
# in one template and "blend_amount" in a script - two false alarms against skills that
# make no runtime claim at all. Same shape as the `diff -rq` quoting trap documented in
# vault/10_Rules/verification-discipline.md.
SANDBOX_TERMS = [
    r'sandbox\w*',
    r'mount(s|ed|ing)?',
    r'YOUR_HOSTED_TOOL_NAME',      # e.g. a remote file-access tool
    r'YOUR_SANDBOX_FILE_API',      # e.g. a sandbox-only file call
    r'connected[- ]folder',
]
HOST_TERMS = [
    r'on the host',
    r'in place on the host',
    r'already on the real disk',
    r'YOUR_OS host',               # e.g. "windows host", "linux host"
]
# ==================================================================================

rows = []
for pkg in sorted(glob.glob('*.skill')):
    z = zipfile.ZipFile(pkg)
    text = ''
    for n in z.namelist():
        if n.endswith(('.md', '.py', '.txt', '.yaml', '.yml', '.cjs')):
            text += z.read(n).decode('utf-8', errors='replace').lower() + '\n'
    has_sb = any(re.search(t, text) for t in SANDBOX_TERMS)
    has_host = any(re.search(t, text) for t in HOST_TERMS)
    rows.append((pkg, has_sb, has_host))

print(f'{"package":38} {"talks sandbox":>14} {"names host":>11}   verdict')
print('-' * 82)
bad = []
for pkg, sb, host in rows:
    if not sb:
        verdict = 'n/a - no runtime claims'
    elif host:
        verdict = 'SCOPED'
    else:
        verdict = 'UNSCOPED  <<< fix'
        bad.append(pkg)
    print(f'{pkg:38} {str(sb):>14} {str(host):>11}   {verdict}')

print()
if bad:
    print('UNSCOPED packages:', ', '.join(bad))
else:
    print('Every package that makes a runtime claim names both runtimes.')
sys.exit(1 if bad else 0)
