.PHONY: all clean ios tvos watchos android macos linux windows

all: ios tvos watchos android macos linux windows

clean:
	rm -rf output build

ios:
	@python scripts/build.py ios

tvos:
	@python scripts/build.py tvos

watchos:
	@python scripts/build.py watchos

android:
	@python scripts/build.py android

macos:
	@python scripts/build.py macos

linux:
	@python scripts/build.py linux

windows:
	@python scripts/build.py windows
