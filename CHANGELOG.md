# CHANGELOG

## 0.7.3

Released on 2025-10-04.

### Fixed

- Print groups in the help output in the order in which they are created.
- Remove deleted public function for creating groups from the stub file.

## 0.7.2

Released on 2025-10-02.

### Enhancements

- Print help for enum members in the long help
- Improved kebab-case conversion

### Changed

- Renamed `clap.Parser.parse_args()` to `clap.Parser.parse()`

### Fixed

- Fixed a typo in the type stub for `clap.command`
- Fixed imports in the stub file for `basedpyright>=1.31.4`
- Added `@abstractmethod` to `clap.Parser.parse()`
- Fixed missing style usages in help output
- Fixed text wrapping in help output

## 0.5.0

Released on 2025-06-21.

Initial release.
