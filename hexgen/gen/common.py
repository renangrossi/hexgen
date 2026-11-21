"""Small helpers shared by the generators.

Every generated fact is a Line: a label, the text, and where it came from, so the
gazetteer can cite the book and page for anything it prints.
"""
import re


def line(label, res, cite=None):
    """res is a Result from Registry.roll, or plain text."""
    if isinstance(res, dict):
        return {'label': label, 'text': res['text'], 'cite': cite or res.get('cite', '')}
    return {'label': label, 'text': str(res), 'cite': cite or ''}


def roll(R, label, tid, col=None, mod=0):
    if tid not in R:
        return None
    return line(label, R.roll(tid, col, mod))


def first_sentence(text):
    """'Recent. The post was …' → ('Recent', 'The post was …')."""
    m = re.match(r'^([^.]{1,60})\.\s+(.*)$', text)
    return (m.group(1), m.group(2)) if m else (text, '')


def tidy_ss(text):
    """Drop Spectacular Settlements' mechanical asides: '(+2 to size roll)'."""
    text = re.sub(r'\s*\((?:[+−-]\d+|Skip|Roll|Re-?roll)[^)]*\)', '', text)
    text = re.sub(r'\s*\[[^\]]*\]', '', text)
    return text.strip()


def name_person(R):
    first = R.text('oh.male' if R.dice.chance(1, 2) else 'oh.female')
    sur = (R.text('oh.surname-prefix').rstrip('-') + R.text('oh.surname-suffix').lstrip('-')).title()
    return f'{first} {sur}'


def name_settlement(R):
    p = R.text('oh.surname-prefix').rstrip('-')
    s = R.text('oh.surname-suffix').lstrip('-')
    return (p + s).title()
