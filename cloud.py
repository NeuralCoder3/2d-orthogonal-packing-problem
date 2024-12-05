# code to pack squares based on discourse statistics (square packing code at bottom)

import os
import json
import re
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

url = "https://vorkurs-discourse.cs.uni-saarland.de/uploads"

files = ["1.json", "19.json", "39.json", "59.json", "79.json", "89.json", "99.json", "102.json", "103.json","110.json","118.json"]
meme_folder = "memes3"

all_posts = []

image_regex = re.compile(r'src="('+url+r'/[^"]+\.(png|jpg|jpeg|gif|webp))"')

cut_off2 = None


prefix="all_top4_"
cut_off = "2024-09-01"
W = 110
H = 110

color_map = {
}

seen_images = set()
for file in files:
    with open(file, "r") as f:
        data = json.load(f)
    posts = data["post_stream"]["posts"]
    for post in posts:
        if "count" in post["actions_summary"][0]:
            likes = post["actions_summary"][0]["count"]
        else:
            likes = 0
        content = post["cooked"]
        # get first image (href ending in png/jpg/jpeg/gif/webp)
        m = image_regex.search(content)
        if m:
            image = m.group(1)
        else:
            image = None
        if image is None:
            continue
        
        created_at = post["created_at"]
        
        # only newer posts
        if created_at < cut_off:
            continue
        if cut_off2 is not None and created_at > cut_off2:
            continue
        if likes == 0:
            continue
        
        img_path = os.path.join(meme_folder, image.split("/")[-1])
        if img_path in seen_images:
            continue
        seen_images.add(img_path)
        img = PIL.Image.open(img_path)
        img = img.convert("RGB")
        for name, color in color_map.items():
            if name in post["name"]:
                img = PIL.Image.blend(img, PIL.Image.new("RGB", img.size, color), 0.5)
        w, h = img.size
        
        all_posts.append((post["id"], likes, img, created_at, (w,h)))
        

        
# all_posts = sorted(set(all_posts))
# unique by id (set is not hashable)
all_posts2 = sorted(set([x[0] for x in all_posts]))
all_posts = [[x for x in all_posts if x[0] == id][0] for id in all_posts2]

print(f"Found {len(all_posts)} posts")

sizes = []
for id, likes, img_path, created, (w,h) in all_posts:
    max_dim = max(w,h)
    ew = likes * w / max_dim
    eh = likes * h / max_dim
    ew = int(round(ew))
    eh = int(round(eh))
    sizes.append((ew, eh))

minizinc_path = f"minizinc_{prefix}{W}_{H}.dzn"

with open(minizinc_path, "w") as f:
    f.write(f"count = {len(all_posts)};\n")
    f.write(f"W = {W};\n")
    f.write(f"H = {H};\n")
    f.write("w = [")
    for w,h in sizes:
        f.write(f"{w}, ")
    f.write("];\n")
    f.write("h = [")
    for w,h in sizes:
        f.write(f"{h}, ")
    f.write("];\n")
    
print(f"Saved {minizinc_path}")
    

from itertools import product
# from mip import Model, xsum, BINARY
from z3 import *

# each post is a square of size like_count
# we want to arrange them in a square grid

s = Solver()

x = [Int(f"x_{i}") for i in range(len(all_posts))]
y = [Int(f"y_{i}") for i in range(len(all_posts))]

for i in range(len(all_posts)):
    s.add(x[i] >= 0)
    s.add(y[i] >= 0)

# no overlap between posts
for i, j in product(range(len(all_posts)), range(len(all_posts))):
    if i == j:
        continue
    # like_i = all_posts[i][1]
    # like_j = all_posts[j][1]
    wi, hi = sizes[i]
    wj, hj = sizes[j]
    s.add(
        Or(x[i] + wi <= x[j],
        y[i] + hi <= y[j],
        x[j] + wj <= x[i],
        y[j] + hj <= y[i])
    )
    
for i in range(len(all_posts)):
    w, h = sizes[i]
    s.add(x[i] + w <= W)
    s.add(y[i] + h <= H)
    
# s.check()
# print("Step 1 done")
# WH = 120
# for i in range(len(all_posts)):
#     s.add(x[i] + all_posts[i][1] <= WH)
#     s.add(y[i] + all_posts[i][1] <= WH)
    
# save s_expressions
# with open(f"{prefix}layout_{W}_{H}.smt2", "w") as f:
#     f.write(s.sexpr())
#     f.write("\n(check-sat)\n(get-model)\n")
    
if s.check() == sat:
    m = s.model()
    
    # scale = 100
    scale = 20
    
    img = PIL.Image.new("RGB", (W*scale, H*scale), "white")
    
    print(f"Saving {prefix}layout_{W}_{H}.png")
    print(W*scale, H*scale)
    
    draw = PIL.ImageDraw.Draw(img)
    for i, (id, likes, img_file, created, _) in enumerate(all_posts):
        if not image:
            continue
        x_coord = m[x[i]].as_long()
        y_coord = m[y[i]].as_long()
        
        w,h = sizes[i]
        img_file = img_file.resize((int(w*scale), int(h*scale)))
        img.paste(img_file, (x_coord*scale, y_coord*scale))
        
        draw.rectangle([x_coord*scale, y_coord*scale, (x_coord+w)*scale, (y_coord+h)*scale], outline="black")
        
    img.save(f"{prefix}layout_{W}_{H}.png")
else:
    print("No solution found")