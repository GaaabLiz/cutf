// Windows-1252 note: citta, perche, gia, euro € e “virgolette”.
using System;

public class Program {
    public static void Main() {
        const string label = "label cp1252 citta € “quote”";
        Console.WriteLine(label);
        Console.WriteLine("Windows-1252 note: citta, perche, gia, euro € e “virgolette”.");
    }
}
