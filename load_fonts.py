
import os
import fnmatch
from PIL import ImageFont
path = 'static/'

files = os.listdir(path)
pattern = "*.ttf"
fonts = {}
for font in files:
    if fnmatch.fnmatch(font, pattern):
        fonts[font[:-4] + "-" + str(10) + ""] = ImageFont.truetype("" + path + font + "", 10)

print(fonts)