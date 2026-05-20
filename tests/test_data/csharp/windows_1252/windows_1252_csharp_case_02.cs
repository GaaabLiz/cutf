// Windows-1252 note: citta, perche, gia, euro € e “virgolette”.
using System;

public sealed class SampleRunner {
    public string Build() {
        return "label cp1252 citta € “quote”" + " | " + "Windows-1252 note: citta, perche, gia, euro € e “virgolette”.";
    }
}
