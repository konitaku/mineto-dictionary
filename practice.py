import re

s = 'aaa@xxx.com, bbb@yyy.com, <p>ccc@あいうがなり都zzz.\net１19212325</p>'

m = re.search(r'<p>\w+', s)
# print(s[26:37])
print(m)
# print(m.span())
x = re.search(r'<p>.+</p>', s, flags=re.DOTALL)
print(x)
print(s[x.span()[0] + 3: x.span()[1] - 4])
