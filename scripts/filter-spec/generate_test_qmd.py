#%%
from quartodoc.tests.test_interlinks import spec
from quartodoc import preview


# %%
spec

# %%

template = """
## {input}

output: {output}

```
{preview}
```
"""

# # {input}
# output: {output}
# 
# {preview of entry}
results = []
for ii, entry in enumerate(spec):
    results.append(template.format(
        input = "`` " + entry.input + " ``",
        output = entry.input,
        preview = preview(entry, as_string=True)
    )
    )

final = "\n\n\n".join(results)


# %%
