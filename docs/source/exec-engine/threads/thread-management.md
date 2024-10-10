---
typora-root-url: ../../
---





# Thread Management

需要 JVM 管理控制的线程有几类：
- 由 Java 代码（无论是应用程序代码还是 Java 库代码）创建的线程。
- 直接 attach 到虚拟机的 native thread
- 为各种目的创建的 `internal VM threads`



## 线程模型
Hotspot 中的基本线程模型是 Java 线程（java.lang.Thread 的一个实例）与本机操作系统线程之间的 1:1 映射。本机线程在 Java 线程启动时创建，并在Java 线程终止后回收。操作系统负责调度所有线程并分派到 CPU。

Java 线程优先级与操作系统线程优先级之间的关系很复杂，因操作系统而异。



## 线程的创建和销毁

将线程引入虚拟机有两种基本方法：
- 执行 Java 代码，在 `java.lang.Thread` 对象上调用 `start()`；
- 使用 JNI 将现有 native thread  attach 到虚拟机。
- 虚拟机为内部目的创建的其他线程。



虚拟机中每个特定线程都有许多相关联的对象（这里指 C++ 编程语言编写的对象）：

- 代表 Java 代码中线程的 `java.lang.Thread` 实例
- 对应虚拟机中 `java.lang.Thread` 实例的 `JavaThread` 实例。它包含跟踪线程状态的附加信息。 `JavaThread` 拥有对其关联 `java.lang.Thread` 对象的引用（oop 形式），`java.lang.Thread` 对象也存储了对其 `JavaThread` 的引用（以 int `形式）。JavaThread` 还保存一个指向其关联 `OSThread` 实例的引用。
- `OSThread` 实例代表操作系统线程，包含跟踪线程状态所需的附加操作系统级信息。然后， `OSThread` 包含一个平台特定的 “`句柄(handle)`”，用于向操作系统标识实际的线程



### java.lang.Thread

启动 `java.lang.Thread` 时，虚拟机会创建相关的 `JavaThread` 和 `OSThread` 对象，并最终创建 native thread 。准备好所有虚拟机状态（如`线程本地存储 thread-local storage`和`分配缓冲区 allocation buffers`、`同步对象 synchronization objects`等）后， native thread 就启动了。 native thread 完成初始化后，会执行一个启动方法，该方法会引导到 java.lang.Thread 对象的 `run()` 方法的执行，然后在返回时，在处理任何未捕获的异常后终止线程，并与虚拟机交互以检查终止该线程是否需要终止整个虚拟机。线程终止会释放所有已分配的资源，将 JavaThread 从已知线程集合中删除，调用 OSThread 和 JavaThread 的析构函数，并最终在其初始启动方法完成后停止执行。



### JNI AttachCurrentThread

 native thread 使用 JNI 的 `AttachCurrentThread` 函数 attach 到虚拟机。此时会创建一个相关的 OSThread 和 JavaThread 实例，并执行基本初始化。接下来，必须为 attached 的线程创建一个 java.lang.Thread 对象，具体方法是根据线程 attach 时提供的参数，通过反射调用线程类构造函数的 Java 代码来完成。一旦 attach，线程就可以通过其他可用的 JNI 方法调用任何需要的 Java 代码。最后，当 native thread 不想再 attach 虚拟机时，它可以调用 JNI `DetachCurrentThread` 方法使其与虚拟机脱离关系（释放资源、放弃对 java.lang.Thread 实例的引用、析构 JavaThread 和 OSThread 对象等）。

attach native thread 的一个特殊情况是通过 JNI `CreateJavaVM` 调用初始化虚拟机，这可以由本地应用程序或 `启动器 launcher`（java.c）完成。这将导致一系列初始化操作，然后就像调用 AttachCurrentThread 一样的效果。然后，线程可根据需要调用 Java 代码，如应用程序主方法的反射调用。



## 线程状态

虚拟机使用多种不同的内部线程状态来描述每个线程正在做什么。这对于协调线程间的交互以及在出现问题时提供有用的调试信息都是必要的。在执行不同操作时，线程的状态会发生转换，这些转换点用于检查线程是否适合在该时间点执行所请求的操作，可见本书中关于 Safepoint 的章节。

从虚拟机角度看，主要的线程状态如下：

- _thread_new：正在初始化的新线程
- _thread_in_Java：正在执行 Java 代码的线程
- _thread_in_vm：正在虚拟机内执行的线程
- _thread_blocked：线程因某种原因被阻塞（获取锁、等待条件、休眠、执行阻塞 I/O 操作等）。



![](/exec-engine/safepoint/safepoint.assets/java-thread-state-machine.png)

*图: JavaThread 状态机。Source: [Java Thread state machine](https://youtu.be/JkbWPPNc4SI?si=c5YYAKHYBPROZAZ_&t=576)*



为便于调试，还在 thread dumps、stack traces 等工具中维护了额外的状态信息。这些信息保存在 OSThread 中，其中一些已不再使用，但在 thread dumps 等报告的状态中还会出现：

- MONITOR_WAIT：一个线程正在等待获取一个有竞争的 monitor lock
- CONDVAR_WAIT：线程正在等待虚拟机使用的内部`条件变量 condition variable `（与任何 Java 级对象无关）
- OBJECT_WAIT：线程正在执行 `Object.wait()` 调用



其他子系统和库会提供自己的状态信息，例如 JVMTI 系统和 java.lang.Thread 类本身暴露的 ThreadState。这些信息通常 虚拟机内部的线程管理 无法访问，也与其无关。



```{toctree}
internal-vm-threads.md
java-thread/java-thread.md
vm-threads-cooperative/vm-operation.md
```





































## 参考
- [OpenJDK Runtime Overiew - Thread Management - openjdk.org](https://openjdk.org/groups/hotspot/docs/RuntimeOverview.html#Thread%20Management|outline:~:text=objectmonitor%22%20structure.%5B8%5D-,Thread%20Management,-Thread%20management%20covers)

