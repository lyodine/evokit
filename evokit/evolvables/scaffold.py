la = list(range(10))

pos = 9

mylar = 2

collected = []
for _ in range(min([len(la) - pos, mylar])):
    collected.append(la[pos])
    pos = pos + 1

print(collected)

