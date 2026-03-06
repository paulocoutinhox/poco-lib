# Poco Lib

Prebuilt [POCO C++ Libraries](https://pocoproject.org/) (Foundation, Net, Util, XML, Zip, NetSSL, Crypto) for cross-platform development. Built via Conan and distributed as individual platform archives through GitHub Releases.

## Supported Platforms

| Platform | Architectures | Output |
|----------|----------------|--------|
| iOS | arm64 (device), arm64 + x86_64 (simulator) | `.a` + `.xcframework` |
| tvOS | arm64 (device), arm64 + x86_64 (simulator) | `.a` + `.xcframework` |
| watchOS | arm64_32 (device), arm64 + x86_64 (simulator) | `.a` + `.xcframework` |
| Android | arm64-v8a, armeabi-v7a, x86_64, x86 | `.a` (static) |
| macOS | arm64 + x86_64 (universal) | `.a` |
| Linux | x86_64, aarch64 | `.a` |
| Windows | x64, x86, arm64 | `.lib` |

## Usage in Your Project

After building or downloading a release archive, use the Poco libraries and headers in your CMake project:

```cmake
set(POCO_ROOT /path/to/poco-lib/output/macos)  # or path to extracted release zip

add_executable(your_app main.cpp)
target_include_directories(your_app PRIVATE ${POCO_ROOT}/include)
target_link_directories(your_app PRIVATE ${POCO_ROOT}/lib)
target_link_libraries(your_app PRIVATE
    PocoFoundation
    PocoNet
    PocoUtil
    PocoXML
    PocoZip
    PocoCrypto
    PocoNetSSL
)
```

On Windows with MSVC you may need to link the same libraries as `.lib` (e.g. `PocoFoundation.lib`).

### OpenSSL (for NetSSL / Crypto)

NetSSL and Crypto provide HTTPS, TLS and cryptography. When linking an app that uses PocoNetSSL or PocoCrypto you must also link OpenSSL. Example below uses a prebuilt OpenSSL via a CMake helper.

```cmake
cmake_minimum_required(VERSION 3.20)
project(my_app LANGUAGES CXX)

# OpenSSL from openssl-lib (downloads prebuilt for current platform or falls back to system)
set(OPENSSL_LIB_VERSION "3.6.1")
list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/third-party/openssl-lib/cmake)
include(openssl-lib)

# Poco from poco-lib output or extracted release zip
set(POCO_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/third-party/poco-lib/output/macos)

add_executable(my_app main.cpp)
target_include_directories(my_app PRIVATE ${POCO_ROOT}/include)
target_link_directories(my_app PRIVATE ${POCO_ROOT}/lib)
target_link_libraries(my_app PRIVATE
    PocoFoundation
    PocoNet
    PocoUtil
    PocoXML
    PocoZip
    PocoCrypto
    PocoNetSSL
    OpenSSL::SSL
    OpenSSL::Crypto
)
```

To use the script only, put `openssl-lib.cmake` in a folder (e.g. `cmake/`), then `list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)` and `include(openssl-lib)`. See [openssl-lib](https://github.com/paulocoutinhox/openssl-lib) for the helper.

## Building From Source

### Prerequisites

- Python 3
- [Conan 2](https://conan.io/) (`pip install conan`)
- Platform-specific toolchains (Xcode for Apple, Android NDK via Conan tool_requires, MSVC for Windows)

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
├── include/ (Poco headers)
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

`build-all.yml` runs all platform builds in parallel.

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
