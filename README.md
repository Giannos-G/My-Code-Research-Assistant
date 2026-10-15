# My Code Research Assistant

An agent that answers "how is this implemented?" questions by searching
real code on GitHub and the live web, then citing what it found. It also
keeps a local history of past research so you can ask "what did I look up
about X before?".

## How it works

- **Brain:** [GitHub Models](https://github.com/marketplace/models) (free
  tier), accessed through the OpenAI-compatible API, with tool-calling.
- **Code search:** the hosted
  [GitHub MCP server](https://github.com/github/github-mcp-server)
  (`https://api.githubcopilot.com/mcp/`), scoped to read-only
  `context,repos,code_search` toolsets — it can search and read code across
  any public repo you mention.
- **Web search:** the hosted [Exa](https://exa.ai) MCP server, for docs,
  blog posts, and discussions that aren't on GitHub.
- **Memory:** a local SQLite file (`data/research.db`) logging every
  question/answer, queryable via a `list_past_research` tool.
- **Interface:** a simple command-line chat loop.

This agent connects to *two* MCP servers at once and merges their tools
into a single tool list for the model — a step up in complexity from a
single-MCP agent.

## Setup

1. Install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in:
   - `GITHUB_MODELS_TOKEN`: a fine-grained GitHub PAT with the **Models**
     permission.
   - `GITHUB_MCP_TOKEN`: a classic GitHub PAT with the `repo` scope, used to
     authenticate to the GitHub MCP server. This can be the same or a
     different token from `GITHUB_MODELS_TOKEN` — they need different
     permission types, so a single fine-grained token usually won't satisfy
     both.
   - `EXA_API_KEY`: an API key from [exa.ai](https://exa.ai).

   Either token can be omitted to run with just one search source; the
   agent still works with whichever MCP server(s) are configured.

3. Run it:

   ```bash
   python main.py
   ```

## Example usage

```
you> how does the requests library handle retries?
assistant> It uses urllib3's Retry class... (searched psf/requests on GitHub)

you> what did I ask about before regarding retries?
assistant> You previously asked how the requests library handles retries...
```

## Project structure

```
main.py                  # entry point
assistant/
  agent.py                # chat loop + GitHub Models tool-calling
  mcp_client.py           # connects to multiple MCP servers, merges their tools
  tools.py                # the local research-history tool
  db.py                   # SQLite research history log
data/                      # SQLite database (gitignored)
```

## Notes on free tiers

- GitHub Models' free tier has rate limits per model; see the
  [GitHub Models docs](https://docs.github.com/en/github-models).
- The GitHub MCP server is free to use with a personal access token, subject
  to normal GitHub API rate limits.
- Exa's free tier has a limited number of monthly searches; see
  [exa.ai](https://exa.ai) for current pricing.
