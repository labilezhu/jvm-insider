# Debug JDK Tools

## gdb 调试 jstack

.vscode/launch.json

一开始，我是用这个方法：
```json
        {
            "name": "jstack",
            "type": "cppdbg",
            "request": "launch",
            "program": "/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/jdk/bin/jstack",
            "args": [
                "204131"
            ],
            "stopAtEntry": false,
            "cwd": "/home/labile/opensource/jdk",
            "environment": [],
            "externalConsole": false,
            "linux": {
                "MIMode": "gdb",
                "setupCommands": [
                    {
                        "text": "handle SIGSEGV noprint nostop",
                        "description": "Disable stopping on signals handled by the JVM"
                    },
                ]
            }
        }
```

### native 与 Java 代码混合调试

后来，我发觉除了 debug native code 外，我还需要 debug java code。于是，就不能用 jstack launcher 命令去使用 jstack 的功能了。就要想法子用 java 命令启动 jstack。于是：

```json
        {
            "name": "java-jstack",
            "type": "cppdbg",
            "request": "launch",
            "program": "/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/jdk/bin//java",
            "args": [
                "-agentlib:jdwp=transport=dt_socket,server=y,address=8000,suspend=y", "-Dapplication.home=/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/jdk", "-Dsun.jvm.hotspot.debugger.useProcDebugger", "-Djdk.module.main=jdk.jcmd", "-Dsun.java.command=jdk.jcmd/sun.tools.jstack.JStack",
                "-XX:-BackgroundCompilation", "-Xint", "-XX:CompileCommand=break,jdk.internal.loader.NativeLibraries::newInstance",
                "sun.tools.jstack.JStack",  "24586"
            ],
            "stopAtEntry": false,
            "cwd": "/home/labile/opensource/jdk",
            "environment": [],
            "externalConsole": false,
            "linux": {
                "MIMode": "gdb",
                "setupCommands": [
                    {
                        "text": "handle SIGSEGV noprint nostop",
                        "description": "Disable stopping on signals handled by the JVM"
                    },
                ]
            }
        }
```

其中， 24586 是一个预先启动好的 java 进程的 pid，等待被 jstack dump threads。 对应的原始命令应为：
```bash
./build/linux-x86_64-server-slowdebug/jdk/bin/java -agentlib:jdwp=transport=dt_socket,server=y,address=8000,suspend=y -Dapplication.home=/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/jdk -Dsun.jvm.hotspot.debugger.useProcDebugger -Djdk.module.main=jdk.jcmd -Dsun.java.command=jdk.jcmd/sun.tools.jstack.JStack sun.tools.jstack.JStack  24586
```

设置好 native 的 breakpoint，开始调试后，JVM 会挂起以等待 debugger 连接（因`suspend=y`）。
```bash
/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/jdk/bin/jdb -attach 8000
```

jdb 连接上后，就可以 set java breakpoint 了。需要执行 `cont` 或 `run` 命令， Java 层面才可以继续运行。 

设置 breakpoint 的一些例子：

```
stop at sun.tools.attach.VirtualMachineImpl:60

stop at sun.tools.attach.VirtualMachineImpl:226

stop at sun.tools.attach.VirtualMachineImpl:314

stop at jdk.internal.loader.NativeLibraries:120
```