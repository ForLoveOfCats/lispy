import sys
from collections import OrderedDict
from fractions import Fraction


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
		return f"Interned: '{list(interner.symbols.keys())[self.id]}'"

	def __repr__(self):
		return self.__str__()


class Interner:
	def __init__(self):
		self.next_index = 0
		self.symbols = OrderedDict() #Newer python does this by default, lets be safe

	def next(self, symbol):
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

	output = Fraction(0)
	for arg in args:
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
	interner.next("print").id : print,
	interner.next("+").id : _lisp_add,
	interner.next("-").id : _lisp_sub,
	interner.next("*").id : _lisp_mul,
	interner.next("/").id : _lisp_div,
}]

if_id = interner.next("if").id
defvar_id = interner.next("defvar").id
setvar_id = interner.next("setvar").id

def lookup(interned, depth):
	global state

	while depth >= 0:
		found = state[depth].get(interned.id)
		if found != None:
			return found
		depth -= 1

	raise Exception(f"Unknown symbol {interned}")


def overwrite(interned, depth, value):
	global state

	while depth >= 0:
		if interned.id in state[depth]:
			state[depth][interned.id] = value
			return
		depth -= 1

	raise Exception(f"Unknown symbol {interned}")


def evaluate(node, depth):
	global state
	state.append({})
	output = None

	if isinstance(node, list):
		if len(node) >= 1 and isinstance(node[0], Interned):
			if node[0].id == if_id:
				cond = evaluate(node[1], depth + 1)
				if cond:
					output = evaluate(node[2], depth + 1)
				else:
					output = evaluate(node[3], depth + 1)

			elif node[0].id == defvar_id:
				symbol = node[1]
				value = None
				if len(node) >= 3:
					value = evaluate(node[2], depth + 1)
				state[depth][symbol.id] = value

			elif node[0].id == setvar_id:
				symbol = node[1]
				value = evaluate(node[2], depth + 1)
				overwrite(symbol, depth, value)

			else:
				symbol = lookup(node[0], depth)
				args = []
				for child in node[1:]:
					args.append(evaluate(child, depth + 1))
				output = symbol(*args)

		else:
			output = []
			for child in node:
				output.append(evaluate(child, depth + 1))

	else:
		if isinstance(node, Interned):
			output = lookup(node, depth)
		else:
			output = node

	state.pop()
	return output


evaluate(tree, 0)
