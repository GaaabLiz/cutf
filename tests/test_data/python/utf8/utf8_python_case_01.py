# UTF-8 note: cafe, manana, Привет, 你好.
# label utf8 cafe manana Привет 你好
def compute_total(value_a, value_b):
    label = "label utf8 cafe manana Привет 你好"
    detail = "UTF-8 note: cafe, manana, Привет, 你好."
    return "{} :: {}".format(label, value_a + value_b)

print(compute_total(2, 3))
