"""Static project checks. Python 3.9+, standard library only, no network."""

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    'README.md', 'AGENTS.md', 'LESSONS.md', 'index.html',
    'docs/CONSTITUTION.md', 'docs/WORKFLOW.md', 'docs/ROADMAP.md',
    'docs/DECISIONS.md', 'docs/QUALITY.md', 'docs/SESSION.md',
    'specs/README.md', 'specs/TEMPLATE.md', 'specs/000-project-foundation.md',
    'specs/001-sinus-cosinus.md', 'specs/002-tangens-cotangens.md',
    'specs/003-newton-binomial.md', 'specs/004-function-transformations.md',
    'specs/005-public-privacy.md', 'scripts/check_privacy.py',
)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.duplicates = []
        self.links = []
        self.lang = None
        self.charset = False
        self.viewport = False
        self.title = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            value = attrs['id']
            if value in self.ids:
                self.duplicates.append(value)
            self.ids.add(value)
        if tag == 'html':
            self.lang = attrs.get('lang')
        if tag == 'meta':
            self.charset |= attrs.get('charset', '').lower() == 'utf-8'
            self.viewport |= attrs.get('name') == 'viewport'
        if tag == 'title':
            self.in_title = True
        for key in ('href', 'src'):
            if attrs.get(key):
                self.links.append(attrs[key])

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def main():
    errors = []
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            errors.append('Missing required file: ' + name)

    paths = sorted(set(ROOT.glob('*.html')) | set(ROOT.glob('*.md'))
                   | set((ROOT / 'docs').glob('*.md'))
                   | set((ROOT / 'specs').glob('*.md')))
    texts, pages = {}, {}
    for path in paths:
        if path.name.startswith('.'):
            continue
        try:
            texts[path] = path.read_text(encoding='utf-8-sig')
        except UnicodeError:
            errors.append(str(path.relative_to(ROOT)) + ': invalid UTF-8')
            continue
        if path.suffix == '.html':
            page = Page()
            page.feed(texts[path])
            pages[path] = page
            label = str(path.relative_to(ROOT))
            for value in page.duplicates:
                errors.append(label + ': duplicate id ' + str(value))
            if page.lang != 'ru' or not page.charset or not page.viewport or not page.title.strip():
                errors.append(label + ': expected lang=ru, UTF-8, viewport and nonempty title')

    link_count = 0
    for path, text in texts.items():
        if path in pages:
            links = pages[path].links
        else:
            prose = re.sub(r'```.*?```', '', text, flags=re.S)
            links = re.findall(r'\[[^\]\n]+\]\(([^)\s]+)\)', prose)
        for link in links:
            parts = urlsplit(link.strip('<>'))
            if parts.scheme or parts.netloc:
                continue
            link_count += 1
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            label = str(path.relative_to(ROOT))
            if not target.is_relative_to(ROOT):
                errors.append(label + ': link escapes project: ' + link)
            elif not target.is_file():
                errors.append(label + ': missing link target: ' + link)
            elif parts.fragment and target in pages:
                if unquote(parts.fragment) not in pages[target].ids:
                    errors.append(label + ': missing HTML anchor: ' + link)

    catalog_path = ROOT / 'index.html'
    registry = texts.get(ROOT / 'LESSONS.md', '')
    if catalog_path in pages:
        catalog_links = {urlsplit(x).path for x in pages[catalog_path].links}
        for lesson in pages:
            if lesson.name == 'index.html':
                continue
            if lesson.name not in catalog_links:
                errors.append(lesson.name + ': missing from index.html')
            if not re.search(r'\]\(' + re.escape(lesson.name) + r'\)', registry):
                errors.append(lesson.name + ': missing from LESSONS.md')

    if errors:
        for error in errors:
            print('ERROR: ' + error)
        print(f'FAILED: {len(errors)} issue(s).')
        return 1
    print(f'OK: {len(texts)} documents, {len(pages)} HTML pages, '
          f'{link_count} local links; lesson catalog and registry agree.')
    print('Static checks only: JavaScript and mathematical answers are not executed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
