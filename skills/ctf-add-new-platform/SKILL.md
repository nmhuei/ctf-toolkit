---
name: ctf-add-new-platform
description: Use when you add or test support for a CTF platform that the toolkit does not support.
---

# Add CTF Platform Support

Use this skill when ctf pull cannot identify or use an authorized platform.

Read the current platform schemas and adapter code before you change them. Do not assume that every platform uses one API format.

## Probe the Platform

The probe command takes the URL as a positional argument. It has no -u or -c option.

~~~bash
ctf platform probe <URL>
~~~

To save a JSON schema in one workspace, use:

~~~bash
ctf platform probe <URL> --save --scope workspace -w <WORKSPACE>
~~~

Do not put cookies or tokens in the command. Configure auth with ctf auth or the supported local credential store.

Treat probe output as a candidate. Check each endpoint, response field, and attachment rule against the authorized platform.

## Choose an Adapter

Use a JSON definition when the platform maps cleanly to the existing schema.

~~~bash
python3 scripts/scaffold_platform.py -k <KEY> -l "<LABEL>" -t json -s workspace -w <WORKSPACE>
~~~

The script creates a JSON definition and a test file. Check both paths before you edit. The default scope is builtin. Use workspace or global only when the user requests that scope.

Use a Python adapter when the platform needs custom response parsing or request behavior.

~~~bash
python3 scripts/scaffold_platform.py -k <KEY> -l "<LABEL>" -t python
~~~

The script creates an adapter, adds its import to the registry, and creates a test file. It changes toolkit source files. Make this change only when the user asked you to add platform support.

The adapter implements these required methods from BasePlatform:

- authenticate
- fetch_challenges
- get_full_file_url
- submit_flag

Follow the template. Use solved_by_me and self.base_url where they match the model and base class.

## Test and Verify

Run the generated test:

~~~bash
pytest tests/test_platform_<KEY>.py
~~~

Read the diff. Keep tests local and mock HTTP requests. Do not submit a test flag to a live platform.

Run ctf pull against a live platform only when the user authorizes the request. Report the exact workspace, result, and any missing schema fields.

## Keep Facts Accurate

Do not claim that probe output proves full platform support. Do not claim that one adapter path fits a fixed percentage of platforms.

Read references/platform_authoring.md for the JSON schema and adapter details.
