import Foundation
import Cocoa
import CoreGraphics
import CoreText

let width: CGFloat = 1080
let height: CGFloat = 1920

func renderHeaderCallout(tag: String, title: String, outputPath: String) {
    let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: Int(width),
        pixelsHigh: Int(height),
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    )!
    rep.size = NSSize(width: width, height: height)

    let context = NSGraphicsContext(bitmapImageRep: rep)!
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = context
    let cg = context.cgContext

    cg.clear(CGRect(x: 0, y: 0, width: width, height: height))

    // Position: Top margin (above speaker's head, ~160px from top)
    // In Cocoa: y = 1920 - 160 - 110 = 1650
    let cardW: CGFloat = 640
    let cardH: CGFloat = 90
    let cardX: CGFloat = (width - cardW) / 2
    let cardY: CGFloat = 1660

    let cardRect = CGRect(x: cardX, y: cardY, width: cardW, height: cardH)

    // Shadow
    cg.saveGState()
    cg.setShadow(offset: CGSize(width: 0, height: -8), blur: 24, color: NSColor.black.withAlphaComponent(0.6).cgColor)

    // Frosted dark pill
    let bgPath = NSBezierPath(roundedRect: cardRect, xRadius: 45, yRadius: 45)
    NSColor(calibratedRed: 0.06, green: 0.06, blue: 0.08, alpha: 0.94).setFill()
    bgPath.fill()
    cg.restoreGState()

    // Gold border
    let borderPath = NSBezierPath(roundedRect: cardRect.insetBy(dx: 1.5, dy: 1.5), xRadius: 43.5, yRadius: 43.5)
    borderPath.lineWidth = 2.0
    NSColor(calibratedRed: 0.88, green: 0.74, blue: 0.38, alpha: 0.8).setStroke()
    borderPath.stroke()

    // Tag badge inside (e.g. "💰 DEAL")
    let badgeW: CGFloat = 110
    let badgeH: CGFloat = 50
    let badgeRect = CGRect(x: cardX + 20, y: cardY + (cardH - badgeH) / 2, width: badgeW, height: badgeH)
    let badgePath = NSBezierPath(roundedRect: badgeRect, xRadius: 25, yRadius: 25)
    NSColor(calibratedRed: 0.88, green: 0.74, blue: 0.38, alpha: 0.22).setFill()
    badgePath.fill()

    let badgeAttrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.boldSystemFont(ofSize: 18),
        .foregroundColor: NSColor(calibratedRed: 0.98, green: 0.85, blue: 0.48, alpha: 1.0)
    ]
    let badgeStr = NSAttributedString(string: tag, attributes: badgeAttrs)
    let badgeSize = badgeStr.size()
    badgeStr.draw(at: CGPoint(x: badgeRect.origin.x + (badgeW - badgeSize.width) / 2, y: badgeRect.origin.y + (badgeH - badgeSize.height) / 2))

    // Title (e.g. "$100M RECORD OFFER")
    let titleAttrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: 26, weight: .bold),
        .foregroundColor: NSColor.white
    ]
    let titleStr = NSAttributedString(string: title, attributes: titleAttrs)
    let titleSize = titleStr.size()
    titleStr.draw(at: CGPoint(x: cardX + 148, y: cardY + (cardH - titleSize.height) / 2))

    NSGraphicsContext.restoreGraphicsState()

    if let pngData = rep.representation(using: .png, properties: [:]) {
        try? pngData.write(to: URL(fileURLWithPath: outputPath))
    }
}

renderHeaderCallout(tag: "💰 DEAL", title: "$100M RECORD OFFER", outputPath: "/tmp/header_callout.png")
print("Rendered header callout successfully!")
