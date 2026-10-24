# Working together on GitHub

The shared development branch is `master`. The integrated application is proposed on
`integrated-pizzeria`; it should be reviewed before merging.

## Terms

- **Repository:** the project's files plus saved history.
- **Branch:** a separate line of changes, so work can be reviewed before joining master.
- **Commit:** a named snapshot of a coherent change.
- **Push:** upload local commits to GitHub.
- **Pull request:** ask teammates to review a branch before merging it.
- **Pull:** download and incorporate changes already pushed by teammates.

## The integration commits

The prepared commits separate backend organization, the frontend prototype,
API/database integration, and tests/documentation. They were prepared together
for review; their timestamps describe the actual commit creation time, not an
invented development schedule.

## Your next change

1. Start from an up-to-date checkout of the branch your team is using.
2. Create a short branch name describing the task.
3. Change a focused part of the application and run its relevant tests.
4. Review `git diff` and `git status` before staging files.
5. Commit with a short description of the actual change.
6. Push that branch and open a pull request.
7. Address teammate feedback, then let the team decide when to merge.

Do not force-push master, upload virtual environments, commit `.env` files,
or add runtime databases and ZIP backups. The repository's `.gitignore`
excludes these files. The database is created from fictional fixtures at startup.

For the application setup and demo accounts, follow the root README.
