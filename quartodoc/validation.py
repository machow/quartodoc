"""User-friendly messages for configuration validation errors.

This module has largely two goals:

* Show the most useful error (pydantic starts with the highest, broadest one).
* Make the error message very user-friendly.

The key dynamic for understanding formatting is that pydantic is very forgiving.
It will coerce values to the target type, and by default allows extra fields.
Critically, if you have a union of types, it will try each type in order until it
finds a match. In this case, it reports errors for everything it tried.

For example, consider this config:

quartodoc:
    package: zzz
    sections:
    - title: Section 1
      contents:
        # name missing here ----
        - children: linked

In this case, the first element of contents is missing a name field.  Since the
first type in the union for content elements is _AutoDefault, that is what it
tries (and logs an error about name). However, it then goes down the list of other
types in the union and logs errors for those (e.g. Doc). This produce a lot of
confusing messages, because nowhere does it make clear what type its trying to create.

We don't want error messages for everything it tried, just the first type in the union.
(For a discriminated union, it uses the `kind:` field to know what the first type to try is).
"""


def fmt_all(e):
    # if not pydantic.__version__.startswith("1."):
    #    # error reports are much better in pydantic v2
    #    # so we just use those.
    #    return str(e)

    errors = [fmt(err) for err in e.errors() if fmt(err)]

    # the last error is the most specific, while earlier ones can be
    # for alternative union types that didn't work out.
    main_error = errors[0]

    msg = f"Configuration error for YAML:\n - {main_error}"
    return msg


def fmt(err: dict):
    "format error messages from pydantic."

    # each entry of loc is a new level in the config tree
    # 0 is root
    # 1 is sections
    # 2 is a section entry
    # 3 is contents
    # 4 is a content item
    # 5 might be Auto.members, etc..
    # 6 might be an Auto.members item

    # type: value_error.discriminated_union.missing_discriminator
    # type: value_error.missing
    # type: value_error.extra
    msg = ""
    if err["msg"].startswith("Discriminator"):
        return msg
    if err["type"] == "value_error.missing":
        msg += "Missing field"
    else:
        msg += err["msg"] + ":"

    if "loc" in err:
        if len(err["loc"]) == 1:
            msg += f" from root level: `{err['loc'][0]}`"
        elif len(err["loc"]) == 3:
            msg += f" `{err['loc'][2]}` for element {err['loc'][1]} in the list for `{err['loc'][0]}`"
        elif len(err["loc"]) == 4 and err["loc"][2] == "Page":
            msg += f" `{err['loc'][3]}` for element {err['loc'][1]} in the list for `{err['loc'][0]}`, which you need when setting `kind: page`."
        elif len(err["loc"]) == 5:
            msg += f" `{err['loc'][4]}` for element {err['loc'][3]} in the list for `{err['loc'][2]}` located in element {err['loc'][1]} in the list for `{err['loc'][0]}`"
        elif len(err["loc"]) == 6 and err["loc"][4] == "Auto":
            msg += f" `{err['loc'][5]}` for element {err['loc'][3]} in the list for `{err['loc'][2]}` located in element {err['loc'][1]} in the list for `{err['loc'][0]}`"
        else:
            return str(err)  # so we can debug and include more cases
    else:
        msg += str(err)
    return msg
