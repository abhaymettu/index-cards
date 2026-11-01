# git tricks

## undoing stuff

- `git restore --staged <file>` unstages without touching working tree. way easier to remember than `reset HEAD`
- `git restore <file>` throws away unstaged edits. no undo on this one, careful
- `git reset --soft HEAD~1` undoes last commit but keeps everything staged. good for "oops wrong message" or "should've been two commits"
- `git reset --hard` only when I'm sure. otherwise `git stash` first, costs nothing
- `git reflog` is the safety net. found lost commits after a bad rebase more than once. look for the hash from before the mess, then `git reset --hard <hash>` or `git branch rescue <hash>`

## rebase / history cleanup

- `git rebase -i HEAD~N` then squash/fixup/reword. mark noisy "wip" commits as fixup
- `git commit --fixup <hash>` + `git rebase -i --autosquash <hash>~1` = no manual reordering in the editor
- `git config --global rebase.autosquash true` so I stop forgetting the flag
- `git pull --rebase` for a cleaner history on shared branches. set `pull.rebase true` globally
- when a rebase goes sideways: `git rebase --abort`, don't try to be a hero
- `git push --force-with-lease` not `--force`. refuses if remote has commits I haven't seen

## finding things

- `git log -S "some string"` finds commits that added or removed that string (pickaxe). great for "when did this function vanish"
- `git log -G "regex"` same idea but regex on the diff
- `git blame -L 40,80 <file>` limits to a line range. add `-w` to ignore whitespace changes
- `git log --follow -- <file>` tracks through renames
- `git bisect start`, `bisect bad`, `bisect good <hash>`. with a test script: `git bisect run ./test.sh`. saves hours
- `git log --oneline --graph --decorate --all` aliased to `git lg`

## stash and worktrees

- `git stash -u` includes untracked files. plain `stash` leaves them behind and that bites me
- `git stash push -m "msg" -- path/` stash only part of the tree, with a label
- `git worktree add ../scratch some-branch` second checkout of the same repo. beats stashing when I need to check another branch quickly
- clean up with `git worktree remove ../scratch`

## small quality-of-life

- `git switch -` jumps back to the previous branch
- `git diff --staged` before every commit, no exceptions
- `git add -p` to stage hunks, keeps commits focused
- `git branch --merged | grep -v main` to find branches safe to delete
- `git config --global rerere.enabled true` remembers conflict resolutions, nice during repeated rebases
