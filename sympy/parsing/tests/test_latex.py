from sympy.parsing.latex import parse_latex

from sympy import *
from sympy.abc import x, y, z, w, pi

def test_latex_parser():
	inputs = {
		"x" : x,
		"1.234": 1.234,
		"x + y": (x + y),
		"xy": (x*y),
		"\\frac{x}{y}": (x/y),
		"\\begin{matrix} 1 & 2 \\\\ 3 & 4 \\end{matrix}": Matrix([ [1,2], [3,4] ]),
		"\\left[ \\begin{matrix} 1 & 2 \\\\ 3 & 4 \\end{matrix} \\right]": Matrix([ [1,2], [3,4] ]),
		"( x+ y) (z + w) ": ((x+y)*(z+w)),
		"\\sqrt[y] 2": root(2, y),
		"\\sqrt 2x": sqrt(2)*x,
		"x + z*\\pi = y": Eq(x+z*pi, y),
		"\\int x \mathrm{d}x": integrate(x, x)
	}

	for text, result in inputs.items():
		print(parse_latex(text))
		assert parse_latex(text) == result
