---
skill_group: platform:huggingface
skill_category: huggingface
---
Install: `curl -LsSf https://hf.co/cli/install.sh | bash -s`.

The Hugging Face Hub CLI tool `hf` is available. IMPORTANT: The `hf` command replaces the deprecated `huggingface-cli` command.

Use `hf --help` to view available functions. Note that auth commands are now all under `hf auth` e.g. `hf auth whoami`.

Generated with `huggingface_hub v1.6.0`. Run `hf skills add --force` to regenerate.

## Commands

- `hf download REPO_ID` — Download files from the Hub.
- `hf env` — Print information about the environment.
- `hf sync` — Sync files between local directory and a bucket.
- `hf upload REPO_ID` — Upload a file or a folder to the Hub. Recommended for single-commit uploads.
- `hf upload-large-folder REPO_ID LOCAL_PATH` — Upload a large folder to the Hub. Recommended for resumable uploads.
- `hf version` — Print information about the hf version.

### `hf auth` — Manage authentication (login, logout, etc.).

- `hf auth list` — List all stored access tokens.
- `hf auth login` — Login using a token from huggingface.co/settings/tokens.
- `hf auth logout` — Logout from a specific token.
- `hf auth switch` — Switch between access tokens.
- `hf auth whoami` — Find out which huggingface.co account you are logged in as.

### `hf buckets` — Commands to interact with buckets.

- `hf buckets cp SRC` — Copy a single file to or from a bucket.
- `hf buckets create BUCKET_ID` — Create a new bucket.
- `hf buckets delete BUCKET_ID` — Delete a bucket.
- `hf buckets info BUCKET_ID` — Get info about a bucket.
- `hf buckets list` — List buckets or files in a bucket.
- `hf buckets move FROM_ID TO_ID` — Move (rename) a bucket to a new name or namespace.
- `hf buckets remove ARGUMENT` — Remove files from a bucket.
- `hf buckets sync` — Sync files between local directory and a bucket.

### `hf cache` — Manage local cache directory.

- `hf cache ls` — List cached repositories or revisions.
- `hf cache prune` — Remove detached revisions from the cache.
- `hf cache rm TARGETS` — Remove cached repositories or revisions.
- `hf cache verify REPO_ID` — Verify checksums for a single repo revision from cache or a local directory.

### `hf collections` — Interact with collections on the Hub.

- `hf collections add-item COLLECTION_SLUG ITEM_ID ITEM_TYPE` — Add an item to a collection.
- `hf collections create TITLE` — Create a new collection on the Hub.
- `hf collections delete COLLECTION_SLUG` — Delete a collection from the Hub.
- `hf collections delete-item COLLECTION_SLUG ITEM_OBJECT_ID` — Delete an item from a collection.
- `hf collections info COLLECTION_SLUG` — Get info about a collection on the Hub.
- `hf collections ls` — List collections on the Hub.
- `hf collections update COLLECTION_SLUG` — Update a collection's metadata on the Hub.
- `hf collections update-item COLLECTION_SLUG ITEM_OBJECT_ID` — Update an item in a collection.

### `hf datasets` — Interact with datasets on the Hub.

- `hf datasets info DATASET_ID` — Get info about a dataset on the Hub.
- `hf datasets ls` — List datasets on the Hub.
- `hf datasets parquet DATASET_ID` — List parquet file URLs available for a dataset.
- `hf datasets sql SQL` — Execute a raw SQL query with DuckDB against dataset parquet URLs.

### `hf discussions` — Manage discussions and pull requests on the Hub.

- `hf discussions close REPO_ID NUM` — Close a discussion or pull request.
- `hf discussions comment REPO_ID NUM` — Comment on a discussion or pull request.
- `hf discussions create REPO_ID title` — Create a new discussion or pull request on a repo.
- `hf discussions diff REPO_ID NUM` — Show the diff of a pull request.
- `hf discussions info REPO_ID NUM` — Get info about a discussion or pull request.
- `hf discussions list REPO_ID` — List discussions and pull requests on a repo.
- `hf discussions merge REPO_ID NUM` — Merge a pull request.
- `hf discussions rename REPO_ID NUM NEW_TITLE` — Rename a discussion or pull request.
- `hf discussions reopen REPO_ID NUM` — Reopen a closed discussion or pull request.

### `hf endpoints` — Manage Hugging Face Inference Endpoints.

- `hf endpoints catalog` — Interact with the Inference Endpoints catalog.
- `hf endpoints delete NAME` — Delete an Inference Endpoint permanently.
- `hf endpoints deploy NAME repo framework accelerator instance_size instance_type region vendor` — Deploy an Inference Endpoint from a Hub repository.
- `hf endpoints describe NAME` — Get information about an existing endpoint.
- `hf endpoints ls` — Lists all Inference Endpoints for the given namespace.
- `hf endpoints pause NAME` — Pause an Inference Endpoint.
- `hf endpoints resume NAME` — Resume an Inference Endpoint.
- `hf endpoints scale-to-zero NAME` — Scale an Inference Endpoint to zero.
- `hf endpoints update NAME` — Update an existing endpoint.

### `hf extensions` — Manage hf CLI extensions.

- `hf extensions exec NAME` — Execute an installed extension.
- `hf extensions install REPO_ID` — Install an extension from a public GitHub repository.
- `hf extensions list` — List installed extension commands.
- `hf extensions remove NAME` — Remove an installed extension.

### `hf jobs` — Run and manage Jobs on the Hub.

- `hf jobs cancel JOB_ID` — Cancel a Job
- `hf jobs hardware` — List available hardware options for Jobs
- `hf jobs inspect JOB_IDS` — Display detailed information on one or more Jobs
- `hf jobs logs JOB_ID` — Fetch the logs of a Job.
- `hf jobs ps` — List Jobs.
- `hf jobs run IMAGE COMMAND` — Run a Job.
- `hf jobs scheduled` — Create and manage scheduled Jobs on the Hub.
- `hf jobs stats` — Fetch the resource usage statistics and metrics of Jobs
- `hf jobs uv` — Run UV scripts (Python with inline dependencies) on HF infrastructure.

### `hf models` — Interact with models on the Hub.

- `hf models info MODEL_ID` — Get info about a model on the Hub.
- `hf models ls` — List models on the Hub.

### `hf papers` — Interact with papers on the Hub.

- `hf papers ls` — List daily papers on the Hub.

### `hf repos` — Manage repos on the Hub.

- `hf repos branch` — Manage branches for a repo on the Hub.
- `hf repos create REPO_ID` — Create a new repo on the Hub.
- `hf repos delete REPO_ID` — Delete a repo from the Hub. This is an irreversible operation.
- `hf repos delete-files REPO_ID PATTERNS` — Delete files from a repo on the Hub.
- `hf repos duplicate FROM_ID` — Duplicate a repo on the Hub (model, dataset, or Space).
- `hf repos move FROM_ID TO_ID` — Move a repository from a namespace to another namespace.
- `hf repos settings REPO_ID` — Update the settings of a repository.
- `hf repos tag` — Manage tags for a repo on the Hub.

### `hf skills` — Manage skills for AI assistants.

- `hf skills add` — Download a skill and install it for an AI assistant.
- `hf skills preview` — Print the generated SKILL.md to stdout.

### `hf spaces` — Interact with spaces on the Hub.

- `hf spaces dev-mode SPACE_ID` — Enable or disable dev mode on a Space.
- `hf spaces hot-reload SPACE_ID` — Hot-reload any Python file of a Space without a full rebuild + restart.
- `hf spaces info SPACE_ID` — Get info about a space on the Hub.
- `hf spaces ls` — List spaces on the Hub.

### `hf webhooks` — Manage webhooks on the Hub.

- `hf webhooks create watch` — Create a new webhook.
- `hf webhooks delete WEBHOOK_ID` — Delete a webhook permanently.
- `hf webhooks disable WEBHOOK_ID` — Disable an active webhook.
- `hf webhooks enable WEBHOOK_ID` — Enable a disabled webhook.
- `hf webhooks info WEBHOOK_ID` — Show full details for a single webhook as JSON.
- `hf webhooks list` — List all webhooks for the current user.
- `hf webhooks update WEBHOOK_ID` — Update an existing webhook. Only provided options are changed.

## Tips

- Use `hf <command> --help` for full options, usage, and real-world examples
- Use `--format json` for machine-readable output on list commands
- Use `-q` / `--quiet` to print only IDs
- Authenticate with `HF_TOKEN` env var (recommended) or with `--token`
