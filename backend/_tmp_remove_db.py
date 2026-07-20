import os
import shutil
path = r"D:\talentup-fichaje\backend\talentup_fichaje.db"
print("exists", os.path.exists(path))
if os.path.exists(path):
    shutil.move(path, path + ".old")
    print("moved")
