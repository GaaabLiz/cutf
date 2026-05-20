# Windows-1252 note: citta, perche, gia, euro € e “virgolette”.
# label cp1252 citta € “quote”
def compute_total(value_a, value_b):
    label = "label cp1252 citta € “quote”"
    detail = "Windows-1252 note: citta, perche, gia, euro € e “virgolette”."
    return "{} :: {}".format(label, value_a + value_b)

print(compute_total(2, 3))
