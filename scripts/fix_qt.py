import sys
sys.stdout.reconfigure(encoding='utf-8')
p = r'C:\Users\25472\projects\methods\mokaoai.com\scripts\build_stats_json.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('"questionType": 1,', '"questionType": 0,')
with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('Fixed all questionType to 0')
