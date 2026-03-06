# Poco Lib

Prebuilt [POCO C++ Libraries](https://pocoproject.org/) (Foundation, Net, Util, XML, Zip, NetSSL, Crypto) for cross-platform development. Each archive bundles Poco and its dependencies (zlib, pcre2, utf8proc, expat, OpenSSL) in one package so you only need to link a single `lib` and `include`. Built via Conan and distributed as individual platform archives through GitHub Releases.

## Supported Platforms

| Platform | Architectures | Output |
|----------|---------------|--------|
| iOS | arm64 (device), arm64 + x86_64 (simulator) | `.a` + `.xcframework` |
| tvOS | arm64 (device), arm64 + x86_64 (simulator) | `.a` + `.xcframework` |
| watchOS | arm64_32 (device), arm64 + x86_64 (simulator) | `.a` + `.xcframework` |
| Android | arm64-v8a, armeabi-v7a, x86_64, x86 | `.a` (static) |
| macOS | arm64 + x86_64 (universal) | `.a` |
| Linux | x86_64, aarch64 | `.a` |
| Windows | x64, x86, arm64 | `.lib` |

## Usage with CMake

### CPM.cmake

```cmake
CPMAddPackage(
    NAME poco-lib
    GITHUB_REPOSITORY paulocoutinhox/poco-lib
    GIT_TAG v1.14.2
)

target_link_libraries(your_target PRIVATE
    PocoFoundation
    PocoNet
    PocoUtil
    PocoXML
    PocoZip
    PocoCrypto
    PocoNetSSL
)
```

### FetchContent

```cmake
include(FetchContent)

FetchContent_Declare(
    poco-lib
    GIT_REPOSITORY https://github.com/paulocoutinhox/poco-lib.git
    GIT_TAG v1.14.2
)

FetchContent_MakeAvailable(poco-lib)

target_link_libraries(your_target PRIVATE
    PocoFoundation
    PocoNet
    PocoUtil
    PocoXML
    PocoZip
    PocoCrypto
    PocoNetSSL
)
```

### Standalone Include

Download `cmake/poco-lib.cmake` and include it directly:

```cmake
set(POCO_LIB_VERSION "1.14.2")
include(path/to/poco-lib.cmake)

target_link_libraries(your_target PRIVATE
    PocoFoundation
    PocoNet
    PocoUtil
    PocoXML
    PocoZip
    PocoCrypto
    PocoNetSSL
)
```

### How It Works

When used via CPM or FetchContent, the project includes `cmake/poco-lib.cmake`, which:

1. If `POCO_ROOT` is set and valid, uses that path
2. Otherwise downloads the matching prebuilt archive from GitHub Releases for the current platform
3. Creates imported targets `PocoFoundation`, `PocoNet`, `PocoUtil`, `PocoXML`, `PocoZip`, `PocoCrypto`, `PocoNetSSL`

On Windows with MSVC you may need to link the same names as `.lib` (e.g. `PocoFoundation.lib`). All transitive dependencies are in the same archive; link the Poco targets and use the single `include` and `lib` from the package.

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POCO_LIB_VERSION` | `1.14.2` | Poco version / release tag to download |
| `POCO_LIB_REPO` | `paulocoutinhox/poco-lib` | GitHub repository for download URLs |
| `POCO_LIB_USE_PREBUILT` | `ON` | Set to `OFF` only when providing `POCO_ROOT` manually |

### Archive Resolution

| Target | Archive |
|--------|---------|
| iOS | `poco-ios.zip` |
| tvOS | `poco-tvos.zip` |
| watchOS | `poco-watchos.zip` |
| Android | `poco-android.zip` |
| macOS | `poco-macos.zip` |
| Linux x86_64 | `poco-linux-x86_64.zip` |
| Linux aarch64 | `poco-linux-aarch64.zip` |
| Windows x64 | `poco-windows-x64.zip` |
| Windows x86 | `poco-windows-x86.zip` |
| Windows arm64 | `poco-windows-arm64.zip` |

## Building From Source

### Prerequisites

- Python 3
- [Conan 2](https://conan.io/) (`pip install conan`)
- Platform-specific toolchains (Xcode for Apple, Android NDK via Conan, MSVC for Windows)

Setup Conan default profile:

```bash
conan profile detect --force
```

### Build Commands

Build all platforms:

```bash
make all
```

Build individual platforms:

```bash
make ios
make tvos
make watchos
make android
make macos
make linux
make windows
```

Or run the script directly:

```bash
python scripts/build.py <platform>
```

Build output is placed in the `output/` directory.

### Output Structure

Includes and libraries are **individual** per component (Foundation, Net, Util, XML, Zip, Crypto, NetSSL): headers live under `include/Poco/` with subdirs per module, and each component has its own `.a` or `.lib` file so you can link only what you need.

**iOS / tvOS / watchOS:**

```
output/<platform>/
├── include/
│   └── Poco/
│       ├── Foundation/ ...
│       ├── Net/ ...
│       ├── Util/ ...
│       ├── XML/ ...
│       ├── Zip/ ...
│       ├── Crypto/ ...
│       └── NetSSL/ ...
└── lib/
    ├── <sdk>/<arch>/libPoco*.a
    ├── libPocoFoundation.xcframework/
    ├── libPocoNet.xcframework/
    └── ...
```

**Android:**

```
output/android/
├── include/Poco (Poco headers)
└── lib/
    ├── arm64-v8a/
    ├── armeabi-v7a/
    ├── x86_64/
    └── x86/
```

**macOS (universal binary):**

```
output/macos/
├── include/Poco/ ...
└── lib/
    ├── libPocoFoundation.a
    ├── libPocoNet.a
    └── ...
```

**Linux / Windows:**

```
output/<platform>-<arch>/
├── include/Poco/ ...
└── lib/
    └── libPoco*.a  (or .lib on Windows)
```

## GitHub Actions

Each platform has its own build workflow that can be triggered manually via `workflow_dispatch`:

- `build-ios.yml`
- `build-tvos.yml`
- `build-watchos.yml`
- `build-android.yml`
- `build-macos.yml`
- `build-linux.yml`
- `build-windows.yml`

All platform builds run in parallel.

### Release

When a tag matching `vX.Y.Z` is pushed, the `release.yml` workflow automatically:

1. Triggers all platform builds in parallel
2. Packages each platform output into an individual `.zip` archive
3. Creates a GitHub Release and uploads all archives as assets

```bash
git tag v1.14.2
git push origin v1.14.2
```

## License

MIT License. See [LICENSE](LICENSE) for details.
