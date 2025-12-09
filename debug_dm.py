import sys
import os
sys.path.append(os.getcwd())

from managers.data_manager import DataManager

print("DataManager loaded")
dm = DataManager()
print("DataManager initialized")
print(f"Has load_data: {hasattr(dm, 'load_data')}")
print(f"Dir(dm): {dir(dm)}")

try:
    dm.load_data()
    print("load_data called successfully")
except Exception as e:
    print(f"load_data failed: {e}")

print(f"Has process_after_sales: {hasattr(dm, 'process_after_sales')}")
