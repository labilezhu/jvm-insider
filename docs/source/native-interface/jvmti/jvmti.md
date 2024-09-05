# JVMTI



## JVMTI 相关数据结构

说到 JNI，对于 Java 开发工具及其实现有兴趣的同学，不得不提一下基于 JNI 基础架构上的 JVMTI。

![JVMTI Data Structure](jvmti-data-struct.drawio.svg)
*JVMTI Data Structure*

*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fblog.mygraphql.com%2Fzh%2Fnotes%2Fjava%2Fjni-junior%2Fjvmti-data-struct.drawio.svg)*



以上内容参考了： [JVMTM Tool Interface](https://docs.oracle.com/en/java/javase/21/docs/specs/jvmti.html) 。



> ### What is the JVM Tool Interface?
>
> The JVMTM Tool Interface (JVM TI) is a programming interface **used by development and monitoring tools**. It provides both a way **to inspect the state and to control the execution of applications running in the JavaTM virtual machine (VM)**.
>
> JVM TI is intended to provide a VM interface for the full breadth of tools that need access to VM state, including but not limited to: profiling, debugging, monitoring, thread analysis, and coverage analysis tools.
>
> JVM TI may not be available in all implementations of the JavaTM virtual machine.
>
> JVM TI is a two-way interface:
>
> - A client of JVM TI, hereafter called an *agent*, 
> - can be notified of interesting occurrences through [events](https://docs.oracle.com/en/java/javase/21/docs/specs/jvmti.html#EventSection). 
>
> JVM TI can query and control the application through many [functions](https://docs.oracle.com/en/java/javase/21/docs/specs/jvmti.html#FunctionSection), either in response to events or independent of them.
>
> Agents run in the same process with and communicate directly with the virtual machine executing the application being examined. This communication is through a native interface (JVM TI). The native in-process interface allows maximal control with minimal intrusion on the part of a tool. Typically, agents are relatively compact. They can be controlled by a separate process which implements the bulk of a tool's function without interfering with the target application's normal execution.
>
> ### Architecture
>
> Tools can be written directly to JVM TI or indirectly through higher level interfaces. The Java Platform Debugger Architecture includes JVM TI, but also contains higher-level, out-of-process debugger interfaces. The higher-level interfaces are more appropriate than JVM TI for many tools. For more information on the Java Platform Debugger Architecture, see the [Java Platform Debugger Architecture website](https://docs.oracle.com/en/java/javase/21/docs/specs/jpda/architecture.html).



