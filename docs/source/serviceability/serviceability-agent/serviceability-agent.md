# Serviceability Agent

> 参考：
>
> - [The HotSpot Serviceability Agent: An out-of-process high level debugger for a JVM - usenix.org](https://www.usenix.org/legacy/events/jvm01/full_papers/russell/russell_html/index.html)
>
> - [Serviceability in HotSpot - openjdk.org](https://openjdk.org/groups/hotspot/docs/Serviceability.html)



`Serviceability Agent(SA)` 原是 HotSpot 原码库中的 Sun 私有组件，由 HotSpot 工程师开发，用于协助调试 HotSpot OpenJDK。他们随后意识到 SA 可用于支持用户编写 serviceability tools ，因为它可以在运行中的进程以及 Core Dump 文件中检视 Java 对象以及 HotSpot 数据结构。



SA 组件有以下功能：

- 从正在执行的 Java 进程中读取内存，或读取 Java 进程生成的 core dump file。
- 从原始内存中提取所有 HotSpot VM C++ 数据结构。
- 从 HotSpot 数据结构中提取 Java 对象。



请注意，SA 在与目标JVM进程不同的进程中运行，并且不执行目标进程中的代码。但是，当 SA 观察目标进程时，目标进程会停止(halted)。

SA 主要由 Java 类组成，但它包含少量 native code，用于从进程和 core dump file 中读取原始内存。在 Linux 上，SA 使用 /proc 和 ptrace（主要是后者）的组合来读取进程中的原始内存。对于 core dump file，SA 直接解析 ELF 文件。



OpenJDK 9 以后出现的 jhsdb (Java HotSpot DeBug) 工具，就是基于 SA 开发的。在 OpenJDK 9 以前，是 JAVA_HOME/lib 中的 sa-jdi.jar 。



HotSpot `Serviceability Agent(SA)` 是一组用于 Java 编程语言的 API，用于为 Java HotSpot 虚拟机的状态建立模型。与大多数动态语言调试系统不同，它们基于一种 “协作(cooperative)” 模型，需要在目标进程运行代码来协助调试过程，而 SA 不需要在目标 VM 中运行代码。相反，它使用符号查找( symbol lookup) 和读取进程内存等原语来(primitives)实现其功能。SA 可以透明地检视运行中的进程或 core dump file，使其适合调试 navtive VM  code 和 Java code。



HotSpot Open JDK 采用混合模式汇编解释器(mixed-mode assembly interpreter)，该解释器与编译为机器代码的 C 代码和 Java 编程语言方法（Java 方法）共享堆栈。运行时分析(Run-time profiling) 仅将编译工作集中在“热” method 上。

如果编译 method 时所依据的要素，因未来的类加载而变弱，`动态反优化(Dynamic deoptimization)`技术 允许已编译的 method 恢复到解释状态。动态反优化的设计，使得编译器可以执行激进的优化和内联，而无后顾之忧。



要调试高度优化后的 JVM 程序，要解决一些挑战：

- 倾向使用生成的机器代码进行调试操作，并合并 C++ 和 Java 虚拟机堆栈（Java 堆栈）。
- 对于编译器高度优化的代码。由于内联(inlining)，堆栈上的一个 Frame 可能对应于多个 Java 方法调用。
- 为节省空间，许多运行时数据结构，不是以原生格式，而会以再编码的格式记录于内存。
- 没有 C++ 数据结构调试信息，去结构描述系统运行时的数据，例如堆(heap)的布局(layout)。

简而言之，当使用传统的 C++ 调试器检视 JVM 时，要直接面对原始二进内存数据。所有高级的抽象数据类型都不能应用于检视。



HotSpot Serviceability Agent 是一组 Java 编程语言的 API，可从运行中的 HotSpot JVM 或 core dump file 中读取原始数据，并解释为高级的抽象数据类型的形式返回给使用者。



![图: 基于 SA API 的对象检视器(object inspector)](serviceability-agent.assets/java2d-jbutton-inspector.jpg)

*图: 基于 SA API 的对象检视器(object inspector)*



使用 SA 的应用程序，可以使用其 API 编写特定于应用程序的工具、调试辅助工具和查询操作，这些操作直接在目标 JVM 上运行，并且完全非侵入式。*图: 基于 SA API 的对象检视器(object inspector)*  展示了基于 SA 的 API 构建的对象检查器。

与大多数动态语言调试器不同，SA 不需要在目标 JVM 中运行任何代码。此属性使它能够作为 JVM core dump file 的调试器。SA 还适用于更多情况，而不仅仅是调试 JVM。例如，最终用户可以使用它来编写堆分析器，这些分析器可以在生产 JVM 上运行，而无需重启 JVM。



SA 旨在诊断 JVM 故障。这一要求决定了几个设计决策，包括目标进程中不运行任何代码。SA 目前是一个仅用于检视的系统，这意味着它使用低级原语（如符号查找(symbol lookup)和从目标进程读取内存）来获取所有信息。这使得它既可以通过 attach 到正在运行的进程来工作，也可以通过读取 core dump file 来工作。它还可以在任意 JVM 中注入并运行其代码。







## 遍历线程列表

HotSpot JVM 在内存中维护着一个 flag ，指明每个 Java 线程正在执行哪种代码：

- JVM 内部代码
- “native”代码 
- Java 代码。



> 由于参考文章 [The HotSpot Serviceability Agent: An out-of-process high level debugger for a JVM - usenix.org](https://www.usenix.org/legacy/events/jvm01/full_papers/russell/russell_html/index.html) 是 2001 年的旧文，本小节部分内容可能已经在 2024 年有大变化。但 SA 的设计细想和原理基本不变。



以下为遍历目标 JVM 的线程列表的简单示例：

![图: SA 中 JVM 数据结构的镜像说明](serviceability-agent.assets/thread-list.jpg)

*图: SA 中 JVM 数据结构的镜像说明(基于 2001 年的 JVM 版本)*



- (A) JVM 的 [JavaThread class C++ 代码](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/javaThread.hpp#L244)，包括线程的状态 [JavaThread 的 volatile JavaThreadState _thread_state](_thread_state) 以 线程列表等数据结构。

[enum JavaThreadState](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/utilities/globalDefinitions.hpp#L1030) 的定义如下：

```c++
// JavaThreadState keeps track of which part of the code a thread is executing in. This
// information is needed by the safepoint code.
//
// There are 4 essential states:
//
//  _thread_new         : Just started, but not executed init. code yet (most likely still in OS init code)
//  _thread_in_native   : In native code. This is a safepoint region, since all oops will be in jobject handles
//  _thread_in_vm       : Executing in the vm
//  _thread_in_Java     : Executing either interpreted or compiled Java code (or could be in a stub)
//
// Each state has an associated xxxx_trans state, which is an intermediate state used when a thread is in
// a transition from one state to another. These extra states makes it possible for the safepoint code to
// handle certain thread_states without having to suspend the thread - making the safepoint code faster.
//
// Given a state, the xxxx_trans state can always be found by adding 1.
//
enum JavaThreadState {
  _thread_uninitialized     =  0, // should never happen (missing initialization)
  _thread_new               =  2, // just starting up, i.e., in process of being initialized
  _thread_new_trans         =  3, // corresponding transition state (not used, included for completeness)
  _thread_in_native         =  4, // running in native code
  _thread_in_native_trans   =  5, // corresponding transition state
  _thread_in_vm             =  6, // running in VM
  _thread_in_vm_trans       =  7, // corresponding transition state
  _thread_in_Java           =  8, // running in Java or in stub code
  _thread_in_Java_trans     =  9, // corresponding transition state (not used, included for completeness)
  _thread_blocked           = 10, // blocked in vm
  _thread_blocked_trans     = 11, // corresponding transition state
  _thread_max_state         = 12  // maximum thread state+1 - used for statistics allocation
};
```



- (B) 说明了此数据结构在 JVM 地址空间中的内存布局；从全局线程列表开始，JavaThread 对象链接在一起*(基于 2001 年的 JVM 版本)*
- (C) 访问这些数据结构的 SA 代码。



SA 采用镜像 JVM  C++ 数据结构的方法。当 SA 要创建`目标 JVM 的对象`的镜像对象时，它会使用 `Address 抽象对象` 从目标地址中获取数据，该 `Address 抽象对象`  包含上图的 method 以及数据结构，以及Java 原始数据：如 `byte getJByteAt(long offset)` 和 `short getJShortAt(long offset)` 。



## 目标对象的解码



目标 JVM 镜像对象的创建，如何才能做不到 hard code pointer offset ? 见 [The HotSpot Serviceability Agent: An out-of-process high level debugger for a JVM - usenix.org](https://www.usenix.org/legacy/events/jvm01/full_papers/russell/russell_html/index.html) 中的 [Describing C++ Types](https://www.usenix.org/legacy/events/jvm01/full_papers/russell/russell_html/index.html#:~:text=Describing%20C%2B%2B%20Types) 。其实这个需求有点像 eBPF 的 [BTF](https://docs.ebpf.io/concepts/btf/) 。由于不是本书的重点，这里不展开。有兴趣的读者可以参考 [Describing C++ Types](https://www.usenix.org/legacy/events/jvm01/full_papers/russell/russell_html/index.html#:~:text=Describing%20C%2B%2B%20Types) 或 OpenJDK 源码 [src/hotspot/share/runtime/vmStructs.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/vmStructs.hpp#L77) 与 [src/jdk.hotspot.agent/share/classes/sun/jvm/hotspot/HotSpotTypeDataBase.java](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/jdk.hotspot.agent/share/classes/sun/jvm/hotspot/HotSpotTypeDataBase.java#L46)  ，其中有大量注释讲解这个对象 Metadata  database 的编写和生成原理。





## Attach  到目标 JVM 进程



有兴趣知道 SA 是如何 attach 到 JVM 的读者，见：[src/jdk.hotspot.agent/share/classes/sun/jvm/hotspot/debugger/linux/LinuxDebuggerLocal.java 中的 void attach(int processID)](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/jdk.hotspot.agent/share/classes/sun/jvm/hotspot/debugger/linux/LinuxDebuggerLocal.java#L295)

以及其对应的 JNI native 代码：[src/jdk.hotspot.agent/linux/native/libsaproc/LinuxDebuggerLocal.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/jdk.hotspot.agent/linux/native/libsaproc/LinuxDebuggerLocal.cpp#L284)



Native debug 层，类似 gdb 的行为，如 `ptrace_attach(pid)` 发生在 src/jdk.hotspot.agent/linux/native/libsaproc/ps_proc.c 的 [Pgrab(pid_t pid, ...)](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/jdk.hotspot.agent/linux/native/libsaproc/ps_proc.c#L443) 



## stack 还原

见 [The HotSpot Serviceability Agent: An out-of-process high level debugger for a JVM - usenix.org] 中的 [Traversing the Stacks](https://www.usenix.org/legacy/events/jvm01/full_papers/russell/russell_html/index.html#:~:text=Traversing%20the%20Stacks) 。这个有点复杂，需要大量背景知识，有兴趣的读者还是自己阅读吧。





 































































## 参考

-  [The HotSpot Serviceability Agent: An out-of-process high level debugger for a JVM - usenix.org](https://www.usenix.org/legacy/events/jvm01/full_papers/russell/russell_html/index.html)