# ISO-8859-1 note: citta, perche, gia, deja, AEOU.
# label iso citta perche gia deja
def compute_total(value_a, value_b):
    label = "label iso citta perche gia deja"
    detail = "ISO-8859-1 note: citta, perche, gia, deja, AEOU."
    return "{} :: {}".format(label, value_a + value_b)

print(compute_total(2, 3))
