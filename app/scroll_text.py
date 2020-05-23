class ScrollText:
    def __init__(self, _i2c):
        self.i2c = _i2c
        self.offset = self.i2c.height / 2 - 4
        self.velocity = -8
        self.start_position = self.i2c.width
        self._text = "Text"
        self._font = "Arial-10"
        self.pos = self.start_position
        self.max_width = 0
        self.y_pos = 0
        self._x = 0
        self._text_width = 0
        self._text_height = 0
        self.allow = False
        self._prepared = False

    def set_send(self):
        pass

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, _txt):
        self._text = _txt

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, fnt):
        self._font = fnt

    def prepare(self):
        max, unused = self.i2c.draw.textsize(self._text, self.i2c.fonts[self._font])
        self._text_width, self._text_height = self.i2c.fonts[self._font].getsize(self._text)
        self.max_width = max
        # Enumerate characters and draw them offset vertically based on a sine wave.
        self._x = self.pos
        self.pos = self.start_position
        self._prepared = True

    def run(self):
        if not self._prepared:
            self.prepare()
        if self._prepared and self.allow:
            self.set_send()
            # Clear image buffer by drawing a black filled box.
            self.i2c.draw.rectangle((0, self.y_pos, self.i2c.width, self.y_pos + self._text_height), outline=0, fill=0)
            self._x = self.pos
            for idx, character in enumerate(self._text):
                # Stop drawing if off the right side of screen.
                if self._x > self.i2c.width:
                    break
                # Calculate width but skip drawing if off the left side of screen.
                if self._x < -10:
                    char_width, char_height = self.i2c.draw.textsize(character, font=self.i2c.fonts[self._font])
                    self._x += char_width
                    continue
                # Draw text.
                self.i2c.draw.text((self._x, self.y_pos), character, font=self.i2c.fonts[self._font], fill=255)
                # Increment x position based on character width.
                char_width, char_height = self.i2c.draw.textsize(character, font=self.i2c.fonts[self._font])
                self._x += char_width
            # Move position for next frame.
            self.pos += self.velocity
            # Start over if text has scrolled completely off left side of screen.
            if self.pos < -self.max_width:
                self.pos = self.start_position
