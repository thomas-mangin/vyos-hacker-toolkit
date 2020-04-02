# import atexit
import sys
from datetime import datetime

_records = []

def _now():
	return datetime.now().strftime('%H:%M:%S')

def _timed(s):
	return f'{_now()} {s}'

def _end(reason, code):
	print(_timed(reason))
	special = []
	for c, t, w, s in _records:
		# make iso reports error with 'E: ' lines
		if w == 'answer' and s.startswith('E: '):
			special.append()
		print(f'{t} {c:>3} {w} {s}')

	if special:
		print()
		print('noteworthy:')
		for s in special:
			print(s)

	sys.exit(code)


def _record(s, w='<', counter=[0]):
	s = s.strip()
	if not s:
		return s
	n = _now()
	c = counter.pop()
	counter.append(c+1)
	_records.append((c, n, w, s))
	return f'{s}\n'

def report(s):
	return _record(s, '=')

def command(s):
	return _record(s, '>')

def answer(s):
	return _record(s)

def failed(s='failure'):
	_end(s, 1)

def completed(s='completed'):
	_end(s, 0)
	sys.exit(0)
