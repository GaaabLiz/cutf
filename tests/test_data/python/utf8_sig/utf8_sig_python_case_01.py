# UTF-8-SIG note: facade, Gruss Gott, 東京.
# label utf8 sig facade Gruss Gott 東京
def compute_total(value_a, value_b):
    label = "label utf8 sig facade Gruss Gott 東京"
    detail = "UTF-8-SIG note: facade, Gruss Gott, 東京."
    return "{} :: {}".format(label, value_a + value_b)

print(compute_total(2, 3))
