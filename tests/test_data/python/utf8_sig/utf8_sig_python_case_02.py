# UTF-8-SIG note: facade, Gruss Gott, 東京.
# label utf8 sig facade Gruss Gott 東京
class SampleRunner:
    def build(self):
        return "label utf8 sig facade Gruss Gott 東京" + " / " + "UTF-8-SIG note: facade, Gruss Gott, 東京."

print(SampleRunner().build())
