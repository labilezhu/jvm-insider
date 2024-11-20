# fatal error log


fatal error log 例子： {download}`hs_err_pid15858.log </troubleshoot/fatal-error-log/hs_err_pid15858.log>`

Fatal Error Log 文件路径：
```
java -XX:ErrorFile=/var/log/java/java_error%p.log
```



> The substring `%%` in the *file* variable is converted to `%`, and the substring `%p` is converted to the PID of the process.
>
> If the `-XX:ErrorFile=file` flag is not specified, then the default log file name is `hs_err_pid.log`, where `pid` is the PID of the process.
>
> In addition, if the `-XX:ErrorFile=file` flag is not specified, the system attempts to create the file in the working directory of the process. In the event that the file cannot be created in the working directory (insufficient space, permission problem, or other issue), the file is created in the temporary directory for the operating system. On the Linux operating system, the temporary directory is `/tmp`


## JVM crash 排查例子

这里有个 [进程的 mmap (vm.max_map_count)耗尽例子](https://blog.mygraphql.com/zh/posts/software-architect/design-for-failure/exhaustion-and-intermittence/#资源耗尽exhaustion)。通过 fatal error log ，其中有 Memory Map 的信息，这就可以现场取证了。


## 参考

- [A Fatal Error Log - Oracle Java SE 17 Docs](https://docs.oracle.com/en/java/javase/17/troubleshoot/location-fatal-error-log.html)