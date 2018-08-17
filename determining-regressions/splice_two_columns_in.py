orig = open('everything.csv')
fix = open('static_fix_everything.csv')

# skip headers
print(next(orig))
next(fix)
f_dict = {}
for line in fix:
    cols = line.split(',')
    key = (cols[0], cols[1], cols[2])
    f_dict[key] = line

for line in orig:
    cols = line.split(',')
    key = (cols[0], cols[1], cols[2])
    if key in f_dict:
        i7 = f_dict[key].split(',')[9]
        i8 = f_dict[key].split(',')[10]
        cols[9] = i7
        cols[10] = i8
        new_line = ','.join(cols)
        print(new_line, end='')
    else:
        print(line, end='')
