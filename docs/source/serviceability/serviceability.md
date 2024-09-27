# JVM Serviceability in HotSpot


> [Serviceability in HotSpot - openjdk.org](https://openjdk.org/groups/hotspot/docs/Serviceability.html)



在 Java/JVM 术语里，Serviceability 是指 HotSpot 虚拟机包含的几种技术，它们使另一个外部 Java 进程可以观察运行了 Serviceability 组件的 JVM 的行为。这些 Serviceability 技术最少包括：



- **The Serviceability Agent(SA)**. The Serviceability Agent is a Sun private component in the HotSpot repository that was developed by HotSpot engineers to assist in debugging HotSpot. They then realized that SA could be used to craft serviceability tools for end users since it can expose Java objects as well as HotSpot data structures both in running processes and in core files.
  翻译一下：`Serviceability Agent(SA)` 原是 HotSpot 原码库中的 Sun 私有组件，由 HotSpot 工程师开发，用于协助调试 HotSpot OpenJDK。他们随后意识到 SA 可用于为最终用户制作 serviceability tools ，因为它可以在运行中的进程以及 Core Dump 文件中检视 Java 对象以及 HotSpot 数据结构。
- **jvmstat performance counters**. HotSpot maintains several performance counters that are exposed to external processes via a Sun private shared memory mechanism. These counters are sometimes called perfdata.
- **The Java Virtual Machine Tool Interface (JVM TI)**. This is a standard C interface that is the reference implementation of [JSR 163 - JavaTM Platform Profiling Architecture](http://jcp.org/en/jsr/detail?id=163) JVM TI is implemented by HotSpot and allows a native code 'agent' to inspect and modify the state of the JVM.
- **Dynamic Attach**. This is a Sun private mechanism that allows an external process to start a thread in HotSpot that can then be used to launch an agent to run in that HotSpot, and to send information about the state of HotSpot back to the external process.



下表包含有关每种技术的更多信息的链接，显示了这些技术在 HotSpot 源码库中的位置，并包含有关 J2SE 源码库中使用这些技术的信息的链接。

| 技术                                         | 源码库中的位置                                               | 在 J2SE 中的应用(依赖于这个技术的模块)                       |
| -------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| JVM TI- Java Virtual Machine Tools Interface | hotspot/src/share/vm/prims/jvmtiGen.java hotspot/src/share/vm/prims/jvmtiGen.java hotspot/src/share/vm/prims/jvmti.xml hotspot/src/share/vm/prims/jvmti* build/.../generated/jvmtifiles/jvmtiEnter.cpp build/.../generated/jvmtifiles/jvmtiEnterTrace.cpp build/.../generated/jvmtifiles/jvmtiEnv.hpp build/.../generated/jvmtifiles/jvmtiEnvRecommended.cpp build/.../generated/jvmtifiles/jvmtiEnvStub.cpp build/.../generated/jvmtifiles/jvmti.h     (copied to j2se/src/share/javavm/export/jvmti.h) | JDWP Agent                                                   |
| Monitoring and Management                    | hotspot/src/share/vm/services/ (most but not all)            |                                                              |
| Dynamic attach mechanism                     | src/share/vm/services/attachListener.* src/os/linux/vm/attachListener_linux.cpp src/os/solaris/vm/attachListener_solaris.cpp src/os/win32/vm/attachListener_win32.cpp | [Module jdk.attach - Defines the attach API](https://docs.oracle.com/en/java/javase/21/docs/api/jdk.attach/module-summary.html) |
| Jvmstat Performance Counters                 | src/share/vm/prims/perf.cpp src/share/runtime/perfMemory.cpp src/share/runtime/perfData.cpp src/share/runtime/statSampler.cpp src/share/vm/services/*Service.cpp src/os/solaris/vm/perfMemory_solaris.cpp src/os/linux/vm/perfMemory_linux.cpp src/os/win32/vm/perfMemory_win32.cpp |                                                              |
| Serviceability Agent                         | hotspot/agent/ hotspot/src/share/vm/runtime/vmStructs.hpp hotspot/src/share/vm/runtime/vmStructs.cpp hotspot/cpu/cpu/vm/vmstructs_cpu.hpp hotspot/os_cpu/os-cpu/vm/vmstructs_os-cpu.hpp | [Usenix Serviceability Agent paper](https://www.usenix.org/legacy/events/jvm01/full_papers/russell/russell_html/index.html) |



## 参考
- [Serviceability in HotSpot - openjdk.org](https://openjdk.org/groups/hotspot/docs/Serviceability.html)
- [Usenix Serviceability Agent paper](https://www.usenix.org/legacy/events/jvm01/full_papers/russell/russell_html/index.html)


```{toctree}
jvmti/jvmti.md
serviceability-agent/serviceability-agent.md
```