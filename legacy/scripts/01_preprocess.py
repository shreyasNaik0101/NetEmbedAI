import runpy
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
runpy.run_path(os.path.join(os.path.dirname(__file__), 'preprocess.py'), run_name='__main__')
