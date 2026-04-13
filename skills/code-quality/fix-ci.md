Fix the failing CI tests on the current branch.

1. Check CI status: `gh run list --limit 5` and `gh run view --log-failed` for the latest failure
2. Identify all failing tests/checks
3. Enter plan mode: present the failures and propose fixes
4. After approval, fix all issues
5. Run `/verify` to confirm everything passes locally
6. Commit the fixes with a descriptive message
