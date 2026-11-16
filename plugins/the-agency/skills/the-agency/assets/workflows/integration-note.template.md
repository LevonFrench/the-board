# Integration note: <feature>

For a worker that may not compile, save into the main project or package. The lane that owns the build integrates from this note. Keep it to what that lane must do and check.

- Worker and date:
- Built and tested where: <side project or folder, absolute path; what was run there and its result>
- Revision of the main project this was written against:

## Files

| File to add or change | Goes to | New or changed |
|---|---|---|
| <absolute source path> | <path in the main project> | new |

## Call sites

Numbered, in the order to make them.

1. <file>, <function>: <the line or call to add, and where>

## Switches

Each one defaults to today's behaviour, so adding the files changes nothing until it is turned on.

| Switch | Default | Turns on |
|---|---|---|

## What the log should say

- On load: <exact line>
- When it runs: <exact line>

## Check after the build

- <what to look at in the assembled build, and the shot or log line that proves it>

## Not done, and risks

- <what was not tested here, and what could break in the main project>
