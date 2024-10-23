---
typora-root-url: ../../../
---





# VMThread - VM Operations

## VM Operations

VMThread 线程作为协调者(coordinator) ，循环监听 `safepoint request`  队列中的  `VM_Operation` 请求，并执行队列中的操作。

以下是部分 VM_Operation 的类型 ：

[src/hotspot/share/runtime/vmOperation.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/vmOperation.hpp#L124)

```c++
// VM_Operation 的类型

// The following classes are used for operations
// initiated by a Java thread but that must
// take place in the VMThread.

#define VM_OP_ENUM(type)   VMOp_##type,

// Note: When new VM_XXX comes up, add 'XXX' to the template table.
#define VM_OPS_DO(template)                       \
  template(Halt)                                  \
  template(SafepointALot)                         \
  template(Cleanup)                               \
  template(ThreadDump)                            \
  template(PrintThreads)                          \
  template(FindDeadlocks)                         \
  template(ClearICs)                              \
  template(ForceSafepoint)                        \
  template(DeoptimizeFrame)                       \
  template(DeoptimizeAll)                         \
  template(ZombieAll)                             \
  template(Verify)                                \
  template(HeapDumper)                            \
  template(CollectForMetadataAllocation)          \
  template(CollectForCodeCacheAllocation)         \
  template(GC_HeapInspection)                     \
  template(GenCollectFull)                        \
  template(GenCollectForAllocation)               \
  template(ParallelGCFailedAllocation)            \
  template(ParallelGCSystemGC)                    \
  template(G1CollectForAllocation)                \
  template(G1CollectFull)                         \
  template(G1PauseRemark)                         \
  template(G1PauseCleanup)                        \
  template(G1TryInitiateConcMark)                 \
  template(ZMarkEndOld)                           \
  template(ZMarkEndYoung)                         \
  template(ZMarkFlushOperation)                   \
  template(ZMarkStartYoung)                       \
  template(ZMarkStartYoungAndOld)                 \
  template(ZRelocateStartOld)                     \
  template(ZRelocateStartYoung)                   \
  template(ZRendezvousGCThreads)                  \
  template(ZVerifyOld)                            \
  template(XMarkStart)                            \
  template(XMarkEnd)                              \
  template(XRelocateStart)                        \
  template(XVerify)                               \
  template(HandshakeAllThreads)                   \
  template(PopulateDumpSharedSpace)               \
  template(JNIFunctionTableCopier)                \
  template(RedefineClasses)                       \
  template(GetObjectMonitorUsage)                 \
  template(GetAllStackTraces)                     \
  template(GetThreadListStackTraces)              \
  template(VirtualThreadGetStackTrace)            \
  template(VirtualThreadGetFrameCount)            \
  template(ChangeBreakpoints)                     \
  template(GetOrSetLocal)                         \
  template(VirtualThreadGetOrSetLocal)            \
  template(VirtualThreadGetCurrentLocation)       \
  template(ChangeSingleStep)                      \
  template(SetNotifyJvmtiEventsMode)              \
  template(HeapWalkOperation)                     \
  template(HeapIterateOperation)                  \
  template(ReportJavaOutOfMemory)                 \
  template(JFRCheckpoint)                         \
  template(ShenandoahFullGC)                      \
  template(ShenandoahInitMark)                    \
  template(ShenandoahFinalMarkStartEvac)          \
  template(ShenandoahInitUpdateRefs)              \
  template(ShenandoahFinalUpdateRefs)             \
  template(ShenandoahFinalRoots)                  \
  template(ShenandoahDegeneratedGC)               \
  template(Exit)                                  \
  template(LinuxDllLoad)                          \
  template(WhiteBoxOperation)                     \
  template(JVMCIResizeCounters)                   \
  template(ClassLoaderStatsOperation)             \
  template(ClassLoaderHierarchyOperation)         \
  template(DumpHashtable)                         \
  template(CleanClassLoaderDataMetaspaces)        \
  template(PrintCompileQueue)                     \
  template(PrintClassHierarchy)                   \
  template(PrintClasses)                          \
  template(ICBufferFull)                          \
  template(PrintMetadata)                         \
  template(GTestExecuteAtSafepoint)               \
  template(GTestStopSafepoint)                    \
  template(JFROldObject)                          \
  template(JvmtiPostObjectFree)                   \
  template(RendezvousGCThreads)

class VM_Operation : public StackObj {
 public:
  enum VMOp_Type {
    VM_OPS_DO(VM_OP_ENUM) // 使用了上面的 #define VM_OPS_DO(template) 
    VMOp_Terminating
  };

 private:
  Thread*         _calling_thread;

  // The VM operation name array
  static const char* _names[];

 public:
  VM_Operation() : _calling_thread(nullptr) {}

  // Called by VM thread - does in turn invoke doit(). Do not override this
  void evaluate();

  // evaluate() is called by the VMThread and in turn calls doit().
  // If the thread invoking VMThread::execute((VM_Operation*) is a JavaThread,
  // doit_prologue() is called in that thread before transferring control to
  // the VMThread.
  // If doit_prologue() returns true the VM operation will proceed, and
  // doit_epilogue() will be called by the JavaThread once the VM operation
  // completes. If doit_prologue() returns false the VM operation is cancelled.
  virtual void doit()                            = 0;
  virtual bool doit_prologue()                   { return true; };
  virtual void doit_epilogue()                   {};

  // An operation can either be done inside a safepoint
  // or concurrently with Java threads running.
  virtual bool evaluate_at_safepoint() const { return true; }
```



## VM Thread

### VM Thread 全局变量

src/hotspot/share/runtime/vmThread.cpp

```c++
VMThread*         VMThread::_vm_thread          = nullptr;
VM_Operation*     VMThread::_cur_vm_operation   = nullptr;
VM_Operation*     VMThread::_next_vm_operation  = &cleanup_op; // Prevent any thread from setting an operation until VM thread is ready.
```



全局锁：

[src/hotspot/share/runtime/mutexLocker.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/mutexLocker.hpp#L51)

```c++
extern Monitor* VMOperation_lock;                // a lock on queue of vm_operations waiting to execute
```



### VM Thread 监听 Safepoint Request

[src/hotspot/share/runtime/vmThread.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/vmThread.cpp#L487)

```c++
void VMThread::loop() {
  assert(_cur_vm_operation == nullptr, "no current one should be executing");

  SafepointSynchronize::init(_vm_thread);

  // Need to set a calling thread for ops not passed
  // via the normal way.
  cleanup_op.set_calling_thread(_vm_thread);
  safepointALot_op.set_calling_thread(_vm_thread);

  while (true) {
    if (should_terminate()) break;
    wait_for_operation();
    if (should_terminate()) break;
    assert(_next_vm_operation != nullptr, "Must have one");
    inner_execute(_next_vm_operation);
  }
}
```



可能是分配内存失败触发 GC，也可能是其它原因，Java 线程向  `VM Thread` 提出了进入 safepoint 的请求(`VM_Operation`)，请求中带上 `safepoint operation` 参数，参数其实是  STOP THE WORLD(STW) 后要执行的 Callback 操作 。

```c++
void VMThread::inner_execute(VM_Operation* op) {
...
  if (_cur_vm_operation->evaluate_at_safepoint() &&
      !SafepointSynchronize::is_at_safepoint()) {
    SafepointSynchronize::begin(); // <<<----
    if (has_timeout_task) {
      _timeout_task->arm(_cur_vm_operation->name());
    }
    end_safepoint = true;
  }

  evaluate_operation(_cur_vm_operation); // <<<----

  if (end_safepoint) {
    if (has_timeout_task) {
      _timeout_task->disarm();
    }
    SafepointSynchronize::end(); // <<<----
  }

...
}
```

更详细可见本书的 [Safepoint](/exec-engine/safepoint/safepoint.md)  一节。



## VM Operations 与 Safepoints 的关系



VMThread 会一直等待 VM Operation 出现在 `VMOperationQueue` 中，然后执行这些VM Operation。通常，这些操作需要虚拟机到达 Safepoint 后才能执行，因此会转给 VMThread。简单地说，当虚拟机处于 Safepoint 时，虚拟机内的所有线程都会被阻塞(blocked)，并且在 Safepoint 期间，在执行 native code 的任何线程都无法返回到虚拟机。这意味着在执行 VM operation 时，不会有线程修改 Java 堆，而且所有线程都处于这样一种状态：它们的 Java stack 是不变的，可以被 GC 线程等检查。

大家最熟悉的 VM operation 是 GC，或者更具体地说是许多 GC 算法中常见的 “Stop The World ”阶段的 GC。但除了 GC 以外，还有许多其他基于 Safepoint 的 VM operation ，例如：有偏见的锁定撤销(biased locking revocation)、thread stack dumps、thread suspension 或 thread stopping（即 java.lang.Thread.stop() 方法）以及通过 JVMTI 请求的许多观察/修改操作。

许多 VM operation 是同步的，即请求者会阻塞直到操作完成，但也有一些是异步或并发的，即请求者可以与 VMThread 并行（当然，前提是没有启动 Safepoint ）。

Safepoint 是通过一种基于轮询的合作机制发起的。简单来说，每隔一段时间就会有一个线程查询 "我是否应该在 Safepoint 阻塞 ？高效地完成这个查询并不简单。在线程状态转换过程中，就是经常查询的地方。一旦发起 Safepoint 请求，VMThread 必须等待所有线程都处于 Safepoint 安全状态后，才能继续执行 VM operation 。在 Safepoint 期间，`Threads_lock` 用于阻塞任何正在运行的线程，VMThread 最终会在 VM Operation 执行完毕后释放 `Threads_lock`。



关于 VM Operations 与 Safepoints 的关系，更详细可见本书的 [Safepoint](/exec-engine/safepoint/safepoint.md)  一节。



(vm-operation-request)=

## 一个应用线程 Request VM Operation

应用线程如需要执行 VM Operation 时，就会向 VM Thread 提交 VM Operation 请求。如内存分配失败，并触发 GC 时。

[src/hotspot/share/runtime/vmThread.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/vmThread.cpp#L531)

```c++
void VMThread::execute(VM_Operation* op) {
  Thread* t = Thread::current();

  if (t->is_VM_thread()) {
    op->set_calling_thread(t);
    ((VMThread*)t)->inner_execute(op);
    return;
  }

  // Avoid re-entrant attempts to gc-a-lot
  SkipGCALot sgcalot(t);

  // JavaThread or WatcherThread
  if (t->is_Java_thread()) {
    JavaThread::cast(t)->check_for_valid_safepoint_state();
  }

  // New request from Java thread, evaluate prologue
  if (!op->doit_prologue()) { // <<<<  (prologue:序幕),是 virtual function，具体实现由 VM Operation 子类实现
    return;   // op was cancelled
  }

  op->set_calling_thread(t);

  wait_until_executed(op); // <<<< 提交 VM Operation Request，并等待  VM Operation Request 执行完成

  op->doit_epilogue(); // <<<< epilogue:结语，相对于上面的 prologue:序幕, 是 virtual function，具体实现由 VM Operation 子类实现
}
```



一个具体实验示例见本书的 [GC 主要流程 - 内存分配失败触发 GC](memory/gc/base-gc-process.md#memory-allocation-failure-triggers-gc) 。



```c++
void VM_Operation::set_calling_thread(Thread* thread) {
  _calling_thread = thread;
}
```



[src/hotspot/share/runtime/vmThread.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/vmThread.cpp#L353)

```c++
void VMThread::wait_until_executed(VM_Operation* op) {
  MonitorLocker ml(VMOperation_lock,
                   Thread::current()->is_Java_thread() ?
                     Mutex::_safepoint_check_flag :
                     Mutex::_no_safepoint_check_flag);
  {
    TraceTime timer("Installing VM operation", TRACETIME_LOG(Trace, vmthread));
    while (true) {
      if (VMThread::vm_thread()->set_next_operation(op)) { // <<<< 提交 VM Operation Request
        ml.notify_all();
        break;
      }
      // Wait to install this operation as the next operation in the VM Thread
      log_trace(vmthread)("A VM operation already set, waiting");
      ml.wait();
    }
  }
  {
    // Wait until the operation has been processed
    TraceTime timer("Waiting for VM operation to be completed", TRACETIME_LOG(Trace, vmthread));
    // _next_vm_operation is cleared holding VMOperation_lock after it has been
    // executed. We wait until _next_vm_operation is not our op.
    while (_next_vm_operation == op) {
      // VM Thread can process it once we unlock the mutex on wait.
      ml.wait();// 并等待  VM Operation Request 执行完成
    }
  }
}
```



```c++
bool VMThread::set_next_operation(VM_Operation *op) {
  if (_next_vm_operation != nullptr) {
    return false;
  }
  log_debug(vmthread)("Adding VM operation: %s", op->name());

  _next_vm_operation = op;

  HOTSPOT_VMOPS_REQUEST(
                   (char *) op->name(), strlen(op->name()),
                   op->evaluate_at_safepoint() ? 0 : 1); // <<<< 提交 VM Operation Request
  return true;
}
```



本以为 vm operations 应该是以队列保存，但实现代码可以看出，是一个变量： `_next_vm_operation` 。即不是以队列支持缓存 VM Operations，而只支持单个，这样的设计当然是有考虑的。



```c++
void VMThread::wait_until_executed(VM_Operation* op) {
  MonitorLocker ml(VMOperation_lock,
                   Thread::current()->is_Java_thread() ?
                     Mutex::_safepoint_check_flag :
                     Mutex::_no_safepoint_check_flag);
  {
    TraceTime timer("Installing VM operation", TRACETIME_LOG(Trace, vmthread));
    while (true) {
      if (VMThread::vm_thread()->set_next_operation(op)) {
        ml.notify_all();
        break;
      }
      // Wait to install this operation as the next operation in the VM Thread
      log_trace(vmthread)("A VM operation already set, waiting");
      ml.wait();
    }
  }
  {
    // Wait until the operation has been processed
    TraceTime timer("Waiting for VM operation to be completed", TRACETIME_LOG(Trace, vmthread));
    // _next_vm_operation is cleared holding VMOperation_lock after it has been
    // executed. We wait until _next_vm_operation is not our op.
    while (_next_vm_operation == op) {
      // VM Thread can process it once we unlock the mutex on wait.
      ml.wait();
    }
  }
}
```



本书的实验 [GC 主要流程 - 内存分配失败触发 GC](memory/gc/base-gc-process.md#memory-allocation-failure-triggers-gc)  中，用 gdb 输出 VMThread 和 VM Operation Request Thread(发起VM Operation 请求的应用线程) 的 call stack 可以直观说明线程的交互：



VM Operation Request Thread(发起VM Operation 请求的应用线程)  的 call stack:

```
libc.so.6!__futex_abstimed_wait_common64(int private, _Bool cancel, const struct timespec * abstime, int op, unsigned int expected, unsigned int * futex_word) (futex-internal.c:57)
libc.so.6!__futex_abstimed_wait_common(_Bool cancel, int private, const struct timespec * abstime, clockid_t clockid, unsigned int expected, unsigned int * futex_word) (futex-internal.c:87)
libc.so.6!__GI___futex_abstimed_wait_cancelable64(unsigned int * futex_word, unsigned int expected, clockid_t clockid, const struct timespec * abstime, int private) (futex-internal.c:139)
libc.so.6!__pthread_cond_wait_common(pthread_mutex_t * mutex, pthread_cond_t * cond) (pthread_cond_wait.c:503)
libc.so.6!___pthread_cond_wait(pthread_cond_t * cond, pthread_mutex_t * mutex) (pthread_cond_wait.c:627)
libjvm.so!PlatformMonitor::wait(PlatformMonitor * const this, uint64_t millis) (/jdk/src/hotspot/os/posix/os_posix.cpp:1900)
libjvm.so!Monitor::wait(Monitor * const this, uint64_t timeout) (/jdk/src/hotspot/share/runtime/mutex.cpp:254)
libjvm.so!MonitorLocker::wait(MonitorLocker * const this, int64_t timeout) (/jdk/src/hotspot/share/runtime/mutexLocker.hpp:255)
libjvm.so!VMThread::wait_until_executed(VM_Operation * op) (/jdk/src/hotspot/share/runtime/vmThread.cpp:377)
libjvm.so!VMThread::execute(VM_Operation * op) (/jdk/src/hotspot/share/runtime/vmThread.cpp:555)
libjvm.so!GenCollectedHeap::mem_allocate_work(GenCollectedHeap * const this, size_t size, bool is_tlab) (/jdk/src/hotspot/share/gc/shared/genCollectedHeap.cpp:355)
libjvm.so!GenCollectedHeap::mem_allocate(GenCollectedHeap * const this, size_t size, bool * gc_overhead_limit_was_exceeded) (/jdk/src/hotspot/share/gc/shared/genCollectedHeap.cpp:398)
libjvm.so!MemAllocator::mem_allocate_outside_tlab(const MemAllocator * const this, MemAllocator::Allocation & allocation) (/jdk/src/hotspot/share/gc/shared/memAllocator.cpp:240)
libjvm.so!MemAllocator::mem_allocate_slow(const MemAllocator * const this, MemAllocator::Allocation & allocation) (/jdk/src/hotspot/share/gc/shared/memAllocator.cpp:348)
libjvm.so!MemAllocator::mem_allocate(const MemAllocator * const this, MemAllocator::Allocation & allocation) (/jdk/src/hotspot/share/gc/shared/memAllocator.cpp:360)
libjvm.so!MemAllocator::allocate(const MemAllocator * const this) (/jdk/src/hotspot/share/gc/shared/memAllocator.cpp:367)
libjvm.so!CollectedHeap::array_allocate(CollectedHeap * const this, Klass * klass, size_t size, int length, bool do_zero, JavaThread * __the_thread__) (/jdk/src/hotspot/share/gc/shared/collectedHeap.inline.hpp:41)
libjvm.so!TypeArrayKlass::allocate_common(TypeArrayKlass * const this, int length, bool do_zero, JavaThread * __the_thread__) (/jdk/src/hotspot/share/oops/typeArrayKlass.cpp:93)
libjvm.so!TypeArrayKlass::allocate(TypeArrayKlass * const this, int length, JavaThread * __the_thread__) (/jdk/src/hotspot/share/oops/typeArrayKlass.hpp:68)
libjvm.so!oopFactory::new_typeArray(BasicType type, int length, JavaThread * __the_thread__) (/jdk/src/hotspot/share/memory/oopFactory.cpp:93)
```



VMThread 接收与处理 VM Operation Request 的  call stack:

```
libjvm.so!VM_GenCollectForAllocation::doit(VM_GenCollectForAllocation * const this) (/jdk/src/hotspot/share/gc/shared/gcVMOperations.cpp:199)
libjvm.so!VM_Operation::evaluate(VM_Operation * const this) (/jdk/src/hotspot/share/runtime/vmOperations.cpp:71)
libjvm.so!VMThread::evaluate_operation(VMThread * const this, VM_Operation * op) (/jdk/src/hotspot/share/runtime/vmThread.cpp:281)
libjvm.so!VMThread::inner_execute(VMThread * const this, VM_Operation * op) (/jdk/src/hotspot/share/runtime/vmThread.cpp:435)
libjvm.so!VMThread::loop(VMThread * const this) (/jdk/src/hotspot/share/runtime/vmThread.cpp:502)
libjvm.so!VMThread::run(VMThread * const this) (/jdk/src/hotspot/share/runtime/vmThread.cpp:175)
libjvm.so!Thread::call_run(Thread * const this) (/jdk/src/hotspot/share/runtime/thread.cpp:217)
libjvm.so!thread_native_entry(Thread * thread) (/jdk/src/hotspot/os/linux/os_linux.cpp:778)
libc.so.6!start_thread(void * arg) (pthread_create.c:442)
libc.so.6!clone3() (clone3.S:81)
```





## 参考

- [OpenJDK Runtime Overiew - Thread Management - openjdk.org](https://openjdk.org/groups/hotspot/docs/RuntimeOverview.html#Thread%20Management|outline:~:text=VM%20Operations%20and%20Safepoints)

