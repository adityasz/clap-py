from enum import StrEnum
from typing import override


# This is super ugly, but far better than the `raise TypeError`s that I had
# before. When I write my own parser to replace argparse, I will implement a
# better diagnostics system with source ranges, highlights, etc. that handles
# both invalid arguments and parser declaration related diagnostics.
class TODO(StrEnum):
    @override
    def format(self, *args, **kwargs) -> str:
        return self.value.format(**kwargs)


class Diagnostics(TODO):
    ParserNotDecorated = (
        "Decorate {cls} with @clap.command to use the parse() method.\n{args}"
    )
    InvalidNumArgs = "The tuple has {n} values but 'num_args' is set to {num_args}."
    InvalidFlag = "This string is not a valid flag."
    TypeHintParsingFailed = "Could not parse the type hint."
    UnionOnlyForSubcommands = "Unions can only contain subcommands."
    CannotExtractEnumChoices = "Cannot uniquely extract choices from this enum."
    CountActionNeverNone = (
        "An argument with the 'count' action cannot be None. If no default is "
        "provided, it is set to 0."
    )
    InvalidValue = "The value '{value}' cannot be assigned to this field."
    RequiredTrueNeverNone = "An argument with 'required=True' can never be None."
    DefaultValueNeverNone = "An argument with a default value can never be None."
    SetFalseNeverNone = "An argument with the SetFalse action can never be None."
    SetTrueNeverNone = "An argument with the SetTrue action can never be None."
    SubcommandDestAlreadySet = "The field {field} is already declared to contain the subcommand."
    SubcommandDestInvalidType = (
        "{field} contains the subcommand as per the type annotation. "
        "Cannot assign {value} to it."
    )
    GroupDestInvalidType = (
        "{field} is a group based on the annotation. Cannot assign {value} to it."
    )
    GroupCanOnlyHaveArgs = (
        "A group can only contain arguments. {value} cannot be assigned to an argument."
    )
    DuplicateGroupTitle = (
        "A group with title '{title}' and the same description already exists."
    )
    TypeContainsSubcommandEtAl = (
        "Type annotation contains a mixture of subcommands and other types."
    )
    UnknownError = (
        "An unknown error occurred. Please file a bug report containing a minimal example."
    )

    class UnimplementedFeatures(TODO):
        CustomNumArgs = (
            "argparse limitation: Please use `num_args='*'` "
            "with manual validation until I write my own parser."
        )
        NestedGroups = "Nested groups are not supported."
        HeterogeneousTuples = "Heterogenous tuples are not supported."
        GroupRequiredTrue = (
            "Currently, `required = True` only works when `multiple` is set to `False`. "
            "Consider restructuring the parser or doing manual validation."
        )
