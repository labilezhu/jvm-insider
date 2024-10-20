---
typora-root-url: ../../../
---


# Java Thread


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
```


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



