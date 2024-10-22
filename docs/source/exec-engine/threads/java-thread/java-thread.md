---
typora-root-url: ../../../
---


# Java Thread


## 线程模型
Hotspot 中的基本线程模型是 Java 线程（java.lang.Thread 的一个实例）与本机操作系统线程之间的 1:1 映射。本机线程在 Java 线程启动时创建，并在Java 线程终止后回收。操作系统负责调度所有线程并分派到 CPU。

Java 线程优先级与操作系统线程优先级之间的关系很复杂，因操作系统而异。



## JavaThread class



[src/hotspot/share/runtime/javaThread.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/javaThread.hpp#L244)

```c++
class JavaThread: public Thread {
...
  // Safepoint support
 public:                                                        // Expose _thread_state for SafeFetchInt()
  volatile JavaThreadState _thread_state;
 private:
  SafepointMechanism::ThreadData _poll_data;
  ThreadSafepointState*          _safepoint_state;              // Holds information about a thread during a safepoint
  address                        _saved_exception_pc;           // Saved pc of instruction where last implicit exception happened

```


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


## JavaThread 状态 - JavaThreadState



[src/hotspot/share/utilities/globalDefinitions.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/utilities/globalDefinitions.hpp#L1030)

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

其中 `class JavaThread` 的 `JavaThreadState _thread_state` 字段记录了线程的状态。


![](/exec-engine/safepoint/safepoint.assets/java-thread-state-machine.png)

*图: JavaThread 状态机。Source: [Java Thread state machine](https://youtu.be/JkbWPPNc4SI?si=c5YYAKHYBPROZAZ_&t=576)*

## JVM 内部 Thread Local

### current thread

[src/hotspot/share/utilities/globalDefinitions_gcc.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/utilities/globalDefinitions_gcc.hpp#L156)
```c++
#define THREAD_LOCAL __thread
```

[src/hotspot/share/runtime/thread.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/thread.cpp#L57)
```c++
THREAD_LOCAL Thread* Thread::_thr_current = nullptr;
```

[src/hotspot/share/runtime/thread.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/thread.hpp#L660)
```c++
void Thread::initialize_thread_current() {
  _thr_current = this;
}

// Inline implementation of Thread::current()
inline Thread* Thread::current() {
  Thread* current = current_or_null();
  assert(current != nullptr, "Thread::current() called on detached thread");
  return current;
}
```

[src/hotspot/os/linux/os_linux.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/os/linux/os_linux.cpp#L739)
```c++
//////////////////////////////////////////////////////////////////////////////
// create new thread

// Thread start routine for all newly created threads
static void *thread_native_entry(Thread *thread) {

  thread->record_stack_base_and_size();
  thread->initialize_thread_current();
```



## 线程的创建和销毁

将线程引入虚拟机有两种基本方法：
- 执行 Java 代码，在 `java.lang.Thread` 对象上调用 `start()`；
- 使用 JNI 将现有 native thread  attach 到虚拟机。
- 虚拟机为内部目的创建的其他线程。



虚拟机中每个特定线程都有许多相关联的对象（这里指 C++ 编程语言编写的对象）：

- 代表 Java 代码中线程的 `java.lang.Thread` 实例
- Java code 的 `java.lang.Thread` 实例对应 JVM 的 `JavaThread` 实例。它包含跟踪线程状态的附加信息。 `JavaThread` 拥有对其关联 `java.lang.Thread` 对象的引用（oop 形式），`java.lang.Thread` 对象也存储了对其 `JavaThread` 的引用（以 int `形式）。JavaThread` 还保存一个指向其关联 `OSThread` 实例的引用。
- `OSThread` 实例代表操作系统线程，包含跟踪线程状态所需的附加操作系统级信息。然后， `OSThread` 包含一个平台特定的 “`句柄(handle)`”，用于向操作系统标识实际的线程



### java.lang.Thread 的创建

启动 `java.lang.Thread` 时，虚拟机会创建相关的 `JavaThread` 和 `OSThread` 对象，并最终创建 native thread 。准备好所有虚拟机状态（如`线程本地存储 thread-local storage`和`分配缓冲区 allocation buffers`、`同步对象 synchronization objects`等）后， native thread 就启动了。 native thread 完成初始化后，会执行一个启动方法，该方法会引导到 java.lang.Thread 对象的 `run()` 方法的执行，然后在返回时，在处理任何未捕获的异常后终止线程，并与虚拟机交互以检查终止该线程是否需要终止整个虚拟机。线程终止会释放所有已分配的资源，将 JavaThread 从已知线程集合中删除，调用 OSThread 和 JavaThread 的析构函数，并最终在其初始启动方法完成后停止执行。


对于在 java code 中用 `new java.lang.Thread` 创建的 thread。以下为 add thread list 的 Call stack:
```
libjvm.so!ThreadsList::add_thread(ThreadsList * list, JavaThread * java_thread) (/jdk/src/hotspot/share/runtime/threadSMR.cpp:678)
libjvm.so!ThreadsSMRSupport::add_thread(JavaThread * thread) (/jdk/src/hotspot/share/runtime/threadSMR.cpp:857)
libjvm.so!Threads::add(JavaThread * p, bool force_daemon) (/jdk/src/hotspot/share/runtime/threads.cpp:999)
libjvm.so!JavaThread::prepare(JavaThread * const this, jobject jni_thread, ThreadPriority prio) (/jdk/src/hotspot/share/runtime/javaThread.cpp:1684)
libjvm.so!JVM_StartThread(JNIEnv * env, jobject jthread) (/jdk/src/hotspot/share/prims/jvm.cpp:2991)
[Unknown/Just-In-Time compiled code] (Unknown Source:0)
```

src/hotspot/share/runtime/javaThread.cpp
```c++
void JavaThread::prepare(jobject jni_thread, ThreadPriority prio) {

  assert(Threads_lock->owner() == Thread::current(), "must have threads lock");
  assert(NoPriority <= prio && prio <= MaxPriority, "sanity check");
  // Link Java Thread object <-> C++ Thread

  // Get the C++ thread object (an oop) from the JNI handle (a jthread)
  // and put it into a new Handle.  The Handle "thread_oop" can then
  // be used to pass the C++ thread object to other methods.

  // Set the Java level thread object (jthread) field of the
  // new thread (a JavaThread *) to C++ thread object using the
  // "thread_oop" handle.

  // Set the thread field (a JavaThread *) of the
  // oop representing the java_lang_Thread to the new thread (a JavaThread *).

  Handle thread_oop(Thread::current(),
                    JNIHandles::resolve_non_null(jni_thread));
  assert(InstanceKlass::cast(thread_oop->klass())->is_linked(),
         "must be initialized");
  set_threadOopHandles(thread_oop());

  if (prio == NoPriority) {
    prio = java_lang_Thread::priority(thread_oop());
    assert(prio != NoPriority, "A valid priority should be present");
  }

  // Push the Java priority down to the native thread; needs Threads_lock
  Thread::set_priority(this, prio);

  // Add the new thread to the Threads list and set it in motion.
  // We must have threads lock in order to call Threads::add.
  // It is crucial that we do not block before the thread is
  // added to the Threads list for if a GC happens, then the java_thread oop
  // will not be visited by GC.
  Threads::add(this);
  // Publish the JavaThread* in java.lang.Thread after the JavaThread* is
  // on a ThreadsList. We don't want to wait for the release when the
  // Theads_lock is dropped somewhere in the caller since the JavaThread*
  // is already visible to JVM/TI via the ThreadsList.
  java_lang_Thread::release_set_thread(thread_oop(), this);
}
```


### JNI AttachCurrentThread 的创建

 native thread 使用 JNI 的 `AttachCurrentThread` 函数 attach 到虚拟机。此时会创建一个相关的 OSThread 和 JavaThread 实例，并执行基本初始化。接下来，必须为 attached 的线程创建一个 java.lang.Thread 对象，具体方法是根据线程 attach 时提供的参数，通过反射调用线程类构造函数的 Java 代码来完成。一旦 attach，线程就可以通过其他可用的 JNI 方法调用任何需要的 Java 代码。最后，当 native thread 不想再 attach 虚拟机时，它可以调用 JNI `DetachCurrentThread` 方法使其与虚拟机脱离关系（释放资源、放弃对 java.lang.Thread 实例的引用、析构 JavaThread 和 OSThread 对象等）。

attach native thread 的一个特殊情况是通过 JNI `CreateJavaVM` 调用初始化虚拟机，这可以由本地应用程序或 `启动器 launcher`（java.c）完成。这将导致一系列初始化操作，然后就像调用 AttachCurrentThread 一样的效果。然后，线程可根据需要调用 Java 代码，如应用程序主方法的反射调用。



## 参考
- [OpenJDK Runtime Overiew - Thread Management - openjdk.org](https://openjdk.org/groups/hotspot/docs/RuntimeOverview.html#Thread%20Management|outline:~:text=objectmonitor%22%20structure.%5B8%5D-,Thread%20Management,-Thread%20management%20covers)
