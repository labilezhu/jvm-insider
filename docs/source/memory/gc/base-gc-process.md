# GC 主要流程

## 触发 GC

(memory-allocation-failure-triggers-gc)=

### 内存分配失败触发 GC

实验环境：

以下结合示例代码 [SafepointGDB.java](https://github.com/labilezhu/pub-diy/blob/f9e68a10cc79a4aa24c33d2724967a527c90eb25/jvm-insider-book/memory/java-obj-layout/src/com/mygraphql/jvm/insider/safepoint/SafepointGDB.java#L14) ，以及本书实验环境一节 [用 VSCode gdb 去 debug JVM](/appendix-lab-env/debug-jdk/debug-jdk-tools.md#vscode-gdb-attach-jvm-process) 的环境，来理论结合实验 fact check 分析一下内存分配失败后诱发 GC 的 Safepoint 流程。



```bash
bash -c 'echo $$ > /tmp/jvm-insider.pid && exec setarch $(uname -m) --addr-no-randomize /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java -XX:+AlwaysPreTouch  -Xms100m -Xmx100m -XX:MaxTenuringThreshold=5 -server -XX:+UseSerialGC  -XX:-UseCompressedOops -XX:+UnlockDiagnosticVMOptions "-Xlog:gc*=debug::tid" -Xlog:safepoint=debug::tid -cp /home/labile/pub-diy/jvm-insider-book/memory/java-obj-layout/out/production/java-obj-layout com.mygraphql.jvm.insider.safepoint.SafepointGDB'
```

示例代码 [SafepointGDB.java](https://github.com/labilezhu/pub-diy/blob/f9e68a10cc79a4aa24c33d2724967a527c90eb25/jvm-insider-book/memory/java-obj-layout/src/com/mygraphql/jvm/insider/safepoint/SafepointGDB.java#L14) 中，累计多次  `new byte[1024*1024*5]` 会触发内存分配失败，并触发 GC ：

```
01: libjvm.so!VM_GC_Operation::VM_GC_Operation(VM_GC_Operation * const this, uint gc_count_before, GCCause::Cause _cause, uint full_gc_count_before, bool full) (/jdk/src/hotspot/share/gc/shared/gcVMOperations.hpp:119)
02: libjvm.so!VM_CollectForAllocation::VM_CollectForAllocation(VM_CollectForAllocation * const this, size_t word_size, uint gc_count_before, GCCause::Cause cause) (/jdk/src/hotspot/share/gc/shared/gcVMOperations.cpp:294)
03: libjvm.so!VM_GenCollectForAllocation::VM_GenCollectForAllocation(VM_GenCollectForAllocation * const this, size_t word_size, bool tlab, uint gc_count_before) (/jdk/src/hotspot/share/gc/shared/gcVMOperations.hpp:203)
04: libjvm.so!GenCollectedHeap::mem_allocate_work(GenCollectedHeap * const this, size_t size, bool is_tlab) (/jdk/src/hotspot/share/gc/shared/genCollectedHeap.cpp:354)
05: libjvm.so!GenCollectedHeap::mem_allocate(GenCollectedHeap * const this, size_t size, bool * gc_overhead_limit_was_exceeded) (/jdk/src/hotspot/share/gc/shared/genCollectedHeap.cpp:398)
06: libjvm.so!MemAllocator::mem_allocate_outside_tlab(const MemAllocator * const this, MemAllocator::Allocation & allocation) (/jdk/src/hotspot/share/gc/shared/memAllocator.cpp:240)
07: libjvm.so!MemAllocator::mem_allocate_slow(const MemAllocator * const this, MemAllocator::Allocation & allocation) (/jdk/src/hotspot/share/gc/shared/memAllocator.cpp:348)
08: libjvm.so!MemAllocator::mem_allocate(const MemAllocator * const this, MemAllocator::Allocation & allocation) (/jdk/src/hotspot/share/gc/shared/memAllocator.cpp:360)
09: libjvm.so!MemAllocator::allocate(const MemAllocator * const this) (/jdk/src/hotspot/share/gc/shared/memAllocator.cpp:367)
10: libjvm.so!CollectedHeap::array_allocate(CollectedHeap * const this, Klass * klass, size_t size, int length, bool do_zero, JavaThread * __the_thread__) (/jdk/src/hotspot/share/gc/shared/collectedHeap.inline.hpp:41)
11: libjvm.so!TypeArrayKlass::allocate_common(TypeArrayKlass * const this, int length, bool do_zero, JavaThread * __the_thread__) (/jdk/src/hotspot/share/oops/typeArrayKlass.cpp:93)
12: libjvm.so!TypeArrayKlass::allocate(TypeArrayKlass * const this, int length, JavaThread * __the_thread__) (/jdk/src/hotspot/share/oops/typeArrayKlass.hpp:68)
13: libjvm.so!oopFactory::new_typeArray(BasicType type, int length, JavaThread * __the_thread__) (/jdk/src/hotspot/share/memory/oopFactory.cpp:93)
14: libjvm.so!InterpreterRuntime::newarray(JavaThread * current, BasicType type, jint size) (/jdk/src/hotspot/share/interpreter/interpreterRuntime.cpp:249)
15: [Unknown/Just-In-Time compiled code] (Unknown Source:0)`
```



TLAB 分配失败：

```c++
HeapWord* MemAllocator::mem_allocate(Allocation& allocation) const {
  if (UseTLAB) {
    // Try allocating from an existing TLAB.
    HeapWord* mem = mem_allocate_inside_tlab_fast();
    if (mem != nullptr) {
      return mem;
    }
  }

  return mem_allocate_slow(allocation); // <<<<<<<<< TLAB 分配失败
}
```



Heap  分配也失败 ，只能触发 GC：

```c++
HeapWord* GenCollectedHeap::mem_allocate_work(size_t size,
                                              bool is_tlab) {

  HeapWord* result = nullptr;

  // Loop until the allocation is satisfied, or unsatisfied after GC.
  for (uint try_count = 1, gclocker_stalled_count = 0; /* return or throw */; try_count += 1) {

    // First allocation attempt is lock-free.
    Generation *young = _young_gen;
    if (young->should_allocate(size, is_tlab)) {
      result = young->par_allocate(size, is_tlab);
      if (result != nullptr) {
        assert(is_in_reserved(result), "result not in heap");
        return result;
      }
    }
    uint gc_count_before;  // Read inside the Heap_lock locked region.
    {
      MutexLocker ml(Heap_lock);
      log_trace(gc, alloc)("GenCollectedHeap::mem_allocate_work: attempting locked slow path allocation");
      // Note that only large objects get a shot at being
      // allocated in later generations.
      bool first_only = !should_try_older_generation_allocation(size);

      result = attempt_allocation(size, is_tlab, first_only);
      if (result != nullptr) {
        assert(is_in_reserved(result), "result not in heap");
        return result;
      }

      if (GCLocker::is_active_and_needs_gc()) {
        if (is_tlab) {
          return nullptr;  // Caller will retry allocating individual object.
        }
        if (!is_maximal_no_gc()) {
          // Try and expand heap to satisfy request.
          result = expand_heap_and_allocate(size, is_tlab);
          // Result could be null if we are out of space.
          if (result != nullptr) {
            return result;
          }
        }

        if (gclocker_stalled_count > GCLockerRetryAllocationCount) {
          return nullptr; // We didn't get to do a GC and we didn't get any memory.
        }

        // If this thread is not in a jni critical section, we stall
        // the requestor until the critical section has cleared and
        // GC allowed. When the critical section clears, a GC is
        // initiated by the last thread exiting the critical section; so
        // we retry the allocation sequence from the beginning of the loop,
        // rather than causing more, now probably unnecessary, GC attempts.
        JavaThread* jthr = JavaThread::current();
        if (!jthr->in_critical()) {
          MutexUnlocker mul(Heap_lock);
          // Wait for JNI critical section to be exited
          GCLocker::stall_until_clear();
          gclocker_stalled_count += 1;
          continue;
        } else {
          if (CheckJNICalls) {
            fatal("Possible deadlock due to allocating while"
                  " in jni critical section");
          }
          return nullptr;
        }
      }

      // Read the gc count while the heap lock is held.
      gc_count_before = total_collections();
    } // <<<<<<<<< Heap  分配也失败

    VM_GenCollectForAllocation op(size, is_tlab, gc_count_before); 
    VMThread::execute(&op); // <<<<<<<<< 只能触发 GC
      
```



详见本书的 [VMThread - VM Operations - VM Operation Request](/exec-engine/threads/vm-threads-cooperative/vm-operation.md#vm-operation-request) 一节。



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



`prologue:序幕` 就是对 heap 上锁：

```c++
bool VM_GC_Sync_Operation::doit_prologue() {
  Heap_lock->lock();
  return true;
}
```







