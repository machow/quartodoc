def fmt(err: dict):
    "format error messages from pydantic."
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
