import Foundation

/// API base URL, with a user-configurable override — mirrors the Android client's
/// `SettingsDataStore` connection-settings override (see `apps/android/README.md`
/// → "Configuring the API base URL"). The backend is reachable over Tailscale only,
/// so the default points at its MagicDNS name; see Info.plist's ATS exception.
final class AppSettings: ObservableObject {
    static let defaultBaseURL = "http://piglet.tailf5e9c9.ts.net:5000/api/v1/"
    private static let overrideKey = "api_base_url_override"

    @Published var baseURLOverride: String? {
        didSet {
            if let baseURLOverride, !baseURLOverride.isEmpty {
                UserDefaults.standard.set(baseURLOverride, forKey: Self.overrideKey)
            } else {
                UserDefaults.standard.removeObject(forKey: Self.overrideKey)
            }
        }
    }

    init() {
        baseURLOverride = UserDefaults.standard.string(forKey: Self.overrideKey)
    }

    var baseURL: String {
        (baseURLOverride?.isEmpty == false) ? baseURLOverride! : Self.defaultBaseURL
    }

    static func isValid(_ candidate: String) -> Bool {
        (candidate.hasPrefix("http://") || candidate.hasPrefix("https://")) && candidate.hasSuffix("/")
    }
}
