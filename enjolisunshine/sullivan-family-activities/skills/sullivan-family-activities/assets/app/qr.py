"""Tiny QR-code generator (byte mode, error correction level M, versions 1-10).

Self-contained so the app never needs an internet connection to show the
"scan with your phone" code. Follows the QR Code Model 2 specification.
"""

# Error correction level M: codewords per version 1..10
_RAW_CODEWORDS = [26, 44, 70, 100, 134, 172, 196, 242, 292, 346]
_ECC_PER_BLOCK = [10, 16, 26, 18, 24, 16, 18, 22, 22, 26]
_NUM_BLOCKS = [1, 1, 1, 2, 2, 4, 4, 4, 5, 5]
_ALIGN = [[], [6, 18], [6, 22], [6, 26], [6, 30], [6, 34],
          [6, 22, 38], [6, 24, 42], [6, 26, 46], [6, 28, 50]]
_ECL_M_FORMAT_BITS = 0


def _gf_mul(x: int, y: int) -> int:
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree: int) -> list[int]:
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(len(result)):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < len(result):
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 0x02)
    return result


def _rs_remainder(data: list[int], divisor: list[int]) -> list[int]:
    result = [0] * len(divisor)
    for b in data:
        factor = b ^ result.pop(0)
        result.append(0)
        for i, coef in enumerate(divisor):
            result[i] ^= _gf_mul(coef, factor)
    return result


def _data_capacity(version: int) -> int:
    return _RAW_CODEWORDS[version - 1] - _NUM_BLOCKS[version - 1] * _ECC_PER_BLOCK[version - 1]


def _encode_data(text: str) -> tuple[int, list[int]]:
    data = text.encode("utf-8")
    for version in range(1, 11):
        count_bits = 8 if version <= 9 else 16
        cap_bits = _data_capacity(version) * 8
        if 4 + count_bits + len(data) * 8 <= cap_bits:
            break
    else:
        raise ValueError("Text is too long for this QR generator")
    bits: list[int] = []
    add = lambda val, n: bits.extend((val >> i) & 1 for i in reversed(range(n)))
    add(0b0100, 4)
    add(len(data), count_bits)
    for b in data:
        add(b, 8)
    add(0, min(4, cap_bits - len(bits)))
    add(0, (-len(bits)) % 8)
    pad = 0xEC
    while len(bits) < cap_bits:
        add(pad, 8)
        pad ^= 0xEC ^ 0x11
    codewords = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    return version, codewords


def _add_ecc_and_interleave(version: int, data: list[int]) -> list[int]:
    num_blocks = _NUM_BLOCKS[version - 1]
    ecc_len = _ECC_PER_BLOCK[version - 1]
    raw = _RAW_CODEWORDS[version - 1]
    num_short = num_blocks - raw % num_blocks
    short_len = raw // num_blocks
    divisor = _rs_divisor(ecc_len)
    blocks, k = [], 0
    for i in range(num_blocks):
        dat = data[k:k + short_len - ecc_len + (0 if i < num_short else 1)]
        k += len(dat)
        ecc = _rs_remainder(dat, divisor)
        if i < num_short:
            dat = dat + [0]
        blocks.append(dat + ecc)
    result = []
    for i in range(len(blocks[0])):
        for j, blk in enumerate(blocks):
            if i != short_len - ecc_len or j >= num_short:
                result.append(blk[i])
    return result


class _Matrix:
    def __init__(self, version: int):
        self.version = version
        self.size = version * 4 + 17
        self.mod = [[False] * self.size for _ in range(self.size)]
        self.fn = [[False] * self.size for _ in range(self.size)]

    def set_fn(self, x: int, y: int, dark: bool) -> None:
        self.mod[y][x] = dark
        self.fn[y][x] = True

    def draw_function_patterns(self) -> None:
        n = self.size
        for i in range(n):
            self.set_fn(6, i, i % 2 == 0)
            self.set_fn(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < n and 0 <= y < n:
                        self.set_fn(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        pos = _ALIGN[self.version - 1]
        last = len(pos) - 1
        for i, ax in enumerate(pos):
            for j, ay in enumerate(pos):
                if (i, j) in ((0, 0), (0, last), (last, 0)):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self.set_fn(ax + dx, ay + dy, max(abs(dx), abs(dy)) != 1)
        self.draw_format_bits(0)
        if self.version >= 7:
            rem = self.version
            for _ in range(12):
                rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
            bits = self.version << 12 | rem
            for i in range(18):
                bit = (bits >> i) & 1 == 1
                a, b = n - 11 + i % 3, i // 3
                self.set_fn(a, b, bit)
                self.set_fn(b, a, bit)

    def draw_format_bits(self, mask: int) -> None:
        n = self.size
        data = _ECL_M_FORMAT_BITS << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        bit = lambda i: (bits >> i) & 1 == 1
        for i in range(6):
            self.set_fn(8, i, bit(i))
        self.set_fn(8, 7, bit(6))
        self.set_fn(8, 8, bit(7))
        self.set_fn(7, 8, bit(8))
        for i in range(9, 15):
            self.set_fn(14 - i, 8, bit(i))
        for i in range(8):
            self.set_fn(n - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.set_fn(8, n - 15 + i, bit(i))
        self.set_fn(8, n - 8, True)  # the always-dark module

    def draw_codewords(self, data: list[int]) -> None:
        n, i = self.size, 0
        right = n - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(n):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = n - 1 - vert if upward else vert
                    if not self.fn[y][x] and i < len(data) * 8:
                        self.mod[y][x] = (data[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            right -= 2

    def apply_mask(self, mask: int) -> None:
        test = [
            lambda x, y: (x + y) % 2 == 0,
            lambda x, y: y % 2 == 0,
            lambda x, y: x % 3 == 0,
            lambda x, y: (x + y) % 3 == 0,
            lambda x, y: (x // 3 + y // 2) % 2 == 0,
            lambda x, y: x * y % 2 + x * y % 3 == 0,
            lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
            lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
        ][mask]
        for y in range(self.size):
            for x in range(self.size):
                if not self.fn[y][x] and test(x, y):
                    self.mod[y][x] = not self.mod[y][x]

    def penalty(self) -> int:
        n, m, score = self.size, self.mod, 0
        lines = [row for row in m] + [[m[y][x] for y in range(n)] for x in range(n)]
        finder_a = [True, False, True, True, True, False, True, False, False, False, False]
        finder_b = finder_a[::-1]
        for line in lines:
            run, prev = 0, None
            for v in line:
                if v == prev:
                    run += 1
                else:
                    if run >= 5:
                        score += 3 + run - 5
                    run, prev = 1, v
            if run >= 5:
                score += 3 + run - 5
            for i in range(len(line) - 10):
                seg = line[i:i + 11]
                if seg == finder_a or seg == finder_b:
                    score += 40
        for y in range(n - 1):
            for x in range(n - 1):
                c = m[y][x]
                if c == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                    score += 3
        dark = sum(sum(row) for row in m)
        total = n * n
        k = (abs(dark * 20 - total * 10) + total - 1) // total - 1
        return score + max(k, 0) * 10


def qr_matrix(text: str) -> list[list[bool]]:
    """Return the QR code for `text` as rows of booleans (True = dark)."""
    version, data = _encode_data(text)
    codewords = _add_ecc_and_interleave(version, data)
    best = None
    for mask in range(8):
        q = _Matrix(version)
        q.draw_function_patterns()
        q.draw_codewords(codewords)
        q.apply_mask(mask)
        q.draw_format_bits(mask)
        p = q.penalty()
        if best is None or p < best[0]:
            best = (p, q)
    return best[1].mod


def qr_svg(text: str, dark: str = "#1F2547", light: str = "#FFFFFF", border: int = 4) -> str:
    m = qr_matrix(text)
    n = len(m) + border * 2
    path = "".join(f"M{x + border},{y + border}h1v1h-1z"
                   for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
            f'<rect width="{n}" height="{n}" fill="{light}"/><path d="{path}" fill="{dark}"/></svg>')
