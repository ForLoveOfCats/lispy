# Crappy little lisp written in Python in a day or so

### Video demo: https://www.youtube.com/watch?v=i1F4oafrp1o

I was bored in class so I started hacking on this. By the end
of the day it could run some non-trival code. This is not a
good lisp, mostly due to my lack of knowledge of lisps, but also
because the implementation is extremely hacky, being ~300 lines
of Python.

I implemented it in Python because I was interested to see how
much I could lean on the host language's runtime. It turns out
Python is a great host language for a lisp, all things considered.
However writing in such a dynamic language proved to be a very
frustrating experience.

## Features
 * Numbers (integer and decimals, represented by big int fractions
   from the Python std)
 * Strings (no escape sequences)
 * Bools
 * None value
 * Dymamically scoped variables
 * Lambda expressions
