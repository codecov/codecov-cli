- [Installing](#installing)
- [Running the upload command](#running-the-upload-command)
- [Running other commands](#running-other-commands)
- [Plugin System](#plugin-system)
- [Development](#development)
  - [Requirements](#requirements)
  - [Guidelines](#guidelines)
- [Releases](#releases)

# Installing

To install this package locally, you can run

`python setup.py develop`

If you are installing from somewhere else, you can add:

```
codecov-cli @ git+ssh://git@github.com/codecov/codecov-cli.git@commitsha
```

to its requirements file

# Running the upload command

To run the CLI, do:

```
codecovcli --auto-load-params-from circleci do-upload
```

and pass parameters as you see fit. You can get help on

```
codecovcli --help
```

and

```
codecovcli do-upload --help
```

# Running other commands

There are many nested commands here.

# Plugin System

In some of the commands, there is a plugin system. For most cases, one might find that changing them is not really needed. But in some cases, have some custom logic run would be beneficial

WIP

# Development

## Requirements

To start, most of this package is a normal Python package. The main different thing is the static analysis tool that uses both git submodules and c code

Before installing, one should pull the submodules with

```
git submodule update --init
```

The c code shouldn't require anything on most places, but it might ask you to install compilers and stuff. Most of the times you can find the instructions online given the error messsage

## Guidelines

There are a few guidelines when developing in this systems. We have a few notable folders:

1. `commands` - It's the folder that interacts with the caller. This is where the commands themselves should live. They are not meant to do heavy lifting. They only do wiring, which is mostly parsing the input parameters
2. `services` - It's where the heavy logic lives. It's mostly organizaed by which command needs them.
3. `helpers` - This is meant for logic that is probably useful accross different commands. For example, logging helpers, or the logic the searches folders

# Releases

The standard way to making a new release is to get the up-to-date master branch locally and run the `tag.release` command from the Makefile.

`$ make tag.release version=v0.1.1`

The version tag must match the regex defined on the Makefile (`tag_regex := ^v([0-9]{1,}\.){2}[0-9]{1,}([-_]\w+)?$`).
Also keep in mind:
* Releases with `test` word in them are created as `draft` 
* Releases with `beta` work in them are created as `pre-release`
