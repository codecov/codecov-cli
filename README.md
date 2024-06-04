# CodecovCLI 

[![codecov](https://codecov.io/gh/codecov/codecov-cli/branch/master/graph/badge.svg?token=jN0CICuA6Z)](https://codecov.io/gh/codecov/codecov-cli)
[![Build-Test-Upload](https://github.com/codecov/codecov-cli/actions/workflows/push_flow.yml/badge.svg)](https://github.com/codecov/codecov-cli/actions/workflows/push_flow.yml)

CodecovCLI is a new way for users to interact with Codecov directly from the user’s terminal or CI platform. Many Codecov features that require the user’s interference can be done via the codecovCLI. It saves commits, creates reports, uploads coverage and has many more features.

- [CodecovCLI](#codecovcli)
- [Installing](#installing)
  - [Using PIP](#using-pip)
  - [As a Binary](#as-a-binary)
    - [Integrity Checking the Binary](#integrity-checking-the-binary)
- [How to Upload to Codecov](#how-to-upload-to-codecov)
  - [How to Get an Upload Token](#how-to-get-an-upload-token)
- [Usage](#usage)
- [Codecov-cli Commands](#codecov-cli-commands)
  - [create-commit](#create-commit)
  - [create-report](#create-report)
  - [do-upload](#do-upload)
  - [create-report-results](#create-report-results)
  - [get-report-results](#get-report-results)
  - [pr-base-picking](#pr-base-picking)
  - [send-notifications](#send-notifications)
  - [empty-upload](#empty-upload)
- [How to Use Local Upload](#how-to-use-local-upload)
- [Work in Progress Features](#work-in-progress-features)
  - [Plugin System](#plugin-system)
  - [Static Analysis](#static-analysis)
- [Contributions](#contributions)
  - [Requirements](#requirements)
  - [Guidelines](#guidelines)
  - [Dependencies](#dependencies)
- [Releases](#releases)

# Installing

## Using PIP
To use codecov-cli in your local machine, or your CI workflows, you need to install it:

`pip install codecov-cli`

The above command will download the latest version of Codecov-cli. If you wish to use a specific version, releases can be viewed [here](https://pypi.org/project/codecov-cli/#history). 

Note: If you're installing in a `pyenv` environment, you may need to call `pyenv rehash` before the CLI will work. 

## As a Binary
If you would like to use the CLI in an environment that does not have access to Python / PIP, you can install the CLI as a compiled binary. Linux and macOS releases can be found [here](https://cli.codecov.io/), along with SHASUMs and signatures for each released version. Binary releases are also available via [Github releases](https://github.com/codecov/codecov-cli/releases) on this repository. 

You can retrieve the Binary for Linux directly from your command line as follows:

```
curl -Os https://cli.codecov.io/latest/linux/codecov
sudo chmod +x codecov
./codecov --help
```

### Integrity Checking the Binary

The binary can be integrity checked using a SHASUM256 and SHASUM256.sig file. The process for macos and Linux is identical. Linux is as follows:

```
curl https://keybase.io/codecovsecurity/pgp_keys.asc | gpg --no-default-keyring --keyring trustedkeys.gpg --import # One-time step
curl -Os https://cli.codecov.io/latest/linux/codecov
curl -Os https://cli.codecov.io/latest/linux/codecov.SHA256SUM
curl -Os https://cli.codecov.io/latest/linux/codecov.SHA256SUM.sig

gpgv codecov.SHA256SUM.sig codecov.SHA256SUM

shasum -a 256 -c codecov.SHA256SUM
```

For macos you will want to use the macos distributions of the binary (e.g., https://cli.codecov.io/latest/macos/codecov)


# How to Upload to Codecov
If desired, the CLI can be used as a replacement for our [NodeJS Binary Uploader](https://github.com/codecov/uploader). To use the CLI to upload from your CI workflow, you need to add these commands: 

```
pip install codecov-cli
codecovcli create-commit
codecovcli create-report
codecovcli do-upload
```
OR 
```
pip install codecov-cli
codecovcli upload-process
```
codecovcli upload-process is a wrapper for create-commit, create-report and do-upload. 

You can customize the commands with the options aligned with each command. 

Note that these commands will automatically search your environment for a `$CODECOV_TOKEN` environment variable and use it if found. If you do not have a repository upload token, or global upload token, stored as an environment variable, you will need to pass it into **each command manually**, like so: `-t {$CODECOV_TOKEN}`. 

## How to Get an Upload Token
The following tokens are suitable for uploading:

* The [Repository Upload Token](https://docs.codecov.com/docs/codecov-uploader#upload-token): Found on the settings page of your repository, also viewable on the `/new` page when setting up a repository on Codecov for the first time. 
* The [Global Upload Token](https://docs.codecov.com/docs/codecov-uploader#organization-upload-token): Found on your organization settings page (e.g., `https://app.codecov.io/account/<scm>/<org>/org-upload-token`). 


# Usage 
If the installation is successful, running `codecovcli --help` will output the available commands along with the different general options that can be used with them. 
```
Usage: codecovcli [OPTIONS] COMMAND [ARGS]...
```
Codecov-cli supports user input. These inputs, along with their descriptions and usage contexts, are listed in the table below:

| Input  | Description | Usage |
| :---:     |     :---:   |    :---:   |
| `--auto-load-params-from`  | The CI/CD platform   | Optional |
| `--codecov-yml-path` | The path for your codecov.yml  | Optional
| `--enterprise-url` | Change the upload host (Enterprise use) | Optional
| `--version` | Codecov-cli's version | Optional
| `--verbose` or `-v` | Run the cli with verbose logging | Optional 

# Codecov-cli Commands
| Command  | Description | 
| :---:     |     :---:   |    
| `create-commit` | Saves the commit's metadata in codecov, it's only necessary to run this once per commit 
| `create-report` | Creates an empty report in codecov with initial data e.g. report name, report's commit 
| `do-upload` | Searches for and uploads coverage data to codecov 
| `create-report-results` | Used for local upload. It tells codecov that you finished local uploading and want it to calculate the results for you to get them locally.
| `get-report-results` | Used for local upload. It asks codecov to provide you the report results you calculated with the previous command. 
| `pr-base-picking` | Tells codecov that you want to explicitly define a base for your PR
| `upload-process` | A wrapper for 3 commands. Create-commit, create-report and do-upload. You can use this command to upload to codecov instead of using the previosly mentioned commands.
| `send-notifications` | A command that tells Codecov that you finished uploading and you want to be sent notifications. To disable automatically sent notifications please consider adding manual_trigger to your codecov.yml, so it will look like codecov: notify: manual_trigger: true.
>**Note**: Every command has its own different options that will be mentioned later in this doc. Codecov will try to load these options from your CI environment variables, if not, it will try to load them from git, if not found, you may need to add them manually. 



## create-commit 
`codecovcli create-commit [Options]`

| Option  | Description | Usage
| :---:     |     :---:   |    :---:   |   
| -C, --sha, --commit-sha | Commit SHA (with 40 chars) | Required
|--parent-sha | SHA (with 40 chars) of what should be the parent of this commit | Optional
|-P, --pr, --pull-request-number| Specify the pull request number manually. Used to override pre-existing CI environment variables | Optional
|-B, --branch | Branch to which this commit belongs to | Optional
|-r, --slug | owner/repo slug used instead of the private repo token in Self-hosted | Required
|-t, --token | Codecov upload token | Required 
|--git-service | Git Provider. Options: github, gitlab, bitbucket, github_enterprise, gitlab_enterprise, bitbucket_server | Required
|-h, --help | Shows usage, and command options                         


## create-report
`codecovcli create-report [OPTIONS]`

| Option  | Description | Usage
| :---:     |     :---:   |    :---:   |   
| -C, --sha, --commit-sha | Commit SHA (with 40 chars) | Required
|-r, --slug | owner/repo slug used instead of the private repo token in Self-hosted | Required
|-t, --token | Codecov upload token | Required 
|--git-service | Git Provider. Options: github, gitlab, bitbucket, github_enterprise, gitlab_enterprise, bitbucket_server | Required
|--code| The code of the report. This is used in local uploading to isolate local reports from regular or cloud reports uploaded to codecov so they don't get merged. It's basically a name you give to your report e.g. local-report. | Optional
|-h, --help | Shows usage, and command options      

## do-upload
`codecovcli do-upload [OPTIONS]`

| Option  | Description | Usage
| :---:     |     :---:   |    :---:   |   
|-C, --sha, --commit-sha|    Commit SHA (with 40 chars) | Required
|--report-code | The code of the report defined when creating the report. If unsure, leave default | Optional
|--network-root-folder |      Root folder from which to consider paths on the network section  default: (Current working directory) | Optional
|-s, --dir, --coverage-files-search-root-folder | Folder where to search for coverage files default: (Current Working Directory) | Optional
|--exclude, --coverage-files-search-exclude-folder | Folders to exclude from search | Optional
|-f, --file, --coverage-files-search-direct-file | Explicit files to upload | Optional
|--disable-search | Disable search for coverage files. This is helpful when specifying what files you want to upload with the --file option.| Optional
|-b, --build, --build-code | Specify the build number manually | Optional
|--build-url | The URL of the build where this is running | Optional
|--job-code | The job code for the CI run | Optional
|-t, --token | Codecov upload token | Required
|-n, --name | Custom defined name of the upload. Visible in Codecov UI | Optional
|-B, --branch | Branch to which this commit belongs to | Optional
|-r, --slug | owner/repo slug | Required
|-P, --pr, --pull-request-number | Specify the pull request number manually. Used to override pre-existing CI environment variables | Optional
|-e, --env, --env-var | Specify environment variables to be included with this build. | Optional
|-F, --flag | Flag the upload to group coverage metrics. Multiple flags allowed. | Optional
|--plugin | plugins to run. Options: xcode, gcov, pycoverage. The default behavior runs them all. | Optional
|-Z, --fail-on-error | Exit with non-zero code in case of error uploading.|Optional
|-d, --dry-run | Don't upload files to Codecov | Optional
|--legacy, --use-legacy-uploader | Use the legacy upload endpoint | Optional
|--git-service | Git Provider. Options: github, gitlab, bitbucket, github_enterprise, gitlab_enterprise, bitbucket_server | Required
|-h, --help | Shows usage, and command options 

## create-report-results
`codecovcli create-report-results [OPTIONS]`

| Option  | Description | Usage
| :---:     |     :---:   |    :---:   | 
|--commit-sha | Commit SHA (with 40 chars) | Required
|--code | The code of the report. If unsure, leave default | Required
|--slug | owner/repo slug | Required
|--git-service | Git provider. Options: github, gitlab, bitbucket, github_enterprise, gitlab_enterprise, bitbucket_server | Optional
|-t, --token | Codecov upload token | Required
|-h, --help | Shows usage, and command options

## get-report-results
`codecovcli get-report-results [OPTIONS]`

| Option  | Description | Usage
| :---:     |     :---:   |    :---:   | 
|--commit-sha | Commit SHA (with 40 chars) | Required
|--code | The code of the report. If unsure, leave default | Required
|--slug | owner/repo slug | Required
|--git-service | Git provider. Options: github, gitlab, bitbucket, github_enterprise, gitlab_enterprise, bitbucket_server | Optional
|-t, --token | Codecov upload token | Required
|-h, --help | Shows usage, and command options

## pr-base-picking
`codecovcli pr-base-picking [OPTIONS]`

| Option  | Description | Usage
| :---:     |     :---:   |    :---:   | 
|--base-sha | Base commit SHA (with 40 chars) | Required
|--pr  | Pull Request id to associate commit with | Required
|--slug | owner/repo slug | Required
|-t, --token| Codecov upload token | Required
|--service | Git provider. Options: github, gitlab, bitbucket, github_enterprise, gitlab_enterprise, bitbucket_server | Optional
|-h, --help | Shows usage, and command options

## send-notifications 
`codecovcli send-notifications [OPTIONS]`

| Option  | Description | Usage
| :---:     |     :---:   |    :---:   | 
| -C, --sha, --commit-sha TEXT    |Commit SHA (with 40 chars) | Required
| -r, --slug TEXT                 |owner/repo slug used instead of the private repo token in Self-hosted | Required
| -t, --token TEXT                |Codecov upload token | Required
| --git-service | Git provider. Options: github, gitlab, bitbucket, github_enterprise, gitlab_enterprise, bitbucket_server | Optional
| -h,--help                      |Show this message and exit.

## empty-upload

Used if the changes made don't need testing, but PRs require a passing codecov status to be merged.
This command will scan the files in the commit and send passing status checks configured if all the changed files
are ignored by codecov (including README and configuration files)

`Usage: codecovcli empty-upload [OPTIONS]`

Options:
  -C, --sha, --commit-sha TEXT    Commit SHA (with 40 chars)  [required]
  -Z, --fail-on-error             Exit with non-zero code in case of error
  --git-service [github|gitlab|bitbucket|github_enterprise|gitlab_enterprise|bitbucket_server]
  -t, --token TEXT                Codecov upload token
  -r, --slug TEXT                 owner/repo slug used instead of the private
                                  repo token in Self-hosted
  -h, --help                      Show this message and exit.

# How to Use Local Upload

The CLI also supports "dry run" local uploading. This is useful if you prefer to see Codecov status checks and coverage reporting locally, in your terminal, as opposed to opening a PR and waiting for your full CI to run. Local uploads do not interfere with regular uploads made from your CI for any given commit / Pull Request. 

Local Upload is accomplished as follows:

```
pip install codecov-cli
codecovcli create-commit
codecovcli create-report --code <CODE>
codecovcli do-upload --report-code <CODE>
codecovcli create-report-results --code <CODE>
codecovcli get-report-results --code <CODE>
```

Codecov will calculate the coverage results, and return them in your terminal, telling you whether your PR will fail or pass the coverage check.

Note: In order for Local Upload to work, it must be used against a commit on the origin repository. Local Upload does not work for arbitrary diffs or uncommitted changes on your local machine. 

# Work in Progress Features

The following features are somewhat implemented in code, but are not yet meant for use. These features will be documented once they are fully implemented in the CLI. 

## Plugin System

To provide extensibility to some of its commands, the CLI makes use of a plugin system. For most cases, the default commands are sufficient. But in some cases, having some custom logic specific to your use case can be beneficial. Note that full documentation of the plugin system is pending, as the feature is still heavily a work in progress.

## Static Analysis

The CLI can perform basic static analysis on Python code today. This static analysis is meant to power more future looking Codecov features and, as such, is not required or in active use today. As more functionality dependent on static analysis becomes available for use, we will document static analysis in detail here. 

# Contributions

This repository, like all of Codecov's repositories, strives to follow our general [Contributing guidlines](https://github.com/codecov/contributing). If you're considering making a contribution to this repository, we encourage review of our Contributing guidelines first. 

## Requirements

Most of this package is a very conventional Python package. The main difference is the static the CLI's analysis module uses both git submodules and C code

Before installing, one should pull the submodules with:

```
git submodule update --init
```
Then, install dependencies with
```
pip install -r requirements.txt 
python setup.py develop
```

The C code shouldn't require any additional setup to get running, but depending on your environment, you may be prompted to install compilers and supporting tools. If errors are generated during installation, it is likely due to missing dependencies / tools required of the C code. In many cases, resulting error messages should be clear enough to determine what is missing and how to install it, but common errors will be collected here as they are encountered.

## Guidelines

There are a few guidelines when developing in this system. Some notable folders:

1. `commands` - It's the folder that interacts with the caller. This is where the commands themselves should reside. These commands are not meant to do heavy lifting. They only do wiring, which is mostly parsing the input parameters. 
2. `services` - It's where the heavy logic resides. It's mostly organized by which command needs them. Commands should generally be thin wrappers around these services.
3. `helpers` - This is meant for logic that is useful across different commands. For example, logging helpers, or the logic that searches folders.

## Dependencies

If external dependencies need to be added, it's important to check whether those dependencies have wheels available on PyPI with the `any` or `universal2` platform tags. If those dependencies don't have those wheels available, then they will need to built during the CI, so they will have to be added to the list of
dependencies in the `--no-binary` flag when building the requirements for the macos release in `build_assets.yml`.

# Releases

The standard way to making a new release is the following:
1)  Open a PR that increases the version number in setup.py. As a rule of thumb, just add one to the micro/patch version (e.g., v0.1.6 -> v0.1.7).

2) Get the up-to-date master branch locally and run the `tag.release` command from the Makefile.

`$ make tag.release version=v<VERSION_NUM>`

The version tag must match the regex defined on the Makefile (`tag_regex := ^v([0-9]{1,}\.){2}[0-9]{1,}([-_]\w+)?$`).

>**Note**: \
>Releases with `test` word in them are created as `draft`. \
>Releases with `beta` word in them are created as `pre-release`.
