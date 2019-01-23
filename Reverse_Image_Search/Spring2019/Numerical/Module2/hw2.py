import math

x = 1

def fa(x):
    return math.sqrt(x + 1)

def fb(x):
    return math.atan(math.radians(x))

def fc(x):
    return math.sin(math.pi * math.radians(x))

def fd(x):
    return math.exp(-x)

def fe(x):
    return math.log(x)

# a)
print("a)")
print("Forward difference")
h = 1/4
print("h = 1/4:", (fa(x+h) - fa(x)) / h)
h = 1/8
print("h = 1/8:", (fa(x+h) - fa(x)) / h)
h = 1/16
print("h = 1/16:", (fa(x+h) - fa(x)) / h)
h = 1/32
print("h = 1/32:", (fa(x+h) - fa(x)) / h)
print("Central difference")
h = 1/4
print("h = 1/4:", (fa(x+h) - fa(x-h)) / (2*h))
h = 1/8
print("h = 1/8:", (fa(x+h) - fa(x-h)) / (2*h))
h = 1/16
print("h = 1/16:", (fa(x+h) - fa(x-h)) / (2*h))
h = 1/32
print("h = 1/32:", (fa(x+h) - fa(x-h)) / (2*h))

# b)
print("b)")
print("Forward difference")
h = 1/4
print("h = 1/4:", (fb(x+h) - fb(x-h)) / h)
h = 1/8
print("h = 1/8:", (fb(x+h) - fb(x-h)) / h)
h = 1/16
print("h = 1/16:", (fb(x+h) - fb(x-h)) / h)
h = 1/32
print("h = 1/32:", (fb(x+h) - fb(x-h)) / h)
print("Central difference")
h = 1/4
print("h = 1/4:", (fb(x+h) - fb(x-h)) / (2*h))
h = 1/8
print("h = 1/8:", (fb(x+h) - fb(x-h)) / (2*h))
h = 1/16
print("h = 1/16:", (fb(x+h) - fb(x-h)) / (2*h))
h = 1/32
print("h = 1/32:", (fb(x+h) - fb(x-h)) / (2*h))

# c)
print("c)")
print("Forward difference")
h = 1/4
print("h = 1/4:", (fc(x+h) - fc(x)) / h)
h = 1/8
print("h = 1/8:", (fc(x+h) - fc(x)) / h)
h = 1/16
print("h = 1/16:", (fc(x+h) - fc(x)) / h)
h = 1/32
print("h = 1/32:", (fc(x+h) - fc(x)) / h)
print("Central difference")
h = 1/4
print("h = 1/4:", (fc(x+h) - fc(x-h)) / (2*h))
h = 1/8
print("h = 1/8:", (fc(x+h) - fc(x-h)) / (2*h))
h = 1/16
print("h = 1/16:", (fc(x+h) - fc(x-h)) / (2*h))
h = 1/32
print("h = 1/32:", (fc(x+h) - fc(x-h)) / (2*h))

# d)
print("d)")
print("Forward difference")
h = 1/4
print("h = 1/4:", (fd(x+h) - fd(x)) / h)
h = 1/8
print("h = 1/8:", (fd(x+h) - fd(x)) / h)
h = 1/16
print("h = 1/16:", (fd(x+h) - fd(x)) / h)
h = 1/32
print("h = 1/32:", (fd(x+h) - fd(x)) / h)
print("Central difference")
h = 1/4
print("h = 1/4:", (fd(x+h) - fd(x-h)) / (2*h))
h = 1/8
print("h = 1/8:", (fd(x+h) - fd(x-h)) / (2*h))
h = 1/16
print("h = 1/16:", (fd(x+h) - fd(x-h)) / (2*h))
h = 1/32
print("h = 1/32:", (fd(x+h) - fd(x-h)) / (2*h))

# e)
print("e)")
print("Forward difference")
h = 1/4
print("h = 1/4:", (fe(x+h) - fe(x)) / h)
h = 1/8
print("h = 1/8:", (fe(x+h) - fe(x)) / h)
h = 1/16
print("h = 1/16:", (fe(x+h) - fe(x)) / h)
h = 1/32
print("h = 1/32:", (fe(x+h) - fe(x)) / h)
print("Central difference")
h = 1/4
print("h = 1/4:", (fe(x+h) - fe(x-h)) / (2*h))
h = 1/8
print("h = 1/8:", (fe(x+h) - fe(x-h)) / (2*h))
h = 1/16
print("h = 1/16:", (fe(x+h) - fe(x-h)) / (2*h))
h = 1/32
print("h = 1/32:", (fe(x+h) - fe(x-h)) / (2*h))
