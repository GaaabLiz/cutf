# Windows-1252 note: citta, perche, gia, euro € e “virgolette”.
# label cp1252 citta € “quote”
class SampleRunner:
    def build(self):
        return "label cp1252 citta € “quote”" + " / " + "Windows-1252 note: citta, perche, gia, euro € e “virgolette”."

print(SampleRunner().build())
