"""
    Parse a LaTeX string and transform it into a SymPy expression
    Call as: sympy.parsing.latex.parse_latex(s)
"""


import re
import sympy
import sympy.abc

import sympy.functions.elementary.piecewise


from .latex_iter import TransformIter, TransformPriorityException



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
        elif len(a) == 0:
            return 0
        else:
            e = 1
            for i in range(len(a)): # Implicit multiplation, TODO: Move this elsewere, implicit multiplication doesn't always make sense
                if is_space(a[i]): # Ignore white space
                    continue

                e = e * a[i]

            return e
            #raise Error() # Could not transform it completely

    else:
        return expr([arr])


from .latex_tokenize import *



def parse_latex(s):
    '''Convert a tex string to an expression'''
    tokens = tokenize_latex(str(s))
    return expr(tokens)

