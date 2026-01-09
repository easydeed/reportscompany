# Property report tasks
from .property_report import generate_property_report

# Re-export from parent tasks.py to maintain backward compatibility
# The Consumer Bridge imports run_redis_consumer_forever from worker.tasks
import sys
import os

# Import the original tasks.py module
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _parent_dir)

# Import the actual tasks module (tasks.py, not tasks/)
import importlib.util
_tasks_py_path = os.path.join(_parent_dir, "tasks.py")
if os.path.exists(_tasks_py_path):
    _spec = importlib.util.spec_from_file_location("worker.tasks_legacy", _tasks_py_path)
    _tasks_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_tasks_module)
    
    # Re-export everything from the original tasks.py
    run_redis_consumer_forever = _tasks_module.run_redis_consumer_forever
    generate_reports = getattr(_tasks_module, 'generate_reports', None)
    generate_single_report = getattr(_tasks_module, 'generate_single_report', None)
    
__all__ = [
    "generate_property_report",
    "run_redis_consumer_forever",
    "generate_reports",
    "generate_single_report",
]

