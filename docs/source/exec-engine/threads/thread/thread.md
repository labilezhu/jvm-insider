# Thread


需要 JVM 管理控制的线程有几类：
- 由 Java 代码（无论是应用程序代码还是 Java 库代码）创建的线程。
- 直接 attach 到虚拟机的 native thread
- 为各种目的创建的 `internal VM threads`


JVM 中 Thread 的分类(hierarchy) 如下。比较意外的是 `CompilerThread` 是属于 `JavaThead` 。

[src/hotspot/share/runtime/thread.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/thread.hpp#L69)
```c++
// Class hierarchy
// - Thread
//   - JavaThread
//     - various subclasses eg CompilerThread, ServiceThread
//   - NonJavaThread
//     - NamedThread
//       - VMThread
//       - ConcurrentGCThread
//       - WorkerThread
//     - WatcherThread
//     - JfrThreadSampler
//     - LogAsyncWriter
//
// All Thread subclasses must be either JavaThread or NonJavaThread.
// This means !t->is_Java_thread() iff t is a NonJavaThread, or t is
// a partially constructed/destroyed Thread.

// Thread execution sequence and actions:
// All threads:
//  - thread_native_entry  // per-OS native entry point
//    - stack initialization
//    - other OS-level initialization (signal masks etc)
//    - handshake with creating thread (if not started suspended)
//    - this->call_run()  // common shared entry point
//      - shared common initialization
//      - this->pre_run()  // virtual per-thread-type initialization
//      - this->run()      // virtual per-thread-type "main" logic
//      - shared common tear-down
//      - this->post_run()  // virtual per-thread-type tear-down
//      - // 'this' no longer referenceable
//    - OS-level tear-down (minimal)
//    - final logging
//
// For JavaThread:
//   - this->run()  // virtual but not normally overridden
//     - this->thread_main_inner()  // extra call level to ensure correct stack calculations
//       - this->entry_point()  // set differently for each kind of JavaThread

class Thread: public ThreadShadow {
  // Current thread is maintained as a thread-local variable
  static THREAD_LOCAL Thread* _thr_current;

 private:
  // Thread local data area available to the GC. The internal
  // structure and contents of this data area is GC-specific.
  // Only GC and GC barrier code should access this data area.
  GCThreadLocalData _gc_data;
  ThreadsList* volatile _threads_hazard_ptr;
  SafeThreadsListPtr*   _threads_list_ptr;
 private:
  ThreadLocalAllocBuffer _tlab;                 // Thread-local eden
  ThreadStatisticalInfo _statistical_info;      // Statistics about the thread
protected:
  // OS data associated with the thread
  OSThread* _osthread;  // Platform-specific thread information
  // Support for stack overflow handling, get_thread, etc.
  address          _stack_base;
 private:
  // Deadlock detection support for Mutex locks. List of locks own by thread.
  Mutex* _owned_locks;

```