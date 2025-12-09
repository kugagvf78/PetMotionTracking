import os
import shutil
import random

BASE = "datasets/pets/train"

img_dir = os.path.join(BASE, "images")
lbl_dir = os.path.join(BASE, "labels")

valid_img = "datasets/pets/valid/images"
valid_lbl = "datasets/pets/valid/labels"

os.makedirs(valid_img, exist_ok=True)
os.makedirs(valid_lbl, exist_ok=True)

files = os.listdir(img_dir)
random.shuffle(files)

valid_size = max(1, int(len(files) * 0.2))  # 20% valid

valid_files = files[:valid_size]

for f in valid_files:
    img_src = os.path.join(img_dir, f)
    lbl_src = os.path.join(lbl_dir, f.replace(".jpg", ".txt").replace(".png", ".txt"))

    shutil.move(img_src, valid_img)
    if os.path.exists(lbl_src):
        shutil.move(lbl_src, valid_lbl)

print("DONE: Đã tạo valid/images và valid/labels")
