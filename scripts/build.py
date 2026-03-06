#!/usr/bin/env python3
"""
Build Poco (Foundation, Net, Util, XML, Zip, NetSSL, Crypto) for a given platform via Conan.
Uses POCO from Conan Center with OpenSSL as dependency.
Usage: python scripts/build.py <platform>
Platforms: android, ios, macos, linux, tvos, watchos, windows
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

LIB_EXTENSIONS = (".a", ".so", ".lib")
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent


def run_cmd(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd or ROOT, check=True)


def _has_poco_libs(lib_dir: Path) -> bool:
    if not lib_dir.is_dir():
        return False
    for f in lib_dir.iterdir():
        if f.is_file() and "Poco" in f.name and f.suffix in LIB_EXTENSIONS:
            return True
    return False


def _has_poco_include(inc_dir: Path) -> bool:
    poco_dir = inc_dir / "Poco"
    return poco_dir.is_dir() or (inc_dir.is_dir() and any("poco" in p.name.lower() for p in inc_dir.iterdir()))


def _is_deploy_package(pkg_dir: Path, exclude: Path | None) -> bool:
    """True if dir looks like a Conan-deployed package (include + lib with artifacts)."""
    if exclude is not None and pkg_dir.resolve() == exclude.resolve():
        return False
    inc = pkg_dir / "include"
    lib = pkg_dir / "lib"
    if not inc.is_dir() or not lib.is_dir():
        return False
    for f in lib.rglob("*"):
        if f.is_file() and f.suffix in LIB_EXTENSIONS:
            return True
    return False


def _copy_libs(src_lib: Path, lib_dst: Path) -> None:
    for p in src_lib.iterdir():
        if p.is_file() and p.suffix in LIB_EXTENSIONS:
            shutil.copy2(p, lib_dst / p.name)
    for sub in ("Release", "Debug"):
        subdir = src_lib / sub
        if subdir.is_dir():
            for p in subdir.iterdir():
                if p.is_file() and p.suffix in LIB_EXTENSIONS:
                    shutil.copy2(p, lib_dst / p.name)


def _merge_include(src_include: Path, include_dst: Path) -> None:
    for p in src_include.iterdir():
        dst = include_dst / p.name
        if p.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(p, dst)
        else:
            shutil.copy2(p, dst)


def build_single(profile: str, lib_dst: Path, include_dst: Path | None = None) -> None:
    build_dir = ROOT / "build" / profile
    lib_dst = lib_dst.resolve()
    if include_dst is not None:
        include_dst = include_dst.resolve()

    print(f"Building Poco for profile: {profile}")
    build_dir.mkdir(parents=True, exist_ok=True)
    if lib_dst.exists():
        shutil.rmtree(lib_dst)
    lib_dst.mkdir(parents=True, exist_ok=True)

    profile_path = ROOT / "profiles" / f"{profile}.profile"
    subprocess.run(
        [
            "conan",
            "install",
            str(ROOT),
            f"--profile:host={profile_path}",
            "--profile:build=default",
            "--build=missing",
            "--deployer=full_deploy",
            f"--output-folder={build_dir}",
        ],
        cwd=ROOT,
        check=True,
    )

    poco_dir = None
    deploy_dirs: list[Path] = []
    for d in build_dir.iterdir():
        if not d.is_dir():
            continue
        inc = d / "include"
        lib = d / "lib"
        if not inc.is_dir() or not lib.is_dir():
            continue
        if _has_poco_libs(lib) and _has_poco_include(inc):
            poco_dir = d
        if _is_deploy_package(d, None):
            deploy_dirs.append(d)
    if poco_dir is None:
        raise SystemExit("Error: could not find deployed Poco package")

    if include_dst is not None:
        include_dst.mkdir(parents=True, exist_ok=True)
        _merge_include(poco_dir / "include", include_dst)

    _copy_libs(poco_dir / "lib", lib_dst)
    for dep_dir in deploy_dirs:
        if dep_dir.resolve() == poco_dir.resolve():
            continue
        _copy_libs(dep_dir / "lib", lib_dst)
        if include_dst is not None:
            _merge_include(dep_dir / "include", include_dst)

    shutil.rmtree(build_dir, ignore_errors=True)
    print(f"Completed: {profile}")


def build_android() -> None:
    output = ROOT / "output" / "android"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    build_single("android-arm64-v8a", output / "lib" / "arm64-v8a", output / "include")
    build_single("android-armeabi-v7a", output / "lib" / "armeabi-v7a")
    build_single("android-x86_64", output / "lib" / "x86_64")
    build_single("android-x86", output / "lib" / "x86")
    print(f"Android build complete: {output}")


def build_ios() -> None:
    output = ROOT / "output" / "ios"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    build_single("ios-arm64", output / "lib" / "iphoneos" / "arm64", output / "include")
    build_single("ios-simulator-arm64", output / "lib" / "iphonesimulator" / "arm64")
    build_single("ios-simulator-x86_64", output / "lib" / "iphonesimulator" / "x86_64")
    sim_fat = output / "lib" / "_sim_fat"
    sim_fat.mkdir(parents=True, exist_ok=True)
    sim_arm = output / "lib" / "iphonesimulator" / "arm64"
    sim_x64 = output / "lib" / "iphonesimulator" / "x86_64"
    for lib in (f for f in sim_arm.iterdir() if f.is_file() and f.suffix == ".a" and "Poco" in f.name):
        run_cmd(["lipo", "-create", str(sim_arm / lib.name), str(sim_x64 / lib.name), "-output", str(sim_fat / lib.name)])
    device_lib = output / "lib" / "iphoneos" / "arm64"
    include = output / "include"
    for lib in (f for f in device_lib.iterdir() if f.is_file() and f.suffix == ".a" and "Poco" in f.name):
        stem = lib.stem
        run_cmd([
            "xcodebuild", "-create-xcframework",
            "-library", str(device_lib / lib.name),
            "-headers", str(include),
            "-library", str(sim_fat / lib.name),
            "-headers", str(include),
            "-output", str(output / "lib" / f"{stem}.xcframework"),
        ])
    shutil.rmtree(sim_fat, ignore_errors=True)
    print(f"iOS build complete: {output}")


def build_macos() -> None:
    output = ROOT / "output" / "macos"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    build_single("macos-arm64", output / "lib" / "_arm64", output / "include")
    build_single("macos-x86_64", output / "lib" / "_x86_64")
    lib_dir = output / "lib"
    for f in (lib_dir / "_arm64").iterdir():
        if f.is_file() and f.suffix == ".a" and "Poco" in f.name:
            run_cmd([
                "lipo", "-create",
                str(lib_dir / "_arm64" / f.name),
                str(lib_dir / "_x86_64" / f.name),
                "-output", str(lib_dir / f.name),
            ])
    shutil.rmtree(lib_dir / "_arm64", ignore_errors=True)
    shutil.rmtree(lib_dir / "_x86_64", ignore_errors=True)
    print(f"macOS build complete: {output}")


def build_linux() -> None:
    for name, profile in [("linux-x86_64", "linux-x86_64"), ("linux-aarch64", "linux-aarch64")]:
        output = ROOT / "output" / name
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True)
        build_single(profile, output / "lib", output / "include")
    print("Linux build complete")


def build_tvos() -> None:
    output = ROOT / "output" / "tvos"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    build_single("tvos-arm64", output / "lib" / "appletvos" / "arm64", output / "include")
    build_single("tvos-simulator-arm64", output / "lib" / "appletvsimulator" / "arm64")
    build_single("tvos-simulator-x86_64", output / "lib" / "appletvsimulator" / "x86_64")
    sim_fat = output / "lib" / "_sim_fat"
    sim_fat.mkdir(parents=True, exist_ok=True)
    sim_arm = output / "lib" / "appletvsimulator" / "arm64"
    sim_x64 = output / "lib" / "appletvsimulator" / "x86_64"
    for lib in (f for f in sim_arm.iterdir() if f.is_file() and f.suffix == ".a" and "Poco" in f.name):
        run_cmd(["lipo", "-create", str(sim_arm / lib.name), str(sim_x64 / lib.name), "-output", str(sim_fat / lib.name)])
    device_lib = output / "lib" / "appletvos" / "arm64"
    include = output / "include"
    for lib in (f for f in device_lib.iterdir() if f.is_file() and f.suffix == ".a" and "Poco" in f.name):
        run_cmd([
            "xcodebuild", "-create-xcframework",
            "-library", str(device_lib / lib.name),
            "-headers", str(include),
            "-library", str(sim_fat / lib.name),
            "-headers", str(include),
            "-output", str(output / "lib" / f"{lib.stem}.xcframework"),
        ])
    shutil.rmtree(sim_fat, ignore_errors=True)
    print(f"tvOS build complete: {output}")


def build_watchos() -> None:
    output = ROOT / "output" / "watchos"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    build_single("watchos-arm64_32", output / "lib" / "watchos" / "arm64_32", output / "include")
    build_single("watchos-simulator-arm64", output / "lib" / "watchsimulator" / "arm64")
    build_single("watchos-simulator-x86_64", output / "lib" / "watchsimulator" / "x86_64")
    sim_fat = output / "lib" / "_sim_fat"
    sim_fat.mkdir(parents=True, exist_ok=True)
    sim_arm = output / "lib" / "watchsimulator" / "arm64"
    sim_x64 = output / "lib" / "watchsimulator" / "x86_64"
    for lib in (f for f in sim_arm.iterdir() if f.is_file() and f.suffix == ".a" and "Poco" in f.name):
        run_cmd(["lipo", "-create", str(sim_arm / lib.name), str(sim_x64 / lib.name), "-output", str(sim_fat / lib.name)])
    device_lib = output / "lib" / "watchos" / "arm64_32"
    include = output / "include"
    for lib in (f for f in device_lib.iterdir() if f.is_file() and f.suffix == ".a" and "Poco" in f.name):
        run_cmd([
            "xcodebuild", "-create-xcframework",
            "-library", str(device_lib / lib.name),
            "-headers", str(include),
            "-library", str(sim_fat / lib.name),
            "-headers", str(include),
            "-output", str(output / "lib" / f"{lib.stem}.xcframework"),
        ])
    shutil.rmtree(sim_fat, ignore_errors=True)
    print(f"watchOS build complete: {output}")


def build_windows() -> None:
    for name, profile in [
        ("windows-x64", "windows-x64"),
        ("windows-x86", "windows-x86"),
        ("windows-arm64", "windows-arm64"),
    ]:
        output = ROOT / "output" / name
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True)
        build_single(profile, output / "lib", output / "include")
    print("Windows build complete")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/build.py <platform>", file=sys.stderr)
        print("Platforms: android, ios, macos, linux, tvos, watchos, windows", file=sys.stderr)
        sys.exit(1)
    platform = sys.argv[1].lower()
    builders = {
        "android": build_android,
        "ios": build_ios,
        "macos": build_macos,
        "linux": build_linux,
        "tvos": build_tvos,
        "watchos": build_watchos,
        "windows": build_windows,
    }
    if platform not in builders:
        print(f"Unknown platform: {platform}", file=sys.stderr)
        sys.exit(1)
    builders[platform]()


if __name__ == "__main__":
    main()
