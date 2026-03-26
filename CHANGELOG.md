## 11.2.8

### New Features ✨

- Clarify upload queueing logging and process completion logging by @calvin-codecov in [#110](https://github.com/getsentry/prevent-cli/pull/110)

### Bug Fixes 🐛

- Update deps by @thomasrockhu-codecov in [#117](https://github.com/getsentry/prevent-cli/pull/117)
- Sample high-volume "Token required" Sentry errors at 1% by @thomasrockhu-codecov in [#116](https://github.com/getsentry/prevent-cli/pull/116)
- Implement some sentry tagging to help identify issues by @thomasrockhu-codecov in [#115](https://github.com/getsentry/prevent-cli/pull/115)

### Internal Changes 🔧

#### Deps

- Bump requests from 2.32.3 to 2.32.4 in /prevent-cli by @dependabot in [#111](https://github.com/getsentry/prevent-cli/pull/111)
- Bump urllib3 from 2.3.0 to 2.6.3 in /prevent-cli by @dependabot in [#112](https://github.com/getsentry/prevent-cli/pull/112)
- Bump urllib3 from 2.3.0 to 2.6.3 in /codecov-cli by @dependabot in [#113](https://github.com/getsentry/prevent-cli/pull/113)
- Bump virtualenv from 20.26.6 to 20.36.1 in /codecov-cli by @dependabot in [#114](https://github.com/getsentry/prevent-cli/pull/114)

## 11.2.7

### Internal Changes 🔧

- Change upload size log to .info by @calvin-codecov in [#109](https://github.com/getsentry/prevent-cli/pull/109)

## 11.2.6

### Bug Fixes 🐛

- fix: add payload size and bump test-results-parser by @thomasrockhu-codecov in [#105](https://github.com/getsentry/prevent-cli/pull/105)

## 11.2.5

### Various fixes & improvements

- chore(release): bump test-results-parser to 0.6.0 (#102) by @thomasrockhu-codecov
- Update README links to point to new repository (#97) by @webknjaz
- Show project URLs on PyPI (#99) by @webknjaz
- Remove pytest-asyncio from dev dependencies (#98) by @webknjaz
- fix: Add missing f string in swiftcov func of xcode plugin (#96) by @wallisch

## 11.2.4

### Various fixes & improvements

- fix: run file fixes (#100) by @thomasrockhu-codecov

## 11.2.3

### Various fixes & improvements

- build: pin click version to correct version (#95) by @joseph-sentry

## 11.2.2

### Various fixes & improvements

- build: try auto discovering packages in setup tools (#94) by @joseph-sentry

## 11.2.1

### Various fixes & improvements

- fix: don't deepcopy click command in prevent cli (#93) by @joseph-sentry
- feat: Sign sentry-prevent-cli binaries with Cosign (#86) by @spalmurray

## 11.2.0

### Various fixes & improvements

- fix: set codecov-cli as an entrypoint (#91) by @joseph-sentry
- fix: add support for deriving repo slug from BUILDKITE_REPO (#88) by @joseph-sentry

## 11.1.0

### Various fixes & improvements

- deploy: Enable real publishes to pypi and gcs (#85) by @spalmurray

## 11.0.6

### Various fixes & improvements

- feat: Add codecov-cli gh release publish to craft flow (#83) by @spalmurray

## 11.0.5

### Various fixes & improvements

- Fix release trigger for codecov-cli publish (b896a153) by @spalmurray

## 11.0.4

### Various fixes & improvements

- fix: Add dependencies to package step (#81) by @spalmurray
- fix: Bundle assets into one artifact named sha for craft publish (#80) by @spalmurray
- fix: Craft try removing requireNames (#79) by @spalmurray
- fix: macos build (#78) by @spalmurray
- feat: Build out Craft release flow (#50) by @spalmurray
- feat: create new upload command (#77) by @joseph-sentry
- Remove workflows.old (#49) by @spalmurray
- docs: Update readme to be slightly more informative (#76) by @spalmurray
- Add craft yaml (#51) by @spalmurray
- fix: configurable rebranding (#7) by @joseph-sentry
- fix: handle merge_group github events (#6) by @joseph-sentry
- ci(release): Fix command to get previous release version (#48) by @ElioDiNino
- Release 11.0.3 (#46) by @sentry-release-bot
- fix: build with python 3.9 (#45) by @spalmurray
- Release 11.0.2 (#44) by @sentry-release-bot
- fix: release asset filename wrong (#43) by @spalmurray
- Release 11.0.2 (#42) by @sentry-release-bot
- fix: linux x86_64 build requiring glibc >= 2.35 (#41) by @spalmurray
- Release 11.0.1 (#40) by @sentry-release-bot
- fix: try testing version name (#37) by @thomasrockhu-codecov
- fix: set version name as env var (#35) by @thomasrockhu-codecov
- fix: Downgrade pyinstaller build to python 3.11 (#34) by @spalmurray
- Release 11.0.0 (#33) by @sentry-release-bot
- fix: pypi publish wrong path (#32) by @spalmurray

_Plus 34 more_

## 11.0.3

### What's Changed
- Release 11.0.2 by @sentry-release-bot in https://github.com/getsentry/prevent-cli/pull/44
- fix: build with python 3.9 by @spalmurray in https://github.com/getsentry/prevent-cli/pull/45
