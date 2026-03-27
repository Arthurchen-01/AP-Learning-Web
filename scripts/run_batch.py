# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import the pipeline
sys.path.insert(0, r'C:\Users\25472\projects\methods\mokaoai.com\scripts')
from exam_pipeline import batch_extract_all

batch_extract_all()
