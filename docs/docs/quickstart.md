# Quickstart Guide

This guide is structured as a tutorial that will walk you through creating
command-line applications with [clap-py](https://github.com/adityasz/clap-py).

It was adapted from the excellent
[tutorial](https://docs.rs/clap/latest/clap/_derive/_tutorial/index.html) for
[clap-rs](https://github.com/clap-rs/clap) using [Claude 4.0
Sonnet](https://www.anthropic.com/news/claude-4) in
[Cursor](https://www.cursor.com/) (and some manual cleaning by hand). Most text
is lifted verbatim.

## Quick Start

You can create an application declaratively with a class and some decorators.

Here is a preview of the type of application you can make:

```python
--8<-- "docs/docs/quickstart/01_quick.py"
```

<~-- output[python docs/docs/quickstart/01_quick.py --help] -->

By default, the program does nothing:

<~-- output[python docs/docs/quickstart/01_quick.py] -->

But you can mix and match the various features:

<~-- output[python docs/docs/quickstart/01_quick.py -dd test] -->

**See also:**

- The [tests](https://github.com/adityasz/clap-py/tree/master/tests) for more
  usage examples.
- The [examples](https://github.com/adityasz/clap-py/tree/master/examples) for
  more application-focused examples.

## Configuring the Parser

You use the [`@clap.command`][clap.command] decorator to start building a parser.

```python
--8<-- "docs/docs/quickstart/02_apps.py"
```

<~-- output[python docs/docs/quickstart/02_apps.py --help] -->

<~-- output[python docs/docs/quickstart/02_apps.py --version] -->

## Adding Arguments

1. [Positionals](#positionals)
2. [Options](#options)
3. [Flags](#flags)
4. [Optional](#optional)
5. [Defaults](#defaults)
6. [Subcommands](#subcommands)

Arguments are inferred from the fields of your class.

### Positionals

By default, class fields define positional arguments:

```python
--8<-- "docs/docs/quickstart/03_03_positional.py"
```

<~-- output[python docs/docs/quickstart/03_03_positional.py --help] -->

<~-- output[python docs/docs/quickstart/03_03_positional.py bob] -->

The `= arg()` assignment can be omitted, but then you need to be aware of the
[sharp edges](#sharp-edges).

Note that the default [`ArgAction`][clap.ArgAction] is
[`Set`][clap.ArgAction.Set]. To accept multiple values, use a [`list`][] type:

```python
--8<-- "docs/docs/quickstart/03_03_positional_mult.py"
```

<~-- output[python docs/docs/quickstart/03_03_positional_mult.py --help] -->

<~-- output[python docs/docs/quickstart/03_03_positional_mult.py] -->

<~-- output[python docs/docs/quickstart/03_03_positional_mult.py bob] -->

<~-- output[python docs/docs/quickstart/03_03_positional_mult.py bob john] -->

### Options

You can name your arguments with a flag:

- Intent of the value is clearer
- Order doesn't matter

To specify the flags for an argument, you can use [`arg()`][clap.arg] on a
field:

- To automatically generate flags, [`short`][clap.short] and
  [`long`][clap.long] can be used: `arg(short, long)`.
    - `arg(short=True, long=True)` can also be used.
- To specify the flags manually:
    - `arg(short="n", long="name")`.

!!! note
    [`arg()`][clap.arg] takes up to two
    [positional-only](https://peps.python.org/pep-0570/) paramters of type
    [`AutoFlag`][clap.core.AutoFlag], and [`short`][clap.short] and
    [`long`][clap.long] are aliases for
    [`AutoFlag.Short`][clap.core.AutoFlag.Short] and
    [`AutoFlag.Long`][clap.core.AutoFlag.Long]. These are used to automatically
    generate flags.

    It also takes [keyword-only](https://peps.python.org/pep-3102/) arguments
    named `short` and `long`. These are used for manually specifying the flags.

```python
--8<-- "docs/docs/quickstart/03_02_option.py"
```

<~-- output[python docs/docs/quickstart/03_02_option.py --help] -->

<~-- output[python docs/docs/quickstart/03_02_option.py --name bob] -->

<~-- output[python docs/docs/quickstart/03_02_option.py --name=bob] -->

<~-- output[python docs/docs/quickstart/03_02_option.py -n bob] -->

<~-- output[python docs/docs/quickstart/03_02_option.py -n=bob] -->

<~-- output[python docs/docs/quickstart/03_02_option.py -nbob] -->

Note that the default [`ArgAction`][clap.ArgAction] is
[`Set`][clap.ArgAction.Set]. To accept multiple occurrences, override the action
with [`Append`][clap.ArgAction.Append] via [`list`][]:

```python
--8<-- "docs/docs/quickstart/03_02_option_mult.py"
```

<~-- output[python docs/docs/quickstart/03_02_option_mult.py --help] -->

<~-- output[python docs/docs/quickstart/03_02_option_mult.py] -->

<~-- output[python docs/docs/quickstart/03_02_option_mult.py --name bob] -->

<~-- output[python docs/docs/quickstart/03_02_option_mult.py --name bob --name john] -->

<~-- output[python docs/docs/quickstart/03_02_option_mult.py --name bob --name=john -n tom -n=chris -nsteve] -->

### Flags

Flags can also be switches that can be on/off:

```python
--8<-- "docs/docs/quickstart/03_01_flag_bool.py"
```

<~-- output[python docs/docs/quickstart/03_01_flag_bool.py --help] -->

<~-- output[python docs/docs/quickstart/03_01_flag_bool.py] -->

<~-- output[python docs/docs/quickstart/03_01_flag_bool.py --verbose] -->

Note that the default [`ArgAction`][clap.ArgAction] for a `bool` field is
[`SetTrue`][clap.ArgAction.SetTrue]. To accept multiple flags, override the
[action][clap.arg] with [`Count`][clap.ArgAction.Count]:

```python
--8<-- "docs/docs/quickstart/03_01_flag_count.py"
```

<~-- output[python docs/docs/quickstart/03_01_flag_count.py --help] -->

<~-- output[python docs/docs/quickstart/03_01_flag_count.py] -->

<~-- output[python docs/docs/quickstart/03_01_flag_count.py --verbose] -->

<~-- output[python docs/docs/quickstart/03_01_flag_count.py --verbose --verbose] -->

### Optional

By default, arguments are assumed to be required. To make an argument optional,
you can either use [PEP 604](https://peps.python.org/pep-0604/) annotations, or
wrap the field's type in [`Optional`][typing.Optional]:

```python
--8<-- "docs/docs/quickstart/03_06_optional.py"
```

<~-- output[python docs/docs/quickstart/03_06_optional.py --help] -->

<~-- output[python docs/docs/quickstart/03_06_optional.py] -->

<~-- output[python docs/docs/quickstart/03_06_optional.py bob] -->

### Defaults

We've previously showed that arguments can be required or optional. When
optional, you work with an [`Optional`][typing.Optional] and can use `or` or
provide a default value. Alternatively, you can set [`default_value`][clap.arg].

```python
--8<-- "docs/docs/quickstart/03_05_default_values.py"
```

<~-- output[python docs/docs/quickstart/03_05_default_values.py --help] -->

<~-- output[python docs/docs/quickstart/03_05_default_values.py] -->

<~-- output[python docs/docs/quickstart/03_05_default_values.py 22] -->

### Subcommands

Subcommands are created with [`@clap.subcommand`][clap.subcommand] and added via
a type annotation to a field that will contain the parsed result. If there are
multiple subcommands, use [`Union`][typing.Union] or
[PEP 604](https://peps.python.org/pep-0604/) annotations. Each instance of a
subcommand can have its own version, author(s), arguments, and even its own
subcommands.

```python
--8<-- "docs/docs/quickstart/03_04_subcommands.py"
```

<~-- output[python docs/docs/quickstart/03_04_subcommands.py --help] -->

<~-- output[python docs/docs/quickstart/03_04_subcommands.py add --help] -->

<~-- output[python docs/docs/quickstart/03_04_subcommands.py add bob] -->

To make a subcommand optional, add a `| None` or wrap it in an `Optional` (e.g.
`command: Optional[Add]`).

!!! note
    
    Due to type checking limitations, the subcommand needs to be the first field
    in the class even though it is specified after all other arguments in the
    command-line, unless you assign an object of a compatible type to it:
    See [sharp edges](#sharp-edges) below.

Since we specified `propagate_version=True`, the `--version` flag is available
in all subcommands:

<~-- output[python docs/docs/quickstart/03_04_subcommands.py --version] -->

<~-- output[python docs/docs/quickstart/03_04_subcommands.py add --version] -->

## Validation

1. [Enumerated values](#enumerated-values)
2. [Argument Relations](#argument-relations)
3. [Custom Validation](#custom-validation)

An appropriate default parser/validator will be selected for the field's type.

### Enumerated values

For arguments with specific values you want to test for, you can use Python's
`Enum`. This allows you to specify the valid values for that argument. If the
user does not use one of those specific values, they will receive a graceful
exit with error message informing them of the mistake, and what the possible
valid values are.

```python
--8<-- "docs/docs/quickstart/04_01_enum.py"
```

<~-- output[python docs/docs/quickstart/04_01_enum.py --help] -->

<~-- output[python docs/docs/quickstart/04_01_enum.py -h] -->

<~-- output[python docs/docs/quickstart/04_01_enum.py fast] -->

<~-- output[python docs/docs/quickstart/04_01_enum.py slow] -->

### Argument Relations

!!! note

    Advanced argument relations and dependencies like `requires` and
    `conflicts_with` are not yet implemented. You can use [`Group`][clap.Group]
    for basic grouping and mutual exclusion.

```python
--8<-- "docs/docs/quickstart/04_02_groups.py"
```

<~-- output[python docs/docs/quickstart/04_02_groups.py --help] -->

<~-- output[python docs/docs/quickstart/04_02_groups.py --major] -->

<~-- output[python docs/docs/quickstart/04_02_groups.py --set-ver 1.2.5] -->

<~-- output[python docs/docs/quickstart/04_02_groups.py --major --minor] -->

### Custom Validation

As a last resort, you can create custom validation logic in your application after parsing:

```python
--8<-- "docs/docs/quickstart/04_04_custom.py"
```

<~-- output[python docs/docs/quickstart/04_04_custom.py --help] -->

<~-- output[python docs/docs/quickstart/04_04_custom.py --major] -->

<~-- output[python docs/docs/quickstart/04_04_custom.py --major -c config.toml --spec-in input.txt] -->

## Docstrings

```python
import clap

@clap.command
class Cli(clap.Parser):
    """This is the short about (without the trailing period).

    Any subsequent paragraphs are ignored in the short about. The long about
    contains the entire docstring.
    """

    input: str = arg()
    """Help messages are generated in a similar way.
    Ellipsis are kept in the short help...

    Paragraphs are separated by at least two newlines.
    """
```

Docstrings are processed just like
[`clap-rs`](https://docs.rs/clap/latest/clap/_derive/index.html#doc-comments).

## Help Output

See [`ArgAction.Help`][clap.ArgAction.Help],
[`ArgAction.HelpLong`][clap.ArgAction.HelpLong], and
[`ArgAction.HelpShort`][clap.ArgAction.HelpShort].

A custom [template][clap.HelpTemplate] can be used, and styles can be customized
using [`Styles`][clap.Styles].

Here's the help output for
[`examples/typst.py`](https://github.com/adityasz/clap-py/tree/master/examples/typst.py):

<~-- output[python examples/typst.py --help] -->

<~-- output[python examples/typst.py watch -h] -->

<~-- output[python examples/typst.py watch --help] -->

## Sharp edges

The decorators [`@clap.command`][clap.command], [`@clap.group`][clap.group], and
[`@clap.subcommand`][clap.subcommand] are decorated with
[`@dataclass_transform`][typing.dataclass_transform] to tell type checkers that
they provide [`dataclass`][dataclasses.dataclass]-like functionality (for
example, pattern matching with positionals in `match`-`case`).

This also brings some dataclass limitations: If fields without default values
are present after fields with default values, type checkers will complain. There
are no runtime implications, but to satisfy the type checkers, the following
(reasonable) workarounds can be used:

- For positionals where you don't need to modify the default behavior, you can
  simply assign `arg()` if there are fields with default values above, even
  though the runtime behavior does not change. In the examples above, I always
  did this, even when it was not required, because it makes the intent clearer,
  especially when the type is a custom class like `Foo`: `foo: Foo` may be an
  argument group, a subcommand, or an argument, while `foo: Foo =
  arg()` can only be an argument.

- If a field that contains the subcommand, make it the first field. (The order
  only matters for positionals; the subcommand is always parsed after all the
  positionals and options.)
  
    While I would have preferred a solution where it is at the bottom, I do not
    want to add a dummy function returning `Any` to the API. There exist
    workarounds, though: If the subcommand is optional, you can assign `None` to
    it. Alternatively, if you have something like `command: A | B | C`, you can
    assign an object of any one of these types to it: `command: A | B | C =
    A()`. The value is ignored by the library. Note that if the subcommand class
    `A` has a field without a default value (e.g., `num: int`, where you do not
    want to modify any attributes), you will have to assign a default to it
    (e.g., `num: int = arg()`).

- For argument [groups][clap.group], you can call the constructor without any
  arguments and assign that, e.g.:
  ```python
  input_opts: InputOpts = InputOpts()
  ```
  Argument groups are generally used for options. However, if an argument group
  has a positional argument without an `= arg()` (i.e., you want the default
  properties), the type checker will complain since that field does not have a
  default value and must be initialized in the constructor (since it cannot see
  that a dummy `__init__` is injected at runtime that will make it possible).
  So, you can just assign `= arg()` to it, just like in the first point above.

Before (works at runtime, but static type checkers do not like it):
```python
@clap.subcommand
class FooA:
    foo_a: int

@clap.subcommand
class FooB:
    foo_b: int

@clap.group
class Stuff:
    foo_c: int
    foo_d: bool = arg(long)

@clap.command
class Cli(clap.Parser):
    foo_e: int = arg(value_name="N")
    foo_f: int
    more: Stuff
    command: FooA | FooB
```

After:
```python
@clap.subcommand
class FooA:
    foo_a: int

@clap.subcommand
class FooB:
    foo_b: int

@clap.group
class Stuff:
    foo_c: int = arg()
    foo_d: bool = arg(long)

@clap.command
class Cli(clap.Parser):
    command: FooA | FooB
    foo_e: int = arg(value_name="N")
    foo_f: int = arg()
    more: Stuff = Stuff()
```

The changes are very minimal, and only make the code clearer:
```diff
  @clap.subcommand
  class FooA:
      foo_a: int
  
  @clap.subcommand
  class FooB:
      foo_b: int
    
  @clap.group
  class Stuff:
-     foo_c: int
+     foo_c: int = arg()
      foo_d: bool = arg(long)


  @clap.command
  class Cli(clap.Parser):
+     command: FooA | FooB
      foo_e: int = arg(value_name="N")
-     foo_f: int
+     foo_f: int = arg()
-     more: Stuff
+     more: Stuff = Stuff()
-     command: FooA | FooB
```

**See also:**

- [API Reference](https://adityasz.github.io/clap-py/) for complete
  documentation.
- [Examples](https://github.com/adityasz/clap-py/tree/master/examples) for
  application-focused examples.
