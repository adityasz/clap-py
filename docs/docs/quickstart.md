# Quickstart Guide

This guide is structured as a tutorial.

!!! note

    **This guide is under development.**
    In the meantime, see [examples](https://github.com/adityasz/clap-py/tree/master/examples)
    and [tests](https://github.com/adityasz/clap-py/tree/master/tests).

## Adding arguments

- Each argument field must have a type annotation.
- Fields without type annotations are ignored, unless it is a
  [(mutually exclusive)][clap.models.MutexGroup] [group][clap.models.Group].
- Flags need to be generated using [`arg()`][clap.arg]. If an arg does not have
  flags, it is a positional argument.
  - To automatically generate flags, [`short`][clap.short] and
    [`long`][clap.long] can be used:

    ```python
    import clap
    from clap import arg, long, short

    @clap.command
    class Cli:
        verbose: bool = arg(short, long)
    ```

  - `arg(short=True, long=True)` can also be used.

## Docstrings

```python
import clap

@clap.command
class Cli(clap.Parser):
    """This is the short help (without the trailing period).

    Any subsequent paragraphs are ignored in the short help. The long help
    contains the entire docstring."""

    input: str
    """The same holds for args."""
```

Docstrings are processed just like
[`clap-rs`](https://docs.rs/clap/latest/clap/_derive/index.html#doc-comments).

## Help

Depending on the help flag, short (`-h`) or long (`--help`) help is output. See [`ArgAction`][clap.ArgAction]. A custom template can be used (TODO: docs), and styles can be customized using [`Styles`][clap.Styles].

Here's the help output for
[typst.py](https://github.com/adityasz/clap-py/tree/master/examples/typst.py):

TODO: ANSI -> HTML
