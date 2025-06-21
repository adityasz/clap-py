# Quickstart Guide

This guide is structured as a tutorial.

!!! note

    **WIP**.
    See [examples](https://github.com/adityasz/clap-py/tree/master/examples)
    and [tests](https://github.com/adityasz/clap-py/tree/master/tests).

## Adding arguments

- Each argument field must have a type annotation.
- Fields without type annotations are ignored.
- Flags need to be generated using [`clap.arg`][]. If an arg does not have flags, it is
  a positional argument.
  - To automatically generate flags, [`clap.short`][] and [`clap.long`][] can be used.
    These are positional-only arguments to [`clap.arg`][]:

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
    """This is the short help.

    Any subsequent paragraphs are ignored in the short help. The long help
    contains the entire docstring."""

    input: str
    """The same holds for args."""
```

Docstrings are processed just like
[`clap-rs`](https://docs.rs/clap/latest/clap/_derive/index.html#doc-comments).
