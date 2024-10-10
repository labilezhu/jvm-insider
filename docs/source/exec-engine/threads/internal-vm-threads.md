# Internal VM Threads

人们经常会惊讶地发现，即使执行一个简单的 “Hello World ”程序，也会在系统中创建十几个线程。这些线程由内部虚拟机线程和 library 相关线程（如 reference handler threads 和 finalizer threads）组合而成。虚拟机线程的主要类型如下：

- `VM thread`： VMThread 的单例负责执行虚拟机操作。主要监听和执行 `VM Operation` 请求。其中主要是 Global Safepoint  Stop The World 的协调。
- `Periodic task thread`： WatcherThread 的单例实例模拟定时器中断，在虚拟机内执行周期性操作
- `GC threads`： 这些不同类型的线程支持并行(parallel)和并发(concurrent)垃圾回收
- `Compiler threads`： 这些线程完成 byte code 到 native machine code 的编译(JIT)
- `Signal dispatcher thread`： 该线程等待进程级的信号(signals)，并将其分派给 Java 级信号处理方法



Thread C++ 对象：

- 所有线程都是`Thread C++ class`的实例  ；
- 所有执行 Java 代码的线程都是 `JavaThread C++ class（ Thread C++ class 的子类）` 实例。

虚拟机会在一个称为 `Threads_list` 的链接列表中跟踪所有线程，该列表受 `Threads_lock` 保护，`Threads_lock` 是虚拟机中使用的重要 `同步锁` 之一。



## 参考
- [OpenJDK Runtime Overiew - Thread Management - openjdk.org](https://openjdk.org/groups/hotspot/docs/RuntimeOverview.html#Thread%20Management|outline:~:text=objectmonitor%22%20structure.%5B8%5D-,Thread%20Management,-Thread%20management%20covers)

