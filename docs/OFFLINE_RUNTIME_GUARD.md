# V104.2 Offline Runtime Guard

This guard turns NO_EXTERNAL_API / NO_REAL_SEND from a policy report into runtime enforcement.

It blocks common direct outbound paths when offline flags are enabled:

- urllib.request.urlopen / urlretrieve
- requests Session.request
- httpx Client / AsyncClient request
- subprocess outbound commands such as git push, curl, wget, scp, ssh, rsync

It does not connect to external services. It is activated by mainline_hook, single_runtime_entrypoint, V104.2 gate, and best-effort sitecustomize for normal Python runs.
