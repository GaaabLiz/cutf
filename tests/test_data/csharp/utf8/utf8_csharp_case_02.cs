// UTF-8 note: cafe, manana, Привет, 你好.
using System;

public sealed class SampleRunner {
    public string Build() {
        return "label utf8 cafe manana Привет 你好" + " | " + "UTF-8 note: cafe, manana, Привет, 你好.";
    }
}
