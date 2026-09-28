import AppKit

let text = "എങ്ങനെ കടന്നുപോകുന്നു?"
let font = NSFont(name: "Malayalam Sangam MN", size: 64) ?? NSFont.systemFont(ofSize: 64)
let str = NSAttributedString(string: text, attributes: [.font: font])
print("Glyph count for text:", str.string.count, "Size:", str.size())
