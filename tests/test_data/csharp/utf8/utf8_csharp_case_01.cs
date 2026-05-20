// UTF-8 note: cafe, manana, Привет, 你好.
using System;

public class Program {
    public static void Main() {
        const string label = "label utf8 cafe manana Привет 你好";
        Console.WriteLine(label);
        Console.WriteLine("UTF-8 note: cafe, manana, Привет, 你好.");
    }
}
