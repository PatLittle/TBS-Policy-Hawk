"""Reproduce this report's English-text metrics; not part of source monitoring.

Run in an isolated environment with beautifulsoup4==4.15.0, textstat==0.7.13,
nltk==3.10.4 and pyphen==0.18.1 (dictionary hash recorded in metrics.json):
    python measure.py
Inputs are the preserved 2026-10-22 HTML captures. Output: metrics.json.
"""
import hashlib
import importlib.metadata
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
import textstat

HERE = Path(__file__).resolve().parent
CAPTURES = HERE.parent / 'captures' / '20261022'
textstat.set_lang('en_US')
LABEL = re.compile(r'^(\d+(?:\.\d+)*)\.?\s+')


def measure(name):
    path = CAPTURES / f'{name}.html'
    raw = path.read_bytes()
    soup = BeautifulSoup(raw, 'html.parser')
    container = soup.find('h2', id='toc1').parent.parent
    sections = [s for s in container.find_all('section', recursive=False)
                if s.find('h2', recursive=False)
                and re.fullmatch(r'toc\d+', s.find('h2').get('id', ''))]
    # Include numbered body sections and the predecessor's institutional appendix.
    # Exclude page title, replacement banner, TOCs, notes, copyright and page furniture.
    blocks, labels, appendix_words = [], [], 0
    for section in sections:
        for extra in section.select('details, sup, script, style'):
            extra.decompose()
        for element in section.find_all(['h2', 'h3', 'h4', 'p']):
            match = LABEL.match(element.get_text(' ', strip=True))
            if match:
                label = match[1]
                labels.append(label[:-2] if label.endswith('.0') else label)
        section_blocks = []
        for element in section.find_all(['p', 'li']):
            # Copy each block and remove nested lists so their children aren't counted twice.
            block = BeautifulSoup(str(element), 'html.parser').find(element.name)
            for nested in block.find_all(['ul', 'ol']):
                nested.decompose()
            text = re.sub(r'\s+', ' ', block.get_text(' ', strip=True)).strip()
            text = LABEL.sub('', text)
            if text:
                # A paragraph/list-item boundary ends a reading unit. Do not split
                # semicolons within prose; normalize only the block's trailing punctuation.
                text = text.rstrip(';:, ')
                if not text.endswith(('.', '!', '?')):
                    text += '.'
                section_blocks.append(text)
        blocks.extend(section_blocks)
        if section.find('h2')['id'] == 'toc10':
            appendix_words = textstat.lexicon_count('\n'.join(section_blocks))
    assert len(labels) == len(set(labels)), 'Duplicate clause label'
    terminal = [n for n in labels if not any(m.startswith(n + '.') for m in labels)]
    text = '\n'.join(blocks)
    words = textstat.lexicon_count(text)
    sentences = textstat.sentence_count(text)
    syllables = textstat.syllable_count(text)
    grade = 0.39 * words / sentences + 11.8 * syllables / words - 15.59
    assert abs(grade - textstat.flesch_kincaid_grade(text)) < 0.001
    return {
        'source': str(path.relative_to(HERE.parent)),
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'numbered_units_all_levels': len(labels),
        'terminal_numbered_units': len(terminal),
        'terminal_labels': terminal,
        'prose_blocks': len(blocks),
        'words': words,
        'appendix_words': appendix_words,
        'sentences_block_adjusted': sentences,
        'syllables_estimated': syllables,
        'words_per_sentence': round(words / sentences, 3),
        'flesch_kincaid_grade': round(grade, 3),
        'flesch_reading_ease': round(textstat.flesch_reading_ease(text), 3),
    }


if __name__ == '__main__':
    result = {
        'method': 'English directive prose, headings excluded, appendix included; block-adjusted sentence boundaries; textstat en_US; terminal printed numbering is structural, not an obligation count.',
        'packages': {p: importlib.metadata.version(p) for p in ['beautifulsoup4', 'textstat', 'nltk', 'pyphen']},
        'pronunciation_dictionary_sha256': hashlib.sha256(__import__('nltk').data.find('corpora/cmudict/cmudict').open().read()).hexdigest(),
        'predecessor': measure('previous'),
        'successor': measure('current'),
    }
    (HERE / 'metrics.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
