import sys
from collections import OrderedDict
from fractions import Fraction


Fraction.__repr__ = Fraction.__str__


def panic(*args):
	print("Panic:", *args)
	sys.exit(-1)

def my_assert(expression, *message):
	if not expression:
		if len(message) > 0:
			panic("Assertion failed,", *message)
		else:
			panic("Assertion failed")


program = ""
with open("./program.lispy", "r") as file:
	program = file.read()


tokens = []
current_token = ""
in_string = False
for car in program:
	if in_string:
		current_token += car
		if car == "\"":
			tokens.append(current_token)
			current_token = ""
			in_string = False

	else:
		if car == ' ' or car == '\t' or car == '\r' or car == '\n':
			if len(current_token) > 0:
				tokens.append(current_token)
				current_token = ""

		elif car == '(' or car == ')':
			if len(current_token) > 0:
				tokens.append(current_token)
				current_token = ""
			tokens.append(str(car))

		elif car == "\"":
			if len(current_token) > 0:
				panic("Invalid syntax, quotation mark cannot be within value")
			current_token += car
			in_string = True

		else:
			current_token += car


class RefOfInner:
	def __init__(self, arg):
		self.inner = arg


class Interned:
	def __init__(self, numerical_id):
		self.id = numerical_id

	def __str__(self):
		global interner
		return f"'{list(interner.symbols.keys())[self.id]}'"

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		return self.id == other.id

	def __hash__(self):
		return self.id.__hash__()


class Interner:
	def __init__(self):
		self.next_index = 0
		self.symbols = OrderedDict() #Newer python does this by default, lets be safe

	def next(self, symbol):
		if not isinstance(symbol, str):
			panic(type(symbol))

		if symbol not in self.symbols:
			index = self.next_index
			self.next_index += 1
			self.symbols[symbol] = index
			return Interned(index)

		else:
			return Interned(self.symbols[symbol])


interner = Interner()


def parse(index):
	global tokens, interner

	self = []
	while index.inner < len(tokens):
		token = tokens[index.inner]

		if token == "(":
			index.inner += 1
			self.append(parse(index))

		elif token == ')':
			return self

		else:
			if token.isnumeric():
				self.append(Fraction(token))
			elif len(token) >= 2 and token.startswith("\"") and token.endswith("\""):
				self.append(token[1:-1])
			elif token == "None":
				self.append(None)
			elif token == "True":
				self.append(True)
			elif token == "False":
				self.append(False)
			else:
				self.append(interner.next(token))

		index.inner += 1

	panic("Unbalanced parens when parsing")


my_assert(tokens[0] == "(", "first token must be open paren")
index = RefOfInner(1)
tree = parse(index)


def _lisp_eq(*args):
	for index in range(0, len(args) - 2):
		if args[index] != args[index + 1]:
			return False
	return True


def _lisp_add(*args):
	if len(args) == 0:
		return None

	output = Fraction(0)
	for arg in args:
		output += arg
	return output

def _lisp_sub(*args):
	if len(args) == 0:
		return None

	output = args[0]
	for arg in args[1:]:
		output -= arg
	return output

def _lisp_mul(*args):
	if len(args) == 0:
		return None

	output = args[0]
	for arg in args[1:]:
		output *= arg
	return output

def _lisp_div(*args):
	if len(args) == 0:
		return None

	output = args[0]
	for arg in args[1:]:
		output /= arg
	return output

state = [{
	interner.next("list") : lambda *args: list(args),

	interner.next("=") : _lisp_eq,
	interner.next(">") : lambda a, b: a > b,
	interner.next(">=") : lambda a, b: a >= b,
	interner.next("<") : lambda a, b: a < b,
	interner.next("<=") : lambda a, b: a <= b,
	interner.next("not") : lambda a: not a,

	interner.next("print") : print,

	interner.next("+") : _lisp_add,
	interner.next("-") : _lisp_sub,
	interner.next("*") : _lisp_mul,
	interner.next("/") : _lisp_div,
	interner.next("mod") : lambda a, b: a % b,
}]

if_symbol = interner.next("if")
lambda_symbol = interner.next("lambda")
defvar_symbol = interner.next("defvar")
setvar_symbol = interner.next("setvar")


class CallableDefunc:
	def __init__(self, arg_symbols, body):
		self.arg_symbols = arg_symbols
		self.body = body

	def __call__(self, *args):
		global state
		frame = {}
		for index, arg_symbol in enumerate(self.arg_symbols):
			frame[arg_symbol] = args[index]
		state.append(frame)
		output = evaluate(self.body)
		state.pop()
		return output


def lookup(interned):
	global state

	for index in reversed(range(0, len(state))):
		if interned in state[index]:
			return state[index][interned]

	raise Exception(f"Unknown symbol {interned}")


def overwrite(interned, value):
	global state

	for index in reversed(range(0, len(state))):
		if interned in state[index]:
			state[index][interned] = value
			return

	raise Exception(f"Unknown symbol {interned}")


def evaluate(node):
	global state
	state.append({})
	output = None

	if isinstance(node, list):
		if len(node) > 1 and isinstance(node[0], Interned):
			if node[0] == if_symbol:
				cond = evaluate(node[1])
				if cond:
					output = evaluate(node[2])
				else:
					output = evaluate(node[3])

			elif node[0] == lambda_symbol:
				output = CallableDefunc(node[1], node[2])

			elif node[0] == defvar_symbol:
				symbol = node[1]
				value = None
				if len(node) >= 3:
					value = evaluate(node[2])
				state[-2][symbol] = value

			elif node[0] == setvar_symbol:
				symbol = node[1]
				value = evaluate(node[2])
				overwrite(symbol, value)
				output = value

			else:
				value = lookup(node[0])
				args = []
				for child in node[1:]:
					args.append(evaluate(child))
				output = value(*args)

		elif len(node) == 0:
			output = None

		else:
			for child in node:
				output = evaluate(child)

	else:
		if isinstance(node, Interned):
			output = lookup(node)
		else:
			output = node

	state.pop()
	return output


evaluate(tree)
