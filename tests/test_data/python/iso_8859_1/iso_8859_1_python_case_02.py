# ISO-8859-1 note: citta, perche, gia, deja, AEOU.
# label iso citta perche gia deja
class SampleRunner:
    def build(self):
        return "label iso citta perche gia deja" + " / " + "ISO-8859-1 note: citta, perche, gia, deja, AEOU."

print(SampleRunner().build())
