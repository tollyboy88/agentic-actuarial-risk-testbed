from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1] / "submission" / "qa" / "word"
out = root / "contact_sheets"
out.mkdir(exist_ok=True)
groups = {}
for f in sorted(root.glob("*.png")):
    stem = f.stem.rsplit("-", 1)[0]
    groups.setdefault(stem, []).append(f)
for stem, files in groups.items():
    for chunk_no in range(0, len(files), 4):
        chunk = files[chunk_no:chunk_no + 4]
        thumbs = []
        for f in chunk:
            im = Image.open(f).convert("RGB")
            im.thumbnail((900, 1200))
            thumbs.append((f, im.copy()))
        canvas = Image.new("RGB", (1840, 2480), "#d0d0d0")
        draw = ImageDraw.Draw(canvas)
        for i, (f, im) in enumerate(thumbs):
            x = 10 + (i % 2) * 915
            y = 25 + (i // 2) * 1225
            canvas.paste(im, (x, y))
            draw.text((x, 5 + (i // 2) * 1225), f.name, fill="black")
        canvas.save(out / f"{stem}_{chunk_no//4 + 1}.jpg", quality=88)
