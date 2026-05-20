# UTF-8 note: cafe, manana, Привет, 你好.
# label utf8 cafe manana Привет 你好
class SampleRunner:
    def build(self):
        return "label utf8 cafe manana Привет 你好" + " / " + "UTF-8 note: cafe, manana, Привет, 你好."

print(SampleRunner().build())
