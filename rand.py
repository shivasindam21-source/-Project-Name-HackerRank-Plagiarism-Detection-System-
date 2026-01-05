import random

num = random.randint(1, 100)
print(num)

with open("rand.txt", "w") as f:
    f.write(str(num))
