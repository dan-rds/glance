s = "ejwjhekwfjkwj wjhbew       ehhe 1233"
import re
s = "Example        String".strip()
while '  ' in s:
    s = s.replace('  ', ' ')
print (s)
#print(s)
#print(s.replace("\w+", ''))