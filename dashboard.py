import runpy
import sys
import os

target_dashboard = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard", "dashboard.py")
runpy.run_path(target_dashboard, run_name="__main__")
