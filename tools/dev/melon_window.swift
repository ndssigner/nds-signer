// Prints "<window id> <x> <y> <width> <height>" of the melonDS window
// (macOS dev helper for screenshots: screencapture -l <window id>).
import CoreGraphics
let windows = CGWindowListCopyWindowInfo(.optionOnScreenOnly, kCGNullWindowID) as! [[String: Any]]
for w in windows where (w["kCGWindowOwnerName"] as? String) == "melonDS" && (w["kCGWindowLayer"] as? Int) == 0 {
    let b = w["kCGWindowBounds"] as! [String: Any]
    print(w["kCGWindowNumber"]!, b["X"]!, b["Y"]!, b["Width"]!, b["Height"]!)
    break
}
