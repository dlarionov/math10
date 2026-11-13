"""Heuristic public-repository audit. Reports locations, never matched values."""

import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NAME = 'math10 contributors'
PUBLIC_EMAIL = 'contributors@math10.invalid'
TEXT_SUFFIXES = {'.md', '.html', '.py', '.json', '.yml', '.yaml', '.toml', '.txt', '.js', '.css', '.xml', '.svg', '.ini', '.cfg', '.conf', '.sh', '.ps1'}
RULES = {
    'private key': r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'access token': r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|glpat-[A-Za-z0-9_-]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,})\b',
    'AWS access key': r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'credential URL': r'https?://[^\s/<>"\x27:]+:[^\s/<>"\x27]+@',
    'personal home path': r'(?:[A-Za-z]:[/\\]Users[/\\][^\s/\\]+|/(?:home|Users)/[^\s/]+)',
    'private family context': r'\bдоч(?:ь|ер\w*|к\w*)\b',
    'assigned credential': r'(?im)^\s*(?:[A-Z_]*(?:SECRET|PASSWORD|ACCESS_TOKEN|API_KEY)[A-Z_]*)\s*=\s*["\x27]?[A-Za-z0-9_+/=-]{12,}',
}
EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')


def git(*args):
    return subprocess.check_output(['git', '-c', 'safe.directory=' + str(ROOT), *args], cwd=ROOT)


def inspect(label, data):
    issues = []
    try:
        text = data.decode('utf-8-sig')
    except UnicodeError:
        return issues
    for category, pattern in RULES.items():
        if re.search(pattern, text, re.I):
            issues.append((label, category))
    for address in EMAIL.findall(text):
        domain = address.rsplit('@', 1)[1].lower()
        if not (domain.endswith('.invalid') or domain in {'example.com', 'example.org', 'example.net'}):
            issues.append((label, 'non-example email'))
            break
    return issues


def check_paths(entries, staged=False):
    issues = []
    for name in entries:
        path = Path(name)
        if path.name.startswith('.env') and path.name != '.env.example':
            issues.append((name, 'environment file'))
        if path.suffix.lower() in {'.pem', '.key', '.p12', '.pfx', '.kdbx'}:
            issues.append((name, 'sensitive file type'))
        if any(part in {'.aws', '.codex', '.agents'} for part in path.parts):
            issues.append((name, 'local settings directory'))
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {'.gitignore', '.gitattributes'}:
            continue
        if staged:
            data = git('show', ':' + name)
        else:
            target = ROOT / name
            if not target.is_file():
                continue
            data = target.read_bytes()
        issues.extend(inspect(name, data))
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Inspect the index, including files ignored in the worktree.')
    parser.add_argument('--history', metavar='REF', help='Also audit every reachable commit and text blob in this ref.')
    args = parser.parse_args()
    listing = ('ls-files', '--cached', '-z') if args.staged else ('ls-files', '--cached', '--others', '--exclude-standard', '-z')
    names = sorted(set(git(*listing).decode('utf-8').strip('\0').split('\0')) - {''})
    issues = check_paths(names, staged=args.staged)
    commits = blobs = 0
    if args.history:
        # Resolve to an object first so the ref cannot become a Git option.
        ref = git('rev-parse', '--verify', args.history + '^{commit}').decode().strip()
        rows = git('log', '--format=%H%x00%an%x00%ae%x00%cn%x00%ce', ref).decode().splitlines()
        for row in rows:
            oid, an, ae, cn, ce = row.split('\0')
            commits += 1
            if (an, ae, cn, ce) != (PUBLIC_NAME, PUBLIC_EMAIL, PUBLIC_NAME, PUBLIC_EMAIL):
                issues.append((oid[:12], 'non-public author/committer identity'))
            issues.extend(inspect(oid[:12] + ':message', git('show', '-s', '--format=%B', oid)))
        seen = set()
        for row in git('rev-list', '--objects', ref).decode().splitlines():
            parts = row.split(' ', 1)
            if len(parts) != 2:
                continue
            oid, name = parts
            if oid in seen:
                continue
            seen.add(oid)
            if git('cat-file', '-t', oid).strip() != b'blob':
                continue
            blobs += 1
            if Path(name).suffix.lower() in TEXT_SUFFIXES or Path(name).name in {'.gitignore', '.gitattributes'}:
                issues.extend(inspect(oid[:12] + ':' + name, git('cat-file', 'blob', oid)))
    if issues:
        for label, category in issues:
            print('REVIEW: ' + label + ' [' + category + ']')
        print(f'FAILED: {len(issues)} privacy finding(s). Matched values are withheld.')
        return 1
    print(f'OK: privacy patterns checked in {len(names)} files, {commits} commits and {blobs} historical blobs.')
    print('Heuristic checks do not replace review or remove cached copies on external services.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
