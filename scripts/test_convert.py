import sys
sys.path.insert(0, r'C:\Users\25472\projects\methods\mokaoai.com\scripts')
from batch_convert_pdfs import *

result = process_pdf('calculus-bc', '2008Intl', '微积分BC', '2008', '国际卷')
if result:
    for sec in result['sections']:
        if sec['id'] == 'section-mcq':
            print(f"MCQ Section: {len(sec['questions'])} questions")
            for q in sec['questions'][:3]:
                print(f"  Q{q['id']}: prompt={q['prompt'][:100]}...")
                print(f"    Options: {[(o['key'], o['text'][:30]) for o in q['options']]}")
                print(f"    Answer: {q['answer']}")
                print()
        elif sec['id'] == 'section-frq':
            print(f"FRQ Section: {len(sec['questions'])} questions")
            for q in sec['questions'][:2]:
                print(f"  {q['id']}: prompt={q['prompt'][:150]}...")
                print()
