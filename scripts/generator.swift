import Foundation
import ImageIO
import CoreGraphics
import UniformTypeIdentifiers

let aprBase64 = "YnBsaXN0MDDSAQIDBFFsUWQQABABCA0PERMAAAAAAAABAQAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAFQ=="

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 2 else {
    fail("Usage: generator inspect <file.heic> | generator make <light> <dark> <output.heic>")
}

func loadImage(_ url: URL) -> CGImage {
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        fail("Could not load image: \(url.path)")
    }
    return image
}

if args[1] == "inspect" {
    guard args.count == 3 else { fail("Usage: generator inspect <file.heic>") }
    let url = URL(fileURLWithPath: args[2])
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
        fail("Could not inspect HEIC: \(url.path)")
    }
    print("count=\(CGImageSourceGetCount(source))")
    for index in 0..<CGImageSourceGetCount(source) {
        if let image = CGImageSourceCreateImageAtIndex(source, index, nil) {
            print("frame\(index)=\(image.width)x\(image.height)")
        }
    }
    if let metadata = CGImageSourceCopyMetadataAtIndex(source, 0, nil),
       let tag = CGImageMetadataCopyTagWithPath(metadata, nil, "apple_desktop:apr" as CFString),
       let value = CGImageMetadataTagCopyValue(tag) {
        print("apr=\(value)")
    } else {
        print("apr=missing")
    }
    exit(0)
}

guard args[1] == "make", args.count == 5 else {
    fail("Usage: generator make <light> <dark> <output.heic>")
}

let lightURL = URL(fileURLWithPath: args[2])
let darkURL = URL(fileURLWithPath: args[3])
let outputURL = URL(fileURLWithPath: args[4])
let lightImage = loadImage(lightURL)
let darkImage = loadImage(darkURL)

guard lightImage.width == darkImage.width, lightImage.height == darkImage.height else {
    fail("Images must have the same dimensions.")
}

guard let destination = CGImageDestinationCreateWithURL(outputURL as CFURL, UTType.heic.identifier as CFString, 2, nil) else {
    fail("Could not create HEIC destination: \(outputURL.path)")
}

let metadata = CGImageMetadataCreateMutable()
let namespace = "http://ns.apple.com/namespace/1.0" as CFString
let prefix = "apple_desktop" as CFString
CGImageMetadataRegisterNamespaceForPrefix(metadata, namespace, prefix, nil)
CGImageMetadataSetValueWithPath(metadata, nil, "apple_desktop:apr" as CFString, aprBase64 as CFString)

let options: [CFString: Any] = [kCGImageDestinationLossyCompressionQuality: 0.95]
CGImageDestinationAddImageAndMetadata(destination, lightImage, metadata, options as CFDictionary)
CGImageDestinationAddImage(destination, darkImage, options as CFDictionary)

guard CGImageDestinationFinalize(destination) else {
    fail("Could not finalize HEIC file.")
}

print(outputURL.path)
