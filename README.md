# fuck ~~45~~ 47

<!-- TODO: description -->

<!-- TODO: minimum requirements -->
## Minimum Requirements

<!-- TODO: recommended requirements -->
## Recommended Requirements

<!-- TODO: quickstart -->
## Quickstart

<!-- TODO: development -->
## Development

### Claude Code

After generating a product requirements document (PRD), Claude Code can generate a codebase.

To generate a PRD:

> Use @docs/create-prd.mdc
> Here's the feature I want to build: [Describe your feature in detail]
> Reference these files to help you: [Optional: @file1.py @file2.ts]

To generate a task list:

> Now take @docs/your-feature-prd.md and create tasks using @docs/generate-tasks.mdc

For each task, prompt Claude Code to iterate over the specific tasks:

> Please start on task 1.1 and use @docs/process-task-list.mdc

## TODO

See the [TODO.md](TODO.md) file for the current list of tasks.

## Further Reading

* [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)
* [AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks)
