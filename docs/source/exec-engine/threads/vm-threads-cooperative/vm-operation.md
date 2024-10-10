---
typora-root-url: ../../../
---





# VM Operations







VMThread 线程作为协调者(coordinator) ，循环监听 `safepoint request`  队列中的  `VM_Operation` 请求，并执行队列中的操作。



[src/hotspot/share/runtime/vmOperation.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/vmOperation.hpp#L124)

```c++
// VM_Operation 的类型
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
    VM_OPS_DO(VM_OP_ENUM)
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





## VM Operations 与 Safepoints 的关系



VMThread 会一直等待 VM Operation 出现在 `VMOperationQueue` 中，然后执行这些VM Operation。通常，这些操作需要虚拟机到达 Safepoint 后才能执行，因此会转给 VMThread。简单地说，当虚拟机处于 Safepoint 时，虚拟机内的所有线程都会被阻塞(blocked)，并且在 Safepoint 期间，在执行 native code 的任何线程都无法返回到虚拟机。这意味着在执行 VM operation 时，不会有线程修改 Java 堆，而且所有线程都处于这样一种状态：它们的 Java stack 是不变的，可以被 GC 线程等检查。

大家最熟悉的 VM operation 是 GC，或者更具体地说是许多 GC 算法中常见的 “Stop The World ”阶段的 GC。但除了 GC 以外，还有许多其他基于 Safepoint 的 VM operation ，例如：有偏见的锁定撤销(biased locking revocation)、thread stack dumps、thread suspension 或 thread stopping（即 java.lang.Thread.stop() 方法）以及通过 JVMTI 请求的许多观察/修改操作。

许多 VM operation 是同步的，即请求者会阻塞直到操作完成，但也有一些是异步或并发的，即请求者可以与 VMThread 并行（当然，前提是没有启动 Safepoint ）。

Safepoint 是通过一种基于轮询的合作机制发起的。简单来说，每隔一段时间就会有一个线程查询 "我是否应该在 Safepoint 阻塞 ？高效地完成这个查询并不简单。在线程状态转换过程中，就是经常查询的地方。一旦发起 Safepoint 请求，VMThread 必须等待所有线程都处于 Safepoint 安全状态后，才能继续执行 VM operation 。在 Safepoint 期间，`Threads_lock` 用于阻塞任何正在运行的线程，VMThread 最终会在 VM Operation 执行完毕后释放 `Threads_lock`。



关于 VM Operations 与 Safepoints 的关系，更详细可见本书的 [Safepoint](/exec-engine/safepoint/safepoint.md)  一节。




















































## 参考
- [OpenJDK Runtime Overiew - Thread Management - openjdk.org](https://openjdk.org/groups/hotspot/docs/RuntimeOverview.html#Thread%20Management|outline:~:text=VM%20Operations%20and%20Safepoints)

