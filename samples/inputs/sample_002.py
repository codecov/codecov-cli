from collections import *


def simple_function(a, b, c, d, e, f, g, h, i, j, k):
    # assert a == b
    pass

def some_more_if_stuff(val):
    if val >= 100:
        val = val + 1
    elif val >= 10:
        val = val * 2
    else:
        val = val - 1
    return val ** 2

def single_line_minecraft(bb):
    k = 3;bb.matrix_blocks.render(); import minecraft; minecraft.run()

a = 3
print("It's me mario")
try:
    a = a + 1
except Exception:
    print("b")
assert a
c = 0
while c < 1:
    print("b")

def nested_conditionals(val):
    if val > 10:
        if val > 100:
            if val > 1000:
                return 'large value'