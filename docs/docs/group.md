# Group

::: clap.group

Nesting groups is not allowed. However, sometimes, a group may have some
arguments that have to be mutually exclusive. In this case,
[`Group`][clap.Group] can be used to create a group field, i.e., `group =
Group(required=True, multiple=False)`, and those arguments can have this as
their group: `verbose: bool = arg(long, group=group)`, `quiet: bool = arg(long,
group=group)`. In the future, I will add a `conflicts_with` argument to
[`arg`][clap.arg], which will be more general than this workaround.

::: clap.Group
