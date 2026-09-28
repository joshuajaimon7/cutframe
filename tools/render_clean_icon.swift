import Foundation
import Cocoa
import CoreGraphics

let size: CGFloat = 1024
let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: Int(size),
    pixelsHigh: Int(size),
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
)!
rep.size = NSSize(width: size, height: size)

let context = NSGraphicsContext(bitmapImageRep: rep)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
let cg = context.cgContext

// 1. Transparent canvas
cg.clear(CGRect(x: 0, y: 0, width: size, height: size))

// 2. Standard macOS App Icon Squircle Geometry
let pad: CGFloat = 90
let squircleRect = CGRect(x: pad, y: pad, width: size - 2 * pad, height: size - 2 * pad)
let squircleRadius: CGFloat = 195

// Ambient macOS Icon Shadow
cg.saveGState()
cg.setShadow(offset: CGSize(width: 0, height: -14), blur: 28, color: NSColor(calibratedWhite: 0, alpha: 0.18).cgColor)

// Pure White Squircle
let squirclePath = NSBezierPath(roundedRect: squircleRect, xRadius: squircleRadius, yRadius: squircleRadius)
NSColor(calibratedRed: 0.98, green: 0.98, blue: 0.99, alpha: 1.0).setFill()
squirclePath.fill()
cg.restoreGState()

// Subtle 1px inner border
let innerBorder = NSBezierPath(roundedRect: squircleRect.insetBy(dx: 1, dy: 1), xRadius: squircleRadius - 1, yRadius: squircleRadius - 1)
innerBorder.lineWidth = 1.5
NSColor(calibratedWhite: 0.88, alpha: 1.0).setStroke()
innerBorder.stroke()

// 3. Creative Minimalist Graphic: The Vertical Crop
// Horizontal 16:9 Frame (Subtle Slate Line)
let hW: CGFloat = 520
let hH: CGFloat = 292
let hRect = CGRect(x: (size - hW) / 2, y: (size - hH) / 2, width: hW, height: hH)
let hPath = NSBezierPath(roundedRect: hRect, xRadius: 28, yRadius: 28)
hPath.lineWidth = 8
NSColor(calibratedRed: 0.82, green: 0.84, blue: 0.88, alpha: 1.0).setStroke()
hPath.stroke()

// Vertical 9:16 Frame (Bold Matte Black Core) - The Short cut out of the video!
let vW: CGFloat = 260
let vH: CGFloat = 462
let vRect = CGRect(x: (size - vW) / 2, y: (size - vH) / 2, width: vW, height: vH)

// Soft Shadow on the Vertical Short
cg.saveGState()
cg.setShadow(offset: CGSize(width: 0, height: -6), blur: 18, color: NSColor(calibratedWhite: 0, alpha: 0.22).cgColor)

let vPath = NSBezierPath(roundedRect: vRect, xRadius: 36, yRadius: 36)
NSColor(calibratedRed: 0.08, green: 0.09, blue: 0.12, alpha: 1.0).setFill()
vPath.fill()
cg.restoreGState()

// Center Precision Play Notch in Vertical Card
let playPath = NSBezierPath()
let pSize: CGFloat = 44
let pX: CGFloat = (size - pSize * 0.7) / 2 + 3
let pY: CGFloat = (size - pSize) / 2

playPath.move(to: CGPoint(x: pX, y: pY + pSize))
playPath.line(to: CGPoint(x: pX + pSize * 0.86, y: pY + pSize / 2))
playPath.line(to: CGPoint(x: pX, y: pY))
playPath.close()

NSColor(calibratedRed: 0.95, green: 0.95, blue: 0.98, alpha: 1.0).setFill()
playPath.fill()

NSGraphicsContext.restoreGraphicsState()

if let pngData = rep.representation(using: .png, properties: [:]) {
    try? pngData.write(to: URL(fileURLWithPath: "assets/icons/icon.png"))
    print("Rendered transparent white vector icon.png successfully!")
}
