"""An important module with some documentation on top.
   "When I created this code only me and God knew what it does. Now only God knows"
"""

# Random comment
# Random comment
# Random comment

x = "some string"
y = 'some string'
w = """some string"""

def well_documented_function(a, b):
    """ Returns the value of a + b, a - b and a * b
        As a tuple, in that order
    """
    plus = a + b
    minus = a - b
    times = a * b
    return (plus, minus, times)

def less_documented_function(a, b):
    """ Returns tuple(a + b, a - b, a * b)"""
    return (a + b, a - b, a * b)

def commented_function(a, b):
    # Returns tuple(a + b, a - b, a * b)
    return (a + b, a - b, a * b)

class MyClass:
    """ This is my class, not yours u.u
    """

    def __init__(self) -> None:
        self.owner = 'me'