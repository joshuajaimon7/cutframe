import AppKit
import Foundation

struct WordData: Codable {
    let word: String
    let start: Double
    let end: Double
}

struct CardData: Codable {
    let cardIdx: Int
    let words: [WordData]
    let activeIdx: Int
    let outPath: String
    let style: String?
}

// Read arguments
guard CommandLine.arguments.count >= 2 else {
    print("Usage: card_renderer <cards.json>")
    exit(1)
}

let jsonPath = CommandLine.arguments[1]
let data = try Data(contentsOf: URL(fileURLWithPath: jsonPath))
let decoder = JSONDecoder()
let cards = try decoder.decode([CardData].self, from: data)

let width: CGFloat = 1080
let height: CGFloat = 1920
let baseFontSize: CGFloat = 58
let targetY: CGFloat = 450 // Bottom-up Cocoa coordinate: 450 is lower third (chest area)

class CardView: NSView {
    override var isFlipped: Bool { true }
    
    var card: CardData!
    var style: String = "luxury_doc"
    
    override func draw(_ dirtyRect: NSRect) {
        let fullText = card.words.map { $0.word }.joined(separator: " ")
        var fontName = "MalayalamSangamMN-Bold"
        let containsMalayalam = fullText.unicodeScalars.contains { $0.value >= 0x0D00 && $0.value <= 0x0D7F }
        let containsHindi = fullText.unicodeScalars.contains { $0.value >= 0x0900 && $0.value <= 0x097F }
        let containsTamil = fullText.unicodeScalars.contains { $0.value >= 0x0B80 && $0.value <= 0x0BFF }
        
        if containsMalayalam {
            fontName = "MalayalamSangamMN-Bold"
        } else if containsHindi {
            fontName = "DevanagariSangamMN-Bold"
        } else if containsTamil {
            fontName = "TamilSangamMN-Bold"
        } else {
            fontName = (style == "luxury_doc") ? "HelveticaNeue-Bold" : "Impact"
        }

        let font = NSFont(name: fontName, size: baseFontSize) ?? NSFont.systemFont(ofSize: baseFontSize, weight: .black)

        var activeColor = NSColor(calibratedRed: 1.0, green: 0.88, blue: 0.28, alpha: 1.0) // Radiant Gold
        var inactiveColor = NSColor.white
        var pillBgColor = NSColor(calibratedWhite: 0.04, alpha: 0.88)
        var pillBorderColor = NSColor(calibratedRed: 0.88, green: 0.75, blue: 0.38, alpha: 0.88) // Luxury Gold border
        var pillBorderWidth: CGFloat = 2.5
        let strokeColor = NSColor.black
        let strokeWidth: CGFloat = -2.5

        if style == "kinetic_punch" {
            activeColor = NSColor(calibratedRed: 1.0, green: 0.95, blue: 0.0, alpha: 1.0)
            inactiveColor = NSColor.white
            pillBgColor = NSColor(calibratedWhite: 0.0, alpha: 0.92)
            pillBorderColor = NSColor(calibratedWhite: 1.0, alpha: 0.3)
            pillBorderWidth = 1.5
        } else if style == "minimal_story" {
            activeColor = NSColor.white
            inactiveColor = NSColor(calibratedWhite: 0.72, alpha: 1.0)
            pillBgColor = NSColor(calibratedWhite: 0.1, alpha: 0.75)
            pillBorderColor = NSColor(calibratedWhite: 1.0, alpha: 0.2)
            pillBorderWidth = 1.0
        } else if style == "hyper_neon" {
            activeColor = NSColor(calibratedRed: 0.0, green: 1.0, blue: 0.88, alpha: 1.0)
            inactiveColor = NSColor.white
            pillBgColor = NSColor(calibratedRed: 0.04, green: 0.05, blue: 0.12, alpha: 0.92)
            pillBorderColor = NSColor(calibratedRed: 0.0, green: 0.88, blue: 1.0, alpha: 0.95)
            pillBorderWidth = 2.8
        }

        var totalWidth: CGFloat = 0
        let spaceWidth: CGFloat = 18
        var wordAttributed: [(NSAttributedString, CGFloat)] = []
        
        for (idx, w) in card.words.enumerated() {
            let isActive = idx == card.activeIdx
            let textColor = isActive ? activeColor : inactiveColor
            
            let attrs: [NSAttributedString.Key: Any] = [
                .font: font,
                .foregroundColor: textColor,
                .strokeColor: strokeColor,
                .strokeWidth: strokeWidth
            ]
            
            let attrStr = NSAttributedString(string: w.word, attributes: attrs)
            let wWidth = attrStr.size().width
            wordAttributed.append((attrStr, wWidth))
            totalWidth += wWidth
        }
        totalWidth += spaceWidth * CGFloat(card.words.count - 1)

        let xPos: CGFloat = (width - totalWidth) / 2
        let yPos = targetY
        
        // Draw Frosted Pill Box
        let pillRect = NSRect(x: xPos - 38, y: yPos - 16, width: totalWidth + 76, height: 104)
        let pillPath = NSBezierPath(roundedRect: pillRect, xRadius: 30, yRadius: 30)
        pillBgColor.setFill()
        pillPath.fill()
        
        if pillBorderWidth > 0 {
            pillPath.lineWidth = pillBorderWidth
            pillBorderColor.setStroke()
            pillPath.stroke()
        }
        
        // Draw Words
        var currX = xPos
        for (attrStr, wWidth) in wordAttributed {
            attrStr.draw(at: NSPoint(x: currX, y: yPos + 18))
            currX += wWidth + spaceWidth
        }
    }
}

let view = CardView(frame: NSRect(x: 0, y: 0, width: width, height: height))

for card in cards {
    view.card = card
    view.style = card.style ?? "luxury_doc"
    
    guard let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: Int(width),
        pixelsHigh: Int(height),
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .calibratedRGB,
        bytesPerRow: 0,
        bitsPerPixel: 32
    ) else { continue }
    rep.size = NSSize(width: width, height: height)
    
    guard let ctx = NSGraphicsContext(bitmapImageRep: rep) else { continue }
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = ctx
    view.draw(view.bounds)
    NSGraphicsContext.restoreGraphicsState()
    
    if let pngData = rep.representation(using: .png, properties: [:]) {
        try? pngData.write(to: URL(fileURLWithPath: card.outPath))
    }
}

print("Rendered \(cards.count) cards with native CoreText at exact 1080x1920!")
