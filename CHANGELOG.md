# CHANGELOG

## 0.10.0

Released on 2025-12-28.

### Enhancements

- New class-based group API.
- Support for PEP604 annotations.
- clap-py is now type checked by mypy (basedpyright was already supported).

## 0.9.0

Released on 2025-12-14.

### Fixed

- Create parser when `.parse()` is called (and not in the decorator). This fixes
  errors when `multiprocessing` is used.

## 0.8.0

Released on 2025-10-05.

### Enhancements

- Style possible values of enum members in long help.
- Align help messages of enum members.

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
