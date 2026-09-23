// Generate oriented JPEG previews without modifying the original files.
import Foundation
import ImageIO

struct Job: Decodable { let source: String; let output: String }
struct Preview: Encodable { let path: String; let width: Int; let height: Int }
let jobs = try JSONDecoder().decode([Job].self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
var result: [String: [Preview]] = [:]
for job in jobs {
    guard let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: job.source) as CFURL, nil),
          let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
          let rawWidth = properties[kCGImagePropertyPixelWidth] as? Int,
          let rawHeight = properties[kCGImagePropertyPixelHeight] as? Int else {
        fatalError("Cannot read image: \(job.source)")
    }
    let orientation = properties[kCGImagePropertyOrientation] as? Int ?? 1
    let rotated = (5...8).contains(orientation)
    let width = rotated ? rawHeight : rawWidth
    let height = rotated ? rawWidth : rawHeight
    var previews: [Preview] = []
    var seenWidths = Set<Int>()
    for requestedWidth in [160, 480, 960, 1440] {
        let targetWidth = min(requestedWidth, width)
        let maxDimension = Int(ceil(Double(targetWidth) * Double(max(width, height)) / Double(width)))
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: maxDimension
        ]
        guard let image = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else {
            fatalError("Cannot resize image: \(job.source)")
        }
        if !seenWidths.insert(image.width).inserted { continue }
        let path = "\(job.output)-\(requestedWidth).jpg"
        try FileManager.default.createDirectory(at: URL(fileURLWithPath: path).deletingLastPathComponent(), withIntermediateDirectories: true)
        guard let destination = CGImageDestinationCreateWithURL(URL(fileURLWithPath: path) as CFURL, "public.jpeg" as CFString, 1, nil) else {
            fatalError("Cannot write preview: \(path)")
        }
        CGImageDestinationAddImage(destination, image, [kCGImageDestinationLossyCompressionQuality: 0.88] as CFDictionary)
        guard CGImageDestinationFinalize(destination) else { fatalError("Cannot save preview: \(path)") }
        previews.append(Preview(path: path, width: image.width, height: image.height))
    }
    result[job.source] = previews
}
let data = try JSONEncoder().encode(result)
FileHandle.standardOutput.write(data)
