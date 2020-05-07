# import atexit
import sys
from datetime import datetime

_records = []


def _now():
    return datetime.now().strftime('%H:%M:%S')


def timed(s):
    return f'{_now()} {s}'


def failed(string, verbose=True):
    print(timed(string))
    if not verbose:
        report()
    sys.exit(1)


def report():
    special = []

    for c, t, w, s in _records:
        # make iso reports error with 'E: ' lines
        if w == 'answer' and s.startswith('E: '):
            special.append()
        if 'sudo: no tty present and no askpass program specified' in s:
            special.append('sudo is not setup to work without password')
            special.append('use sudo -S for your command')
        print(f'{t} {c:>3} {w} {s}')

    if special:
        print()
        print('feedback:')
        for s in special:
            print(s)
        print()


def _record(s, w='<', counter=[0]):
    s = s.strip()
    if not s:
        return s
    n = _now()
    c = counter.pop()
    counter.append(c+1)
    _records.append((c, n, w, s))
    return f'{s}\n'


def note(s):
    return _record(s, '=')


def command(s):
    return _record(s, '>')


def answer(s):
    return _record(s)


def completed(s='completed'):
    print(timed(s))
    sys.exit(0)
