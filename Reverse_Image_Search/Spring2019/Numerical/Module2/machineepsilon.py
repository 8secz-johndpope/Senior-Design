val = 0.000001
y = 1.0+val
while y > 1.0:
    y = 1 + val
    val *= 0.99
print(val)
