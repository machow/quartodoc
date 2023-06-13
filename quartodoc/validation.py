
def fmt(err:dict):
    "format error messages from pydantic."
    msg = ""
    if err['msg'].startswith('Discriminator'):
        return msg
    if err['type'] == 'value_error.missing':
        msg += 'Missing field'
    else:
        msg += err['msg'] + ':'
        
    if 'loc' in err:
        if len(err['loc']) == 1:
            msg += f" from root level: `{err['loc'][0]}`"
        elif len(err['loc']) == 3:
            msg += f" `{err['loc'][2]}` for element {err['loc'][1]} in the list for `{err['loc'][0]}`"
                
    else:
        msg += str(err['msg'])
    return msg
