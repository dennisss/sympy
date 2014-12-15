from sympy.parsing.latex import parse_latex

from sympy import *
from sympy.abc import x, y, z, w, pi, n, i

def test_latex_parser():
	inputs = {
		"x" : x,
		"1.234": 1.234,
		"-34": -34,
		"-8": -8,
        "-7/24": (-7/24),
		"x + y": (x + y),
		"xy": (x*y),
		"2x^3": (2*(x**3)),
		"(x+y)^4": (x+y)**4,
		"\\frac{x}{y}": (x/y),
		"\\begin{matrix} 1 & 2 \\\\ 3 & 4 \\end{matrix}": Matrix([ [1,2], [3,4] ]),
		"\\left[ \\begin{matrix} 1 & 2 \\\\ 3 & 4 \\end{matrix} \\right]": Matrix([ [1,2], [3,4] ]),
		"( x+ y) (z + w) ": ((x+y)*(z+w)),
		"\\sqrt[y] 2": root(2, y),
		"\\sqrt 2x": sqrt(2)*x,
		#"x + z\\pi = y": Eq(x+z*pi, y),
		"\\int x \mathrm{d}x": integrate(x, x),
        "\\sum^n_{i=1} 2i  \\;\\; + 1": (Sum(2*i, (i, 1, n)).doit() + 1)
	}

	for text, result in inputs.items():
		#print(text + " >>> ")
		#print(str(parse_latex(text)) + "\n")
		assert parse_latex(text) == result
