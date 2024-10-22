# Thread 管理



## ThreadsList

Thread C++ 对象：

- 所有线程都是`Thread C++ class`的实例  ；
- 所有执行 Java 代码的线程都是 `JavaThread C++ class（ Thread C++ class 的子类）` 实例。

虚拟机会在一个称为 `ThreadsList ThreadsSMRSupport::_java_thread_list` 的链接列表中跟踪所有线程，该列表受 `Threads_lock` 保护，`Threads_lock` 是虚拟机中使用的重要 `同步锁` 之一。

src/hotspot/share/runtime/threadSMR.hpp
```c++
class ThreadsSMRSupport : AllStatic {
  static ThreadsList           _bootstrap_list;
  static ThreadsList* volatile _java_thread_list;

  static void add_thread(JavaThread *thread);
  static ThreadsList* get_java_thread_list();

```

[src/hotspot/share/runtime/threadSMR.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/threadSMR.cpp#L91)
```c++
// The bootstrap list is empty and cannot be freed.
ThreadsList ThreadsSMRSupport::_bootstrap_list{0};

// This is the VM's current "threads list" and it contains all of
// the JavaThreads the VM considers to be alive at this moment in
// time. The other ThreadsList objects in the VM contain past
// snapshots of the "threads list". _java_thread_list is initially
// set to _bootstrap_list so that we can detect when we have a very
// early use of a ThreadsListHandle.
ThreadsList* volatile ThreadsSMRSupport::_java_thread_list = &_bootstrap_list;
```

src/hotspot/share/runtime/threadSMR.inline.hpp
```c++
inline ThreadsList* ThreadsSMRSupport::get_java_thread_list() {
  return (ThreadsList*)Atomic::load_acquire(&_java_thread_list);
}
```

[src/hotspot/share/runtime/threadSMR.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/threadSMR.hpp#L162)
```c++
// A fast list of JavaThreads.
//
class ThreadsList : public CHeapObj<mtThread> {
  uint _magic;
  const uint _length;
  ThreadsList* _next_list;
  JavaThread *const *const _threads;
  volatile intx _nested_handle_cnt;
  static ThreadsList* add_thread(ThreadsList* list, JavaThread* java_thread);
  static ThreadsList* remove_thread(ThreadsList* list, JavaThread* java_thread);
```


JVM 初始化阶段初始化 `ThreadsList ThreadsSMRSupport::_bootstrap_list`：
```
1: libjvm.so!ThreadsList::ThreadsList(ThreadsList * const this, int entries) /jdk/src/hotspot/share/runtime/threadSMR.cpp:660)
2: libjvm.so!__static_initialization_and_destruction_0(int __initialize_p, int __priority) /jdk/src/hotspot/share/runtime/threadSMR.cpp:83)
3: libjvm.so!_GLOBAL__sub_I_threadSMR.cpp(void)() /jdk/src/hotspot/share/runtime/threadSMR.cpp:1290)
4: ...
5: ___dlopen(const char * file, int mode) (dlopen.c:81)
6: libjli.so!LoadJavaVM(const char * jvmpath, InvocationFunctions * ifn) /jdk/src/java.base/unix/native/libjli/java_md.c:539)
7: libjli.so!JLI_Launch(int argc, char ** argv, int jargc, const char ** jargv, int appclassc, const char ** appclassv, const char * fullversion, const char * dotversion, const char * pname, const char * lname, jboolean javaargs, jboolean cpwildcard, jboolean javaw, jint ergo) /jdk/src/java.base/share/native/libjli/java.c:295)
8: main(int argc, char ** argv) /jdk/src/java.base/share/native/launcher/main.c:166)
```

Java main thead 初始化阶段初始化  `ThreadsList ThreadsSMRSupport::_java_thread_list`：
```
01: libjvm.so!ThreadsList::ThreadsList(ThreadsList * const this, int entries) /jdk/src/hotspot/share/runtime/threadSMR.cpp:660)
02: libjvm.so!ThreadsList::add_thread(ThreadsList * list, JavaThread * java_thread) /jdk/src/hotspot/share/runtime/threadSMR.cpp:681)
03: libjvm.so!ThreadsSMRSupport::add_thread(JavaThread * thread) /jdk/src/hotspot/share/runtime/threadSMR.cpp:857)
04: libjvm.so!Threads::add(JavaThread * p, bool force_daemon) /jdk/src/hotspot/share/runtime/threads.cpp:999)
05: libjvm.so!Threads::create_vm(JavaVMInitArgs * args, bool * canTryAgain) /jdk/src/hotspot/share/runtime/threads.cpp:565)
06: libjvm.so!JNI_CreateJavaVM_inner(JavaVM ** vm, void ** penv, void * args) /jdk/src/hotspot/share/prims/jni.cpp:3577)
07: libjvm.so!JNI_CreateJavaVM(JavaVM ** vm, void ** penv, void * args) /jdk/src/hotspot/share/prims/jni.cpp:3668)
08: libjli.so!InitializeJVM(JavaVM ** pvm, JNIEnv ** penv, InvocationFunctions * ifn) /jdk/src/java.base/share/native/libjli/java.c:1506)
09: libjli.so!JavaMain(void * _args) /jdk/src/java.base/share/native/libjli/java.c:415)
10: libjli.so!ThreadJavaMain(void * args) /jdk/src/java.base/unix/native/libjli/java_md.c:650)
11: start_thread(void * arg) (pthread_create.c:442)
12: clone3() (clone3.S:81)
```

### Threads_lock
虚拟机会在一个称为 `ThreadsList ThreadsSMRSupport::_java_thread_list` 的链接列表中跟踪所有线程，该列表受 `Threads_lock` 保护，`Threads_lock` 是虚拟机中使用的重要 `同步锁` 之一。

[src/hotspot/share/runtime/mutexLocker.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/mutexLocker.hpp#L51)

```c++
extern Monitor* Threads_lock;                    // a lock on the Threads table of active Java threads
```

### Iterate thread list


Iterate thread list. 可以保证在替代 thread list 过程中 `JavaThread` c++ 对象不会被 c++ delete 。但不保存 `JavaThread` 对应的线程不会退出。

[src/hotspot/share/runtime/threadSMR.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/threadSMR.hpp#L41)
```c++
// Thread Safe Memory Reclamation (Thread-SMR) support.
//
// ThreadsListHandles are used to safely perform operations on one or more
// threads without the risk of the thread or threads exiting during the
// operation. It is no longer necessary to hold the Threads_lock to safely
// perform an operation on a target thread.
//
// There are several different ways to refer to java.lang.Thread objects
// so we have a few ways to get a protected JavaThread *:
//
// JNI jobject example:
//   jobject jthread = ...;
//   :
//   ThreadsListHandle tlh;
//   JavaThread* jt = nullptr;
//   bool is_alive = tlh.cv_internal_thread_to_JavaThread(jthread, &jt, nullptr);
//   if (is_alive) {
//     :  // do stuff with 'jt'...
//   }
//
// JVM/TI jthread example:
//   jthread thread = ...;
//   :
//   JavaThread* jt = nullptr;
//   ThreadsListHandle tlh;
//   jvmtiError err = JvmtiExport::cv_external_thread_to_JavaThread(tlh.list(), thread, &jt, nullptr);
//   if (err != JVMTI_ERROR_NONE) {
//     return err;
//   }
//   :  // do stuff with 'jt'...
//
// JVM/TI oop example (this one should be very rare):
//   oop thread_obj = ...;
//   :
//   JavaThread *jt = nullptr;
//   ThreadsListHandle tlh;
//   jvmtiError err = JvmtiExport::cv_oop_to_JavaThread(tlh.list(), thread_obj, &jt);
//   if (err != JVMTI_ERROR_NONE) {
//     return err;
//   }
//   :  // do stuff with 'jt'...
//
// A JavaThread * that is included in the ThreadsList that is held by
// a ThreadsListHandle is protected as long as the ThreadsListHandle
// remains in scope. The target JavaThread * may have logically exited,
// but that target JavaThread * will not be deleted until it is no
// longer protected by a ThreadsListHandle.
//
// SMR Support for the Threads class.
//
...
// This stack allocated ThreadsListHandle keeps all JavaThreads in the
// ThreadsList from being deleted until it is safe.
//
class ThreadsListHandle : public StackObj {
  friend class ThreadsListHandleTest;  // for _list_ptr access

  SafeThreadsListPtr _list_ptr;
  elapsedTimer _timer;  // Enabled via -XX:+EnableThreadSMRStatistics.

public:
  ThreadsListHandle(Thread *self = Thread::current());
  ~ThreadsListHandle();

  ThreadsList *list() const {
    return _list_ptr.list();
  }

  using Iterator = ThreadsList::Iterator;
  inline Iterator begin();
  inline Iterator end();

  bool cv_internal_thread_to_JavaThread(jobject jthread, JavaThread ** jt_pp, oop * thread_oop_p);

  bool includes(JavaThread* p) {
    return list()->includes(p);
  }

  uint length() const {
    return list()->length();
  }

  JavaThread *thread_at(uint i) const {
    return list()->thread_at(i);
  }
};
...
// This stack allocated ThreadsListHandle and JavaThreadIterator combo
// is used to walk the ThreadsList in the included ThreadsListHandle
// using the following style:
//
//   for (JavaThreadIteratorWithHandle jtiwh; JavaThread *jt = jtiwh.next(); ) {
//     ...
//   }
//
class JavaThreadIteratorWithHandle : public StackObj {
  ThreadsListHandle _tlh;
  uint _index;

public:
  JavaThreadIteratorWithHandle() : _index(0) {}

  uint length() const {
    return _tlh.length();
  }

  ThreadsList *list() const {
    return _tlh.list();
  }

  JavaThread *next() {
    if (_index >= length()) {
      return nullptr;
    }
    return _tlh.list()->thread_at(_index++);
  }

  void rewind() {
    _index = 0;
  }
};
```

## thread 的注册

### main java thread 的注册

Call stack 如下：

```
01: libjvm.so!ThreadsList::ThreadsList(ThreadsList * const this, int entries) /jdk/src/hotspot/share/runtime/threadSMR.cpp:660)
02: libjvm.so!ThreadsList::add_thread(ThreadsList * list, JavaThread * java_thread) /jdk/src/hotspot/share/runtime/threadSMR.cpp:681)
03: libjvm.so!ThreadsSMRSupport::add_thread(JavaThread * thread) /jdk/src/hotspot/share/runtime/threadSMR.cpp:857)
04: libjvm.so!Threads::add(JavaThread * p, bool force_daemon) /jdk/src/hotspot/share/runtime/threads.cpp:999)
05: libjvm.so!Threads::create_vm(JavaVMInitArgs * args, bool * canTryAgain) /jdk/src/hotspot/share/runtime/threads.cpp:565)
06: libjvm.so!JNI_CreateJavaVM_inner(JavaVM ** vm, void ** penv, void * args) /jdk/src/hotspot/share/prims/jni.cpp:3577)
07: libjvm.so!JNI_CreateJavaVM(JavaVM ** vm, void ** penv, void * args) /jdk/src/hotspot/share/prims/jni.cpp:3668)
08: libjli.so!InitializeJVM(JavaVM ** pvm, JNIEnv ** penv, InvocationFunctions * ifn) /jdk/src/java.base/share/native/libjli/java.c:1506)
09: libjli.so!JavaMain(void * _args) /jdk/src/java.base/share/native/libjli/java.c:415)
10: libjli.so!ThreadJavaMain(void * args) /jdk/src/java.base/unix/native/libjli/java_md.c:650)
11: start_thread(void * arg) (pthread_create.c:442)
12: clone3() (clone3.S:81)
```

而其中 `Threads::create_vm(...)` 中创建了 main java thread 的 `JavaThread` 对象：
[src/hotspot/share/runtime/threads.cpp]((https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/threads.cpp#L523))
```c++
jint Threads::create_vm(JavaVMInitArgs* args, bool* canTryAgain) {
...
  // Initialize OopStorage for threadObj
  JavaThread::_thread_oop_storage = OopStorageSet::create_strong("Thread OopStorage", mtThread);

  // Attach the main thread to this os thread
  JavaThread* main_thread = new JavaThread();
  main_thread->set_thread_state(_thread_in_vm);
  main_thread->initialize_thread_current();
  // must do this before set_active_handles
  main_thread->record_stack_base_and_size();
  main_thread->register_thread_stack_with_NMT();
  main_thread->set_active_handles(JNIHandleBlock::allocate_block());
  ...
  // Add main_thread to threads list to finish barrier setup with
  // on_thread_attach.  Should be before starting to build Java objects in
  // init_globals2, which invokes barriers.
  {
    MutexLocker mu(Threads_lock);
    Threads::add(main_thread);
  }

```

可见，对 thread list 的 add，使用了上文中的 `Threads_lock` 。


### pure java Thread 的注册

对于在 java code 中用 `new java.lang.Thread` 创建的 thread.

Call stack:

```
libjvm.so!ThreadsList::add_thread(ThreadsList * list, JavaThread * java_thread) (/jdk/src/hotspot/share/runtime/threadSMR.cpp:678)
libjvm.so!ThreadsSMRSupport::add_thread(JavaThread * thread) (/jdk/src/hotspot/share/runtime/threadSMR.cpp:857)
libjvm.so!Threads::add(JavaThread * p, bool force_daemon) (/jdk/src/hotspot/share/runtime/threads.cpp:999)
libjvm.so!JavaThread::prepare(JavaThread * const this, jobject jni_thread, ThreadPriority prio) (/jdk/src/hotspot/share/runtime/javaThread.cpp:1684)
libjvm.so!JVM_StartThread(JNIEnv * env, jobject jthread) (/jdk/src/hotspot/share/prims/jvm.cpp:2991)
[Unknown/Just-In-Time compiled code] (Unknown Source:0)
```

