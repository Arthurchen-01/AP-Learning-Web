import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa'

# 2020Intl - Q4 detection
print('=== 2020Intl Q4 ===')
with open(f'{base}\\2020Intl_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()
frq_start = 34342
frq = text[frq_start:]
# Find all matches of the current pattern
for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s*(?:This question|The |A |In this|Consider|A high|At a|The method|Many |Users)', frq):
    print(f'  Q{m.group(1)} at {m.start()}: {repr(frq[m.start():m.start()+80])}')

# Try broader pattern
print('\nBroader pattern:')
for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s+[A-Z]', frq):
    print(f'  Q{m.group(1)} at {m.start()}: {repr(frq[m.start():m.start()+80])}')

# Check exact text around 16702-34342=12360
print(f'\nText around pos 12360 in FRQ:')
print(repr(frq[12340:12400]))
