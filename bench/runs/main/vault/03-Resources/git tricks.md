# git tricks

## undoing stuff

- `git reset --soft HEAD~1` – undo last commit, keep changes staged. use this 90% of the time when I commit too early
- `git reset --hard origin/main` – nuke local to match remote. double check nothing unpushed first
- `git restore <file>` – discard working changes. `git restore --staged <file>` to unstage
- `git revert <sha>` – for anything already pushed/shared. makes a new commit instead of rewriting
- **reflog is the safety net.** `git reflog` shows every place HEAD has been, even after a bad reset or deleted branch. find the sha, `git checkout -b rescue <sha>`. works for ~90 days by default

## cleaner history

- `git commit --fixup <sha>` then `git rebase -i --autosquash <sha>~1` – way less fiddly than editing the todo list by hand
- `git commit --amend --no-edit` – tack a forgotten file onto the last commit
- `git pull --rebase` – avoids the pointless merge commits. set `pull.rebase true` globally and forget about it
- `git push --force-with-lease` instead of `--force`. refuses if someone else pushed in the meantime
- `git rebase --onto main old-base feature` – move a branch that was cut from the wrong parent

## finding things

- `git log -S"someString"` – pickaxe, finds commits that added/removed that string
- `git log -G"regex"` – same idea but regex, matches changed lines
- `git log -p -- path/to/file` – history of one file with diffs. add `--follow` if it was renamed
- `git blame -w -C -C file` – ignore whitespace, detect lines moved between files. much more honest blame
- `git bisect start; git bisect bad; git bisect good <sha>` – then `git bisect run ./test.sh` and go get coffee

## daily quality of life

- `git stash push -m "msg" -- path` – stash only specific files, with a label so I can find it later
- `git stash show -p stash@{1}` – peek before applying
- `git switch -` – jump back to previous branch (like `cd -`)
- `git branch --merged | grep -v main | xargs git branch -d` – prune local branches already merged
- `git worktree add ../scratch some-branch` – second checkout of the same repo, no stashing dance when I need to hop over for a quick fix
- `git diff --stat main...HEAD` – three dots = changes on my branch since it diverged. two dots is a different thing, easy to mix up

## config worth keeping

- `rerere.enabled true` – remembers conflict resolutions, saves me during repeated rebases
- `diff.algorithm histogram` – nicer diffs on moved code
- `fetch.prune true` – stale remote branches disappear on their own
- `init.defaultBranch main`
