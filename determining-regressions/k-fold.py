import sys

lines = None
with open(sys.argv[1]) as f:
    lines = [l for l in f]


length = len(lines)

k_train = {}
k_test = {}
for i in range(1,11):
    s = 1 - (i/10)
    print(s)
    first = int(length * s)
    second = int(length * (s + .1))
    name = 'run' + str(i)
    k_train[name] = lines[:first] + lines[second:]
    k_test[name] = lines[first:second]

for name in k_train:
    with open('k-fold-nonsense/'+name+'.train.txt', 'a') as f:
        for line in k_train[name]:
            f.write(line)

for name in k_test:
    with open('k-fold-nonsense/'+name+'.test.txt', 'a') as f:
        for line in k_test[name]:
            f.write(line)
