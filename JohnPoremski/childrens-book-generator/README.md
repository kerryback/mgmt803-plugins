# childrens-book-generator

Scaffold and run a FastAPI app that turns a character, art style, and moral of
the story into a short illustrated children's picture book.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install childrens-book-generator@mgmt803
```

Then say what you want, e.g. "make a children's book about a fox who learns
to share."

## What it does

Fill in a character (name + description), an art style, a moral, and a few
optional extras (setting, age range, supporting characters, tone, page count,
rhyming on/off). The app writes plot beats page by page and generates a
matching illustration for each one, chaining the first illustration back in
as a reference for later pages so the character and style stay consistent
instead of drifting. Finished books are saved and can be reopened or
downloaded as a PDF.

## Requirements

`OPENAI_API_KEY` set to an OpenRouter key (story text uses OpenRouter chat
completions; illustrations use OpenRouter's separate image endpoint, which
needs OpenRouter account credits even when chat completions don't).
