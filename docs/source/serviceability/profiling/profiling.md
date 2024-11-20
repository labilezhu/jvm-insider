# Profiling

## Stack Walk



### AsyncGetCallTrace

- [AsyncGetStackTrace: A better Stack Trace API for the JVM](https://mostlynerdless.de/blog/2023/01/19/asyncgetstacktrace-a-better-stack-trace-api-for-the-jvm/)
- [Writing a Profiler from Scratch: Introduction](https://mostlynerdless.de/blog/2022/12/20/writing-a-profiler-from-scratch-introduction/)

#### Async-profiler's AsyncGetCallTrace

async-profiler 的 wall-clock 模式下， walk stack 在目标线程中执行：

![img](./profiling.assets/wall-clock-sampling-sequence.svg)
*图 Source: [Couldn’t we just Use AsyncGetCallTrace in a Separate Thread?](https://community.sap.com/t5/technology-blogs-by-sap/couldn-t-we-just-use-asyncgetcalltrace-in-a-separate-thread/ba-p/13558812)*





### Async-profiler's AsyncGetCallTrace replacement
- [AsyncGetCallTrace replacement #795 - async-profiler issues](https://github.com/async-profiler/async-profiler/issues/795)



## JDK Flight Recorder (JFR) SuspendedThreadTask

JDK Flight Recorder (JFR) 使用单线程执行 Stack Walk :
![img](./profiling.assets/wall-clock-sampling-sequence-Page-2.svg)
*图 Source: [Couldn’t we just Use AsyncGetCallTrace in a Separate Thread?](https://community.sap.com/t5/technology-blogs-by-sap/couldn-t-we-just-use-asyncgetcalltrace-in-a-separate-thread/ba-p/13558812)*



### 比较几种 Stack Walk 方法

> One important difference to consider is that in JFR, in contrast to AGCT, there is only a single thread, the ThreadSampler thread, that is wrapped in the CrashProtection. Stack walking is different in JFR compared to AGCT, in that it is done by a *different thread*, during a point where the target is suspended. Originally, this thread sampler thread was not even part of the VM, although now it is a NonJavaThread. It has been trimmed to not involve malloc(), raii, and other hard-to-recover-from constructs, from the moment it has another thread suspended. Over the years, some transitive malloc() calls has snuck in, but it was eventually found due to rare deadlocking. Thomas brings a good point about crashes needing to be recoverable.
>
> [MarKUS Grönlund In A Comment on OpenJDK PR 8225](https://github.com/openjdk/jdk/pull/8225#issuecomment-1099391050)



## 参考

- [AsyncGetStackTrace: A better Stack Trace API for the JVM](https://mostlynerdless.de/blog/2023/01/19/asyncgetstacktrace-a-better-stack-trace-api-for-the-jvm/)
- [Couldn’t we just Use AsyncGetCallTrace in a Separate Thread?](https://community.sap.com/t5/technology-blogs-by-sap/couldn-t-we-just-use-asyncgetcalltrace-in-a-separate-thread/ba-p/13558812)

