# Packaging Policy

当前包类型：source_release_without_runtime_cache。

运行时缓存、旧日志、临时文件、虚拟环境、node_modules、__pycache__ 不进入发布包。
必须保留源码、脚本、配置、身份上下文、最小状态目录与 mock approval 文件。
