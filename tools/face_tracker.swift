import AVFoundation
import Vision
import AppKit
import Foundation

struct FaceTrackingResult: Codable {
    let time: Double
    let faceCount: Int
    let midX: Double
    let cropX: Int
}

guard CommandLine.arguments.count >= 4 else {
    print("Usage: face_tracker <video_path> <start_time> <duration>")
    exit(1)
}

let videoPath = CommandLine.arguments[1]
guard let startTime = Double(CommandLine.arguments[2]),
      let duration = Double(CommandLine.arguments[3]) else {
    print("Invalid time/duration")
    exit(1)
}

let url = URL(fileURLWithPath: videoPath)
let asset = AVURLAsset(url: url)
let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true
generator.requestedTimeToleranceBefore = .zero
generator.requestedTimeToleranceAfter = .zero

let step = 1.5
let numSteps = max(1, Int(duration / step))
var results: [FaceTrackingResult] = []

let frameWidth: Double = 1920.0
let cropWidth: Double = 608.0 // 1080 * 9/16 for standard 9:16 vertical crop of 1080p

for i in 0..<numSteps {
    let t = startTime + Double(i) * step
    let cmTime = CMTime(seconds: t, preferredTimescale: 600)
    var actualTime = CMTime.zero
    
    var midX: Double = 0.5
    var faceCount = 0
    
    if let cgImage = try? generator.copyCGImage(at: cmTime, actualTime: &actualTime) {
        let request = VNDetectFaceRectanglesRequest()
        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        if (try? handler.perform([request])) != nil, let faces = request.results {
            faceCount = faces.count
            if faceCount > 0 {
                // Find primary face (largest area)
                let primary = faces.max(by: { ($0.boundingBox.width * $0.boundingBox.height) < ($1.boundingBox.width * $1.boundingBox.height) })!
                midX = Double(primary.boundingBox.origin.x + primary.boundingBox.size.width / 2.0)
            }
        }
    }
    
    let pixelCenterX = midX * frameWidth
    let rawCropX = pixelCenterX - (cropWidth / 2.0)
    let clampedCropX = max(0, min(Int(frameWidth - cropWidth), Int(rawCropX)))
    
    results.append(FaceTrackingResult(time: Double(i) * step, faceCount: faceCount, midX: midX, cropX: clampedCropX))
}

let encoder = JSONEncoder()
if let jsonData = try? encoder.encode(results), let jsonString = String(data: jsonData, encoding: .utf8) {
    print(jsonString)
}
