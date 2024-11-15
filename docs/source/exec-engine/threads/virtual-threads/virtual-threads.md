# Virtual Threads

按这本书作者的德性，和这本书的定位，这里不会有介绍什么是 `Virtual Threads` 的章节了。只会写这个技术的一些细节。



术语：

- Carrier Threads (CTs)
- Virtual Thread (VT)
- Platform Thread (PT)


## Virtual Thread 状态
:::{figure-md} 图: Virtual Thread 状态机

<img src="virtual-thread-state.drawio.svg" alt="图: Virtual Thread 状态机">

*图: Virtual Thread 状态机*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fvirtual-thread-state.drawio.svg)*

上面是 OpenJDK 21.35 的状态图。

在 OpenJDK 22 的 [8312498: Thread::getState and JVM TI GetThreadState should return TIMED_WAITING virtual thread is timed parked](https://github.com/openjdk/jdk/commit/4461eeb31d5ccc89e304329a7dccb9cb130713fc) 后，状态图变复杂了一点。


## 优劣及原因

### 简化性能分析

> [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)
> Java debuggers can step through virtual threads, show call stacks, and inspect variables in stack frames. JDK Flight Recorder (JFR), which is the JDK's low-overhead profiling and monitoring mechanism, can associate events from application code (such as object allocation and I/O operations) with the correct virtual thread. **These tools cannot do these things for applications written in the asynchronous style**. In that style tasks are not related to threads, so debuggers cannot display or manipulate the state of a task, and profilers cannot tell how much time a task spends waiting for I/O.

对于以前的基于 callback 异步编程模式编写的程序，很多性能分析(profiling)工具不能提供好的分析结果，因为这些工具有一个假设：一个任务是一个线程从头同步跑到尾的。工具本身不知道如何跟踪 callback 模式中的任务上下文，从而无法识别出运行期的相关性。
而采用 virtual thread 后，运行期上下文的 virtual thread id 可以用于跟踪任务的相关性，就帮助 profiling 工具更好更简单地串联起多个运行期事件。



## 调度

virtual threads 的调度，在 Pure Java 代码中完成。所以，别对调度的 `公平性` `实时性` `可抢占性` 有太大期望了。如果你用过 199x 年的 MS Windows 3.1，看到过一个有 bug 的应用如何卡死了整个操作系统，就知道这种调度有什么短板了。不过，什么东西是没有短板的呢？

> [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)
> The JDK's virtual thread scheduler is a work-stealing ForkJoinPool that operates in FIFO mode. The parallelism of the scheduler is the number of platform threads available for the purpose of scheduling virtual threads. By default it is equal to the number of available processors, but it can be tuned with the system property  jdk.virtualThreadScheduler.parallelism.

JDK 的 VT 调度程序是一个以 FIFO 模式运行的 ForkJoinPool。调度程序的并行度取决于可用于调度 VT 的 `platform threads` 数。默认情况下，它等于可用 CPU/core 的数量，但可以使用系统属性 `jdk.virtualThreadScheduler.parallelism` 进行调整。



### 调度配置

#### ForkJoinPool

> 以下参考： [Monitoring Java Virtual Threads](https://jefrajames.fr/2024/01/10/monitoring-java-virtual-threads/)

正如我们所见，ForkJoinPool 在 VT 调度中起着关键作用。如果池太小，调度会变慢并降低性能。 可以使用以下系统属性配置 ForkJoinPool：

- `jdk.virtualThreadScheduler.parallelism` ：池大小（多少个 CT），默认为 CPU  core 数 
- `jdk.virtualThreadScheduler.maxPoolSize` ：池的最大大小，默认为 256。当 CT 被阻止时（由于操作系统或 JVM 限制），CT 数量可能会暂时超过 `jdk.virtualThreadScheduler.parallelism` 设置的数量。（注意，调度程序不会通过临时增加并行 CT 来补偿 pinned VT 占用的 CT）
- `jdk.virtualThreadScheduler.minRunnable` ：池中保持可运行的线程的最小数量。



## Java 层的实现原理



![magic-of-continuation](./virtual-threads.assets/magic-of-continuation.png)

*图：Magic of continuation : Source: [Monitoring Java Virtual Threads](https://jefrajames.fr/2024/01/10/monitoring-java-virtual-threads/)*





### 为什么要 pin Carrier Threads



> [Monitoring Java Virtual Threads](https://jefrajames.fr/2024/01/10/monitoring-java-virtual-threads/)
>
> This happens when Java stack addresses are referenced from non-Java code. Java adresses are relocated when restoring from the heap, making non-Java references no longer good.
>
> To prevent this error, the CT is pinned:

![img](./virtual-threads.assets/threadpinning.png)

*图：Continuation pinned : Source: [Monitoring Java Virtual Threads](https://jefrajames.fr/2024/01/10/monitoring-java-virtual-threads/)*



这在以下调用时发生:

- `synchronized` blocks 或 methods
- native code:  JVM 自身的内部代码，或通过 JNI / Foreign Functions 发起的外部调用

这意味着我们必须跟踪 pinned VT 以识别那些可能影响性能的 VT。



## 监控

以下参考： [Monitoring Java Virtual Threads](https://jefrajames.fr/2024/01/10/monitoring-java-virtual-threads/)



### 监控 pinned VT

我们可以使用：

- `-Djdk.tracePinnedThreads` Java 启动选项。它可以跟踪代码中出现 pinned VT 的位置
- JFR 事件 `jdk.VirtualThreadPinned` ：它能够识别可能影响性能的 pinned VT。此事件默认启用，阈值为记录超过 20 毫秒（可配置） 的 pinned VT











## 参考

- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)
- [Monitoring Java Virtual Threads](https://jefrajames.fr/2024/01/10/monitoring-java-virtual-threads/)