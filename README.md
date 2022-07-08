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

WIP