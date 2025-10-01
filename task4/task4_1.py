import random
import string
from itertools import cycle


def get_words(text, n, n_word, acts):
    words = []
    sp = sorted(random.sample(range(1, n), n_word - 1))
    # words = [text[a:b] for a, b in zip([0] + sp, sp + [len(text)])]
    start = 0
    for pos in sp:
        words.append(text[start:pos])
        start = pos
    words.append(text[start:]) 
    func_cycle = cycle(acts)
    return [fn(x) for x, fn in zip(words, func_cycle)]


n = 1000
n_word = 10
actions = ("upper", "reverse", "double", "del_digits", "del_even", "replace")
text = "".join([random.choice(string.ascii_letters + string.digits) for i in range(n)])
acts = (
    lambda w: w.upper(),
    lambda w: w[::-1],
    lambda w: w + w,
    lambda w: "".join(filter(lambda c: not c.isdigit(), w)),
    lambda w: "".join(c for i, c in enumerate(w) if i % 2 == 0),
    lambda w: "".join("Python" if c.isdigit() else c for c in w),
)

print(text)

print(get_words(text, n, n_word, acts))
