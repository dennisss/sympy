"""
	Parse a LaTeX string and transform it into a SymPy expression
	Call as: sympy.parsing.latex.parse_latex(s)
"""


import re
import sympy
import sympy.abc


class TransformPriorityException(Exception):
	def __init__(self, num):
		self.num = num

	def __int__(self):
		return self.num

class TransformIter:
	'''Pseudo-iterator for performing tree-list transforms relative to the current node'''

	def __init__(self, arr, i, parent=None):
		self.arr = arr
		self.i = i
		self.parent = parent # TODO: If specified index shifts on this iterator bubble up to the parent

		self.set_priority(0)

	def __radd__(self, other):
		return self.i

	def __len__(self):
		return len(self.arr)

	def __getitem__(self, key):
		if type(key) is slice:
			start = self.i + key.start if key.start != None else None
			stop = self.i + key.stop if key.stop != None else None

			return self.arr[start:stop]
		else:
			i = self.i + key
			if i < 0 or i >= len(self.arr):
				return None

			return self.arr[self.i + key]

	def __setitem__(self, key, value):
		if type(key) is slice:
			if not type(value) is list:
				value = [value]

			start = self.i + key.start if key.start != None else None
			stop = self.i + key.stop if key.stop != None else None

			self.arr[start:stop] = value

			# Perform the operation and set the iterator to the last set element
			self.i = (start + len(value) - 1) if start != None else len(value) - 1
		else:
			i = self.i + key
			if i < 0 or i >= len(self.arr):
				raise Error()

			self.arr[self.i + key] = value

	def __delitem__(self, key):
		i = self.i + key

		if i < 0 or i >= len(self.arr):
			raise Error()

		if i <= self.i:
			self.i = self.i - 1

		del self.arr[i]

	def before(self):
		return self[:0]

	def after(self):
		return self[1:]

	def next(self):
		i = self.i + 1
		if i >= len(self.arr):
			return None
		else:
			it = TransformIter(self.arr, i, self.parent if self.parent else self)
			it.set_priority(self._priority)
			return it


	def set_priority(self, num):
		self._priority = num

	def priority(self, num):
		if self._priority < num:
			raise TransformPriorityException(num)
		return

	def match(self, pat):
		'''Match a token pattern'''
		pass



specials = "{}$&#^_%~"
pat = re.compile(r"((?:\\?[{}$&#^_%~])|(?:\\\\)|(?:\\[a-z]*\s*)|.)", re.IGNORECASE)

class TexToken:
	'''Represents a token extracted from Tex'''

	def __init__(self):
		pass

	@staticmethod
	def parse(data):
		'''Return the token representation of the data'''

		if len(data) > 0 and "\\" == data[0]:
			if len(data) == 2 and data[1] in specials: # Escaped character
				return TexRegular(data[1])

			else: # Control sequence
				name = data[1:]
				if name == "begin":
					return TexObject()
				return TexCommand.new(name)

		elif len(data) == 1 and data in (specials + '\\'): # Special character # TODO What about \\\\
			if data == "{":
				return TexGroup()
			else:
				return TexSpecial(data)
		else:
			return TexRegular(data)



	def append(self, token):
		'''
			Try to use the next token as part of the current.
			Returns whether or not it could use it.
			If it can't use token, then token will possibly become a separate entity
		'''
		if self.append is TexToken.append:
			raise NotImplementedError

		return False


class TexSpecial(TexToken):
	def __init__(self, data):
		TexToken.__init__(self)
		self.data = data
		self.arg = None

	def __str__(self):
		return str(self.data)

	def __repr__(self):
		return str(self)

	def append(self, token):
		if TexToken.append(self, token):
			return True

		if self.data == "_" or self.data == "^":
			if self.arg:
				return self.arg.append(token)
			else:
				self.arg = token
				return True

		return False

	def expr(self, it):
		if self.data == "^":

			it[:0] = expr(it[:0]) ** expr(self.arg)
			del it.next()[0]

		elif self.data == "_":
			del it[0]




num_pat = re.compile(r"^(([0-9]+\.?[0-9]*)|([0-9]*\.?[0-9]+))$")
int_pat = re.compile(r"[0-9]*")

class TexRegular(TexToken):
	'''A plain character with no special meaning'''

	def __init__(self, data):
		TexToken.__init__(self)
		self.data = data

	def __str__(self):
		return str(self.data)

	def __repr__(self):
		return "'" + str(self) + "'"

	def append(self, token):
		return TexToken.append(self, token)

	def expr(self, it):
		if self.data == "+": # TODO: What if one side is empty
			it.priority(2)
			it[:] = expr(it[:0]) + expr(it[1:])
		elif self.data == "-":
			it.priority(2)
			it[:] = expr(it[:0]) - expr(it[1:])
		elif self.data == "/":

			# TODO: {}^1/_2 will not work are the exponent was consumed by the empty group
			if type(it[-1]) == TexSpecial and it[-1].data == "^" and \
				type(it[1]) == TexSpecial and it[-1].data == "_":
					it[-1:2] = expr(it[-1].arg) / expr(it[1].arg)
			else:
				it[:] = expr(it[:0]) / expr(it[1:])
		elif self.data == "*":
			it.priority(3)
			it[:] = expr(it[:0]) * expr(it[1:])
		elif self.data == "=":
			it[:] = sympy.Eq( expr(it[:0]), expr(it[1:]) )

		elif self.data == "(":
			# TODO: Generalize this matching behavior as something like
			# it[lambda_start : lambda_stop]

			i = it.next()
			while type(i[0]) != TexRegular or i[0].data != ')':

				if type(i[0]) == TexRegular and i[0].data == "(": # Resolve the inner set of parenthesis first
					i[0].expr(i)

				i = i.next()

			#   (x)        =     expr x
			it[0:i.next()] = expr( it[1:i] )


		elif self.data == "!":
			it[:1] = sympy.factorial( expr(it[:0]) )

		elif re.match(num_pat, self.data): # Number
			while type(it[1]) == TexRegular and re.match(num_pat, self.data + it[1].data):
				self.data = self.data + it[1].data
				del it[1]

			it[0] = int(self.data) if re.match(int_pat, self.data) else float(self.data)
		else: # Eval as symbol
			it[0] = sympy.symbols(self.data)






class TexGroup(TexToken):
	'''
		A collection of tokens found in {curly} braces
		An entire string of tex is also considered a TexGroup by this parser
	'''

	def __init__(self, closure=lambda t: (type(t) is TexSpecial and t.data == "}") ):
		TexToken.__init__(self)
		self.closure = closure # Determine if the group is closed by a token
		self.closed = False
		self.end = None
		self.inner = []

	def __str__(self):
		s = ""
		for i in range(len(self.inner)):
			s = s + str(self.inner[i])

		return s

	def __repr__(self):
		return repr(self.inner)

	def append(self, token):
		if self.closed:
			return self.end.append(token)

		# Try to give the token to an inner item first
		if len(self.inner) > 0 and self.inner[-1].append(token):
			return True

		if self.closure(token):
			self.closed = True
			self.end = token
		else:
			self.inner.append(token)

		return True

	def empty(self):
		return self.inner.length == 0

	def expr(self, it):
		it[0] = expr(self.inner)





class TexTable(TexGroup):
	'''
		Parses out rows and columns in the form of ... & ... & ... \\ ... & ... & ... while keeping track of the outer group
		All the inner tokens are still located in self.inner, but any table data is located in self.table[row][col]
	'''

	def __init__(self, closure):
		TexGroup.__init__(self, closure)
		self.table = []

	def append(self, token):
		res = TexGroup.append(self, token)

		if not res: # Table/outer group ended
			return False

		if self.closed:
			return res


		iscoldelim = lambda t: type(t) is TexSpecial and t.data == "&"
		isrowdelim = lambda t: isinstance(t, TexCommand) and t.name == "\\"
		isdelim = lambda t: (iscoldelim(t) or isrowdelim(t))

		if len(self.table) == 0:
			self.table = [ [ TexGroup(isdelim) ] ]

		r = len(self.table) - 1
		c = len(self.table[r]) - 1


		while not self.table[r][c].append(token): # The col or row/col ended

			endtok = self.table[r][c].end

			if isrowdelim(endtok):
				self.table.append([])
				r = r + 1
				c = -1

			self.table[r].append( TexGroup(isdelim) )
			c = c + 1


		return True


tex_spacing_commands = [",", ":", ";", "!" ] # \! is negative spacing
tex_commands = {} # Class dictionary based on the name of the control first control sequence

class TexCommand(TexToken):
	def __init__(self):
		TexToken.__init__(self)

		for i in range(len(self.args)):
			setattr(self, self.args[i], self.defaults[i] if i < len(self.defaults) else None)

		self._argi = -1
		self._lastarg = None


	@staticmethod
	def define(name, args = [], defaults=[]):

		if type(name) is dict:
			d = name
			for k in d:
				v = d[k]
				TexCommand.define(k, v[0], v[1])
			return

		t = type(name, (TexCommand, object), {
			'args': args,
			'name': name,
			'defaults': defaults
		})
		tex_commands[name] = t

	@staticmethod
	def new(name):
		if not name in tex_commands:
			TexCommand.define(name)

		return tex_commands[name]()


	def __str__(self):
		return "\\" + str(self.name) # TODO: Also encode arguments

	def __repr__(self):
		args = str(self.name) + " "
		for i in range(0, len(self.args)):
			k = self.args[i]
			v = getattr(self, k, None)
			args = args + " " + k + "='" + str(v) + "'"

		return "[" + args + "]"

	def append(self, token):
		if TexToken.append(self, token):
			return True

		# See if the next token is part of the last
		if self._lastarg and self._lastarg.append(token):
			return True


		# Otherwise, if there are more defined arguments, try to add it as a new argument
		if self._argi < len(self.args) - 1:

			self._argi = self._argi + 1
			argname = self.args[self._argi]

			if getattr(self, argname) != None: # It has a default value, so it is optional
				self._lastarg = None
				if type(token) is TexRegular and token.data == "[": # Valid start for an optional arg
					g = TexGroup(closure=lambda t: (type(t) is TexRegular and t.data == "]"))
					self._lastarg = g
					setattr(self, argname, g)
					return True
				else: # Skip the optional arg and try the next
					return self.append(token)



			#if type(token) is TexRegular and token.data == "[" and getattr()


			setattr(self, argname, token)
			self._lastarg = token
			return True

		return False

	def expr(self, it):
		name = self.name

		if name == "frac":
			it[0] = expr(self.upper) / expr(self.lower)
		elif name == "over":
			it[:] = expr(it[:0]) / expr(it[1:])
		elif name == "times":
			it[:] = expr(it[:0]) * expr(it[1:])

		elif name == "sin":
			it[0] = sympy.sin( expr(self.token) )
		elif name == "cos":
			it[0] = sympy.cos( expr(self.token) )
		elif name == "choose":
			it[:] = sympy.binomial( expr(it[:0]), expr(it[1:]) )
		elif name == "sqrt":
			it[0] = sympy.root( expr(self.token), expr(self.n) )

		elif name == "int":
			# TODO: This needs to work more like the parenthesis transform
			i = it.next()
			instart = True
			lower = None
			upper = None

			# TODO: Try to find spacing first, then fall back to mathrm
			# Pattern: [(int), (limits)?, (^|_){0-2}, (.+), (<spacing>)?, (mathrm of d or del), (.)
			while type(i[0]) != tex_commands["mathrm"] or str(i[0].token) != 'd': # TODO: Do better letter checking
				if instart:
					t = i[0]
					if type(t) == tex_commands["limits"]:
						del i[0]
					elif type(t) == TexSpecial and t.data == "^":
						upper = expr(t.arg)
					elif type(t) == TexSpecial and t.data == "_":
						lower = expr(t.arg)
					else:
						instart = False

				i = i.next()

			inner = expr( it[1:i] )
			var = expr(i[1])

			it[0:i.next().next()] = sympy.integrate(inner, (var, lower, upper))



		else:
			sym = getattr(sympy.abc, name, None)
			if sym:
				it[0] = sym




TexCommand.define({
	"begin": ( ['name'], [] ),
	"end": ( ['name'], [] ),
	"left": ( ['token'], [] ),
	"right": ( ['token'], [] ),
	"limits": ([], []),
	"sqrt": ( ['n', 'token'], [2] ),
	"frac": ( ['upper', 'lower'], [] ),
	"mathrm": ( ['token'], [] ),

	"sin": ( ['token'], [] ),
	"cos": ( ['token'], [] ),
	"tan": ( ['token'], [] ),
	"\\": ( ['spacing'], [0] )

})
# See http://en.wikibooks.org/wiki/LaTeX/Mathematics for a lot more examples to implement


# Defined Environment
tex_classes = {}
class TexObject(tex_commands['begin'], TexTable):
	'''For command sets: \begin{name} ... \end{name}'''

	def __init__(self):
		TexCommand.__init__(self)
		TexTable.__init__(self, lambda t: (type(t) is tex_commands["end"]))

	def new(name):
		pass

	def append(self, token):
		if not TexCommand.append(self, token):
			return TexTable.append(self, token)

		return True

	def expr(self, it):
		self.name = str(self.name)

		if self.name == "matrix" or self.name == "array": # TODO: 'array' should have a stricter check
			data = self.table[:]

			# Isolate each cell and transform them separately
			for i in range(len(data)):
				for j in range(len(data[i])):
					data[i][j] = expr(data[i][j])

			it[0] = sympy.Matrix(data)

			if type(it[-1]) is tex_commands["left"] \
				and type(it[1]) is tex_commands["right"]:
				# I'm probably a matrix (or the determinant of a matrix)

				if str(it[-1].token) == "|":
					it[0] = it[0].det()

				del it[-1]; del it[1]


def tokenize_latex(tex):
	raw = re.split(pat, tex)

	tokens = TexGroup(lambda t: False)
	comment = False
	for i in range(0, len(raw)): # Interpret every token

		r = raw[i]
		s = r.strip()

		if s == "%":
			comment = True

		if not comment and len(s) > 0: # Drop comments
			tokens.append(TexToken.parse(s))

		if r == "\n":
			comment = False

	return tokens

def expr(arr):
	if type(arr) is list:
		a = arr[:]

		priorities = [0] # Kind of inverted: 0 for run immediately, higher for run later

		while len(priorities) > 0:

			it = TransformIter(a, 0, None)
			it.set_priority(priorities.pop(0))

			# Iterate through and allow each token to run expr()
			while it:
				if isinstance(it[0], TexToken):
					try:
						it[0].expr(it)
					# TODO: This can happen multiple times for the same symbol if another token runs expr()
					except TransformPriorityException as e:
						priorities.append(int(e))

				it = it.next()

			priorities = sorted(set(priorities))

		if len(a) == 1:
			return a[0]
		else:
			e = 1
			for i in range(len(a)): # Implicit multiplation, TODO: Move this elsewere, implicit multiplication doesn't always make sense
				e = e * a[i]

			return e
			#raise Error() # Could not transform it completely

	else:
		return expr([arr])


def parse_latex(s):
	'''Convert a tex string to an expression'''
	tokens = tokenize_latex(s)
	return expr(tokens)

