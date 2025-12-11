import os
import sys

# Mocking the class and method to test logic
class MockPopup:
    def open_file(self, path):
        print(f"Original path: {path}")
        if path:
            path = os.path.normpath(path)
        print(f"Normalized path: {path}")
        return path

# Test cases
popup = MockPopup()
test_paths = [
    "C:/Users/sue/Documents/file.txt",
    "C:\\Users\\sue\\Documents\\file.txt",
    "C:/Users/sue\\Documents/file.txt", # Mixed slashes
    "//server/share/folder/file.txt"
]

print("--- Testing Path Normalization ---")
for p in test_paths:
    norm_p = popup.open_file(p)
    expected = os.path.normpath(p)
    if norm_p == expected:
        print("PASS")
    else:
        print(f"FAIL: Expected {expected}, got {norm_p}")
