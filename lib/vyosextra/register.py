class Registerer(object):
	def __init__ (self):
		self._register = {}

	def call(self, name, *args):
		return self._register[name](*args)

	def doc(self, name):
		return self._register[name].__doc__

	def registered(self):
		return list(self._register.keys())

	def _register_function(self, name, function):
		self._register[name] = function

	def _register_decorator(self, name):
		def _register(function):
			self._register[name] = function
			return function
		return _register

	def __call__(self, name=None, function=None):
		if function is None:
			return self._register_decorator(name)
		self._register_function(name,function)
