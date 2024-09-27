---
typora-root-url: ../../
---

# JVMTI



## JVMTI 相关数据结构

说到 JNI，对于 Java 开发工具及其实现有兴趣的同学，不得不提一下基于 JNI 基础架构上的 JVMTI。


:::{figure-md} 图: JVMTI Data Structure

<img src="/serviceability/jvmti/jvmti-data-struct.drawio.svg" alt="图: JVMTI Data Structure">

*图: JVMTI Data Structure*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fjvmti-data-struct.drawio.svg)*



以上内容参考了： [JVM Tool Interface Spec](https://docs.oracle.com/en/java/javase/21/docs/specs/jvmti.html) 。



### What is the JVM Tool Interface?

The JVMTM Tool Interface (JVM TI) is a programming interface **used by development and monitoring tools**. It provides both a way **to inspect the state and to control the execution of applications running in the JavaTM virtual machine (VM)**.

JVM TI is intended to provide a VM interface for the full breadth of tools that need access to VM state, including but not limited to: profiling, debugging, monitoring, thread analysis, and coverage analysis tools.

JVM TI may not be available in all implementations of the JavaTM virtual machine.

JVM TI is a two-way interface:

- A client of JVM TI, hereafter called an *agent*, 
- can be notified of interesting occurrences through [events](https://docs.oracle.com/en/java/javase/21/docs/specs/jvmti.html#EventSection). 

JVM TI can query and control the application through many [functions](https://docs.oracle.com/en/java/javase/21/docs/specs/jvmti.html#FunctionSection), either in response to events or independent of them.

Agents run in the same process with and communicate directly with the virtual machine executing the application being examined. This communication is through a native interface (JVM TI). The native in-process interface allows maximal control with minimal intrusion on the part of a tool. Typically, agents are relatively compact. They can be controlled by a separate process which implements the bulk of a tool's function without interfering with the target application's normal execution.

### Architecture

Tools can be written directly to JVM TI or indirectly through higher level interfaces. The Java Platform Debugger Architecture includes JVM TI, but also contains higher-level, out-of-process debugger interfaces. The higher-level interfaces are more appropriate than JVM TI for many tools. For more information on the Java Platform Debugger Architecture, see the [Java Platform Debugger Architecture website](https://docs.oracle.com/en/java/javase/21/docs/specs/jpda/architecture.html).



## JVM TI 实现

> 以下部分内容源自 [JVM Tool Interface(JVM TI) Implementation in HotSpot(2007) - Robert.Field@Sun.com](https://openjdk.org/groups/hotspot/docs/jvmtiImpl.pdf) 以下简称为 [JVM TI Impl - ReobertField](https://openjdk.org/groups/hotspot/docs/jvmtiImpl.pdf)



JVM TI 实现内部使用分层设计，由 高层 到 底层 分别为：



- User agent
  - JVM TI
- JVM TI View 层
  - jvmtiEnv.hpp
- JVM TI 实现层
  - jvmtiExport.hpp
- VM Core



### 分层实现 - JVM TI View 层

生成的 interface 和 辅助转接代码(transition code) 

- jvmti.h  : JVM TI 规范标准的 interface – `C`语言 interface) 
  - 位于 hotspot/variant-server/gensrc/jvmtifiles/jvmti.h
- jvmtiEnv.hpp  : HotSpot JVM TI `C++`语言 interface 
  - 位于 hotspot/variant-server/gensrc/jvmtifiles/jvmtiEnv.hpp
- jvmtiEnter.cpp  :  辅助转接代码(transition code) 
  -  位于 hotspot/variant-server/gensrc/jvmtifiles/jvmtiEnv.hpp



### 分层实现 - JVM TI 实现层 \- jvmtiExport

JVM TI 实现层 \- jvmtiExport 代码位于： [src/hotspot/share/prims/jvmtiExport.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/prims/jvmtiExport.cpp#L27)。

主要功能是：



- 负责 JVM TI 到 VM Core 的通信

  - 知道上层需要的信息 (capabilitie)
    - 因此要保留(preserve) 什么资源

  - 要发送哪些事件到上层

- 从 VM Core 捕获事件，并发送事件在上层
- 解藕 JVM TI 内部 与 VM Core 



![Function Architecture - from JVM TI Impl - ReobertField](/native-interface/jvmti/jvmti.assets/image-20240926165627386.png)

*图: Function Architecture - from [JVM TI Impl - ReobertField](https://openjdk.org/groups/hotspot/docs/jvmtiImpl.pdf)*





![image-20240926170439162](/native-interface/jvmti/jvmti.assets/image-20240926170439162.png)

*图: Function Flow - from [JVM TI Impl - ReobertField](https://openjdk.org/groups/hotspot/docs/jvmtiImpl.pdf)*





![image-20240926170634828](/native-interface/jvmti/jvmti.assets/image-20240926170634828.png)

*图: Event Architecture - from [JVM TI Impl - ReobertField](https://openjdk.org/groups/hotspot/docs/jvmtiImpl.pdf)*





![image-20240926170724341](/native-interface/jvmti/jvmti.assets/image-20240926170724341.png)

*图: Event Flow - from [JVM TI Impl - ReobertField](https://openjdk.org/groups/hotspot/docs/jvmtiImpl.pdf)*



### 实现细节

#### 线程与环境数据

![image-20240926172423843](/native-interface/jvmti/jvmti.assets/image-20240926172423843.png)

*图: 线程与环境数据 - from [JVM TI Impl - ReobertField](https://openjdk.org/groups/hotspot/docs/jvmtiImpl.pdf)*





## 参考
- [JVM Tool Interface(JVM TI) Implementation in HotSpot(2007) - Robert.Field@Sun.com](https://openjdk.org/groups/hotspot/docs/jvmtiImpl.pdf)

  