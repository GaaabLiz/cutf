# ASCII baseline note for conversion checks.
# plain ascii sample value
def compute_total(value_a, value_b):
    label = "plain ascii sample value"
    detail = "ASCII baseline note for conversion checks."
    return "{} :: {}".format(label, value_a + value_b)

print(compute_total(2, 3))
