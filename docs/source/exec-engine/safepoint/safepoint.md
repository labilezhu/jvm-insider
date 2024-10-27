---

---

# Safepoint

```{toctree}
:hidden:
:includehidden:

threads-handshake.md
```



Safepoint 作为 Java 最让 end-user 讨厌，但又最让 JVM 实现者爱恨交织，重度依赖的机制。成为每个要研究 Java/JVM 的人都必须研究的机制。



![image-20241007152649877](./safepoint.assets/save-point-domain-relationship.png)

*图: Safepoint 是 JVM 众多模块的依赖和协调机制 ([来自: HotSpot JVM Deep Dive - Safepoint](https://www.youtube.com/watch?v=JkbWPPNc4SI&ab_channel=Java))*



## Safepoint 术语



先看看 Safepoint 相关知识的术语：

`Safepoint` /  `Safepointing` / `Stopping-the-world`





> [来自: HotSpot JVM Deep Dive - Safepoint](https://www.youtube.com/watch?v=JkbWPPNc4SI&ab_channel=Java)
>
> - `Thread-local GC root` := An [oop](/memory/oop/oop.md) , i.e. a pointer into the Java heap, local to a `JavaThread`. The denoted Java object is a root of a reachability tree.  
>
> - `Mutable thread state` := A JavaThread state in which the thread can mutate the Java heap or its thread-local GC roots. Aka an unsafe state. 
>
> - `A Safepoint (noun)` is a global JVM state 
>   - Intuition: At this point (state), the Java world is stopped. It is therefore safe, as in exclusive access, to inspect and process by the JVM. 
>   - Technical: No JavaThread is executing inside or can transition into a thread state classified as mutable 
>   - Technical: Thread-local GC roots for all JavaThreads are accessible (published) to the JVM 
>
> 
>
> - `Safepointing (verb)` or Stopping-the-world is a JVM process or mechanism to reach a Safepoint 
>   - Intuition, older notion: "The process of halting or stopping all executing Java threads" 
>   - Technical: The JVM cooperates with Java Threads using a technique called Cooperative Suspension 
>
> 
>
> - `Cooperative Suspension` is a poll-based technique 
>   - JavaThreads check or poll thread-local state at designated locations 
>   - On suspension, the JVM blocks JavaThreads from transitioning into thread states classified as mutable 
>   - On suspension, the JVM triggers JavaThreads to transition from a mutable into an immutable thread state. As a consequence, thread-local GC roots are published. 
>
>   - For example: 
>     - mov r10, qword ptr [r15+130h] // get thread-local poll page address 
>     - test dword ptr [r10], eax // try to read the poll page
>
> - Traditionally, bringing the system to a Safepoint has been a necessary evil for runtimes that provide some form of automatic memory management** 
>
>   - A pervasive JVM/Runtime mechanism. Consequently, a lot of machinery in the JVM.
>   - But JVM developments, especially in the GC area, move ever closer to obviating the need for the global JVM safepoint state.
>
>



- `Thread-local GC root` := `JavaThread` 本地的一个指向 heap 的  [oop](/memory/oop/oop.md) 。作为 GC 对象可达性分析树的树根
- `Mutable thread state` := 指一类型的 JavaThread 的状态，在该状态下，线程可以改变 Java help 或其 `Thread-local GC root`。又称 `unsafe state`。
- `Safepoint (名词)` 是指一种 JVM 全局状态
  - 直觉上：此时（状态），Java 世界已停止。因此，JVM 检查和处理是安全的，就像独占访问一样。
  - 技术上：没有 JavaThread 在内部执行或可以转换为归类为 `Mutable thread state`  的线程
  - 技术上：所有 JavaThread 的`Thread-local GC root`都可以访问（发布）到 JVM

- `Safepointing（动词）` 或 Stopping-the-world 是 JVM 达到安全点的过程或机制

  - 直觉上，较旧的概念：暂停或停止所有正在执行的 Java 线程的过程

  - 技术：JVM 使用一种称为`Cooperative Suspension 协作挂起`的技术与 Java 线程协作

- 传统上，将系统置于`Safepoint`对于提供某种形式的自动内存管理的运行时来说是一种必要之恶

  - 但是 JVM 的发展，特别是在 GC 领域，已经越来越接近于消除对全局 JVM 安全点状态的需求。



## Safepoint 流程概述



以上文字内容不太直观，来个图：

![alt text](./safepoint.assets/stw-process.png)

*图: Stop The World 的步骤。Source: [Async-profiler - manual by use cases](https://krzysztofslusarski.github.io/2022/12/12/async-manual.html#tts)*





1. Global safepoint request 

   1.1 有一个线程向一个叫  `VM Thread` 提出了进入 safepoint 的请求，请求中带上 `safepoint operation` 参数，参数其实是  STOP THE WORLD(STW) 后要执行的 Callback 操作 。可能是触发 GC。也可能是其它原因。

   1.2 `VM Thread` 线程在收到 safepoint request 后，修改一个 JVM 全局的 `safepoint flag `为 true（这个 flag 可以是操作系统的内存页权限标识） 。

   1.3 然后这个  `VM Thread`   就开始等待其它应用线程（App thread） 到达（进入） safepoint 。

   1.4 其它应用线程（App thread）其实会高频检查这个 safepoint flag ，当发现为 true 时，就到达（进入） safepoint 状态。

   [源码 SafepointSynchronize::begin() ](https://github.com/openjdk/jdk/blob/dfacda488bfbe2e11e8d607a6d08527710286982/src/hotspot/share/runtime/safepoint.cpp#L339)

   

2. Global safepoint

   当 `VM Thread`   发现所有 App thread 都到达 safepoint （真实的 STW 的开始） 。就开始执行 `safepoint operation` 。`GC 操作` 是 `safepoint operation` 其中一种可能类型。

   [源码 RuntimeService::record_safepoint_synchronized()](https://github.com/openjdk/jdk/blob/dfacda488bfbe2e11e8d607a6d08527710286982/src/hotspot/share/runtime/safepoint.cpp#L1108)

   

3. End of safepoint operation 

   `safepoint operation`  执行完毕， `VM Thread`  结束 STW 。

   [源码 SafepointSynchronize::end()](https://github.com/openjdk/jdk/blob/dfacda488bfbe2e11e8d607a6d08527710286982/src/hotspot/share/runtime/safepoint.cpp#L487-L488)



##  JavaThread - State

详见本书的 [JavaThread Polling 与 Reach Safepoint - JavaThread - State](/exec-engine/safepoint/threads-handshake.md#javathread-state) 一节。



## GC oop trace

[src/hotspot/share/runtime/javaThread.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/javaThread.hpp#L244)

```c++
class JavaThread: public Thread {
...
  // Active_handles points to a block of handles
  JNIHandleBlock* _active_handles;
...
  JavaFrameAnchor _anchor;                       // Encapsulation of current java frame and it state
```



[src/hotspot/share/runtime/javaFrameAnchor.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/javaFrameAnchor.hpp#L40)

```c++
class JavaFrameAnchor {
...
 private:
  //
  // Whenever _last_Java_sp != nullptr other anchor fields MUST be valid!
  // The stack may not be walkable [check with walkable() ] but the values must be valid.
  // The profiler apparently depends on this.
  //
  intptr_t* volatile _last_Java_sp;

  // Whenever we call from Java to native we can not be assured that the return
  // address that composes the last_Java_frame will be in an accessible location
  // so calls from Java to native store that pc (or one good enough to locate
  // the oopmap) in the frame anchor. Since the frames that call from Java to
  // native are never deoptimized we never need to patch the pc and so this
  // is acceptable.
  volatile  address _last_Java_pc;

  // tells whether the last Java frame is set
  // It is important that when last_Java_sp != nullptr that the rest of the frame
  // anchor (including platform specific) all be valid.

  bool has_last_Java_frame() const                   { return _last_Java_sp != nullptr; }
```





> [来自: HotSpot JVM Deep Dive - Safepoint](https://www.youtube.com/watch?v=JkbWPPNc4SI&ab_channel=Java)
>
> Global jvm state the second clause was that thread local gc routes for all java threads are accessible or published to the jvm. All current garbage collectors are tracing collectors which means they follow or trace the reachability trees starting out from what is called a root set. That is a set of immediately available oops. 
>
> Proper subset of the route set is the set of routes that is local to and reachable from java threads.
>
> 
>
> Let's take a look at what some of these thread local gc routes are.
>
> 
>
> ###  oop Handles
>
> - Local jni handles
>
>   A `JavaThread` has a field called `JNIHandleBlock* _active_handles`. A `local jni handle` provides indirect access to an `oop` for jni code running in `state native` . But allocating/deallocating and even dereferencing a jni handle involve first performing a `vm state transition` which will perform a safe point check.  `Local jni handles` are auto managed so when the code returns from a jni method that is it transitions from `state native` doing a safe point check into `state java` the `local jni handles` allocated by that method are deallocated. 
>
> - HandleArea *(missed in OpenJDK21)*
>
>   The `JavaThread` also has a field called `handle area` and handle area and its companion the handle provides pretty much the same indirection functionality as a `local jni handle` but these are targeted for code running in the `vm state`.  The important difference is that these handles are NOT auto managed but instead must be manually managed by the openjdk programmer. `Handle marks` are used to describe a `handle scope`. And the `handle mark` destructor will deallocate the allocated handles for that particular scope and the scopes can also be nested.
>
> ### Last Java Frame
>
> The thread also has an embedded struct called the `JavaFrameAnchor _anchor` field. It consists of three pointers:
>
> - `_last_Java_sp` for last java stack pointer 
>
> - `_last_Java_pc` for last java program counter
>
> - `_last_Java_fp`*(missed in OpenJDK21, because of virtual thread ?)* for last java frame pointer. the last java frame is the entry point for external stack walking. It is set if a thread has at least one java activation record or frame on its stack and it's currently not in `state java`. So the `_last_Java_fp` is set in `state java` before the thread transitions out. And conversely it is cleared upon thread reentry. 
>
> The anchor struct here requires only that the `last java stack pointer` is set as the other fields are either not relevant for that context or they can be derived by the stack walking code. 
>
> Java frames on the stack may contain `ordinary narrow oops` or `derived oops`. So if you compared to the handles we discussed previously these are naked oops that is they do not have a handling direction they are direct pointers. 
>
> - An `ordinary oop` is a regular oop, 
> - a `narrow oop` is a compressed version of an oop it's a 32-bit size oop. 
> - And the `derived oop` is a pointer into an object not pointing directly to its header. 
>
> So for example we can think of an a pointer that points out an element in an array and a `derived oop` is always associated with a base for a specific code position in java for a specific code position like a` program counter` which stack slots and registers contain oops relative to that `pc` is described by a piece of metadata generated by the compilers something called an `oop map`. 
>
> For a specific code position (pc), which stack slots and registers contain oops is described by a piece of metadata generated by the compilers, called an `OopMap`. To pinpoint an oop in a frame, the `OopMap` describes a location using a relative address, either from the `frame stackpointer (sp)` or as an index into a `RegisterMap`. Not all code positions have `OopMaps`; mainly call sites and safepoint poll page instructions. For stackwalks, the return address of each frame is associated with an `OopMap`.
>
> ### JavaThread CPU Context
>
> A thread executing Java code also has a CPU context. Per the calling convention and performance reasons, oops are ideally placed in registers. Hotspot widely employs something called `Stubs` or `StubRoutines`, which are special platform-specific assembly helper routines. An important feature of most `Stubs` is to save the CPU context when a thread leaves, or suspends its Java execution, and restoring it when the thread re-enters, resuming execution. A `Register Map` is used to resolve a location described by an `OopMap` to be in a register. 



## Safepoint 协作流程详述

Safepoint 协作流程可以划分为以下几步：

1. VM Thread 监听 Safepoint Request
2.  应用线程 Polling Safepoint
3.  一个应用线程 Request Safepoint
4.  接收 Safepoint Request
5.  Arm Safepoint - 标记所有线程
6.  应用线程陷入 Safepoint
7.  等待所有应用线程到达 Safepoint
8.  执行 Stop The World 操作
9.  Disarming Safepoint
10. 应用线程离开 Safepoint
11. 发起 Request Safepoint 的应用线程恢复运行


:::{figure-md}

<img src="/exec-engine/threads/vm-threads-cooperative/vm-operation.drawio.svg" alt="图:VM Operations">

*图:VM Operations*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fvm-operation.drawio.svg)*



### 实验环境

以下结合示例代码 [SafepointGDB.java](https://github.com/labilezhu/pub-diy/blob/f9e68a10cc79a4aa24c33d2724967a527c90eb25/jvm-insider-book/memory/java-obj-layout/src/com/mygraphql/jvm/insider/safepoint/SafepointGDB.java#L14) ，以及本书实验环境一节 [用 VSCode gdb 去 debug JVM](/appendix-lab-env/debug-jdk/debug-jdk-tools.md#vscode-gdb-attach-jvm-process) 的环境，来理论结合实验 fact check 分析一下内存分配失败后诱发 GC 的 Safepoint 流程。

```bash
bash -c 'echo $$ > /tmp/jvm-insider.pid && exec setarch $(uname -m) --addr-no-randomize /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java -XX:+AlwaysPreTouch  -Xms100m -Xmx100m -XX:MaxTenuringThreshold=5 -server -XX:+UseSerialGC  -XX:-UseCompressedOops -XX:+UnlockDiagnosticVMOptions "-Xlog:gc*=debug::tid" -Xlog:safepoint=debug::tid -cp /home/labile/pub-diy/jvm-insider-book/memory/java-obj-layout/out/production/java-obj-layout com.mygraphql.jvm.insider.safepoint.SafepointGDB'
```



### 应用线程 Polling Safepoint

见 [Threads Handshake - Polling](threads-handshake.md#polling) 一节。



### 一个应用线程 Request Safepoint

详见本书的 [VMThread - VM Operations - VM Operation Request](/exec-engine/threads/vm-threads-cooperative/vm-operation.md#vm-operation-request) 一节。



### VM Thread 监听 Safepoint Request

见本书的 [VM Operations](/exec-engine/threads/vm-threads-cooperative/vm-operation.md) 一节。



### 接收 Safepoint Request

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



(arming-safepoint)=
### Arm Safepoint - 标记所有线程

`VM Thread` 线程在收到 safepoint request 后，修改一个 JVM 全局的 `safepoint flag `为 true（这个 flag 可以是操作系统的内存页权限标识） 。



Arm Safepoint 术语中这个 arm 可以直译成 “武装/装备” ，但我翻译成`设置标志` 。



[src/hotspot/share/runtime/safepoint.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/safepoint.cpp#L352)

```c++
// Roll all threads forward to a safepoint and suspend them all
void SafepointSynchronize::begin() {
...
  int nof_threads = Threads::number_of_threads();
  _nof_threads_hit_polling_page = 0;
...
  // Arms the safepoint, _current_jni_active_count and _waiting_to_block must be set before.
  arm_safepoint();
  // Will spin until all threads are safe.
  int iterations = synchronize_threads(safepoint_limit_time, nof_threads, &initial_running);
  ...
}

void SafepointSynchronize::arm_safepoint() {
  // Begin the process of bringing the system to a safepoint.
  // Java threads can be in several different states and are
  // stopped by different mechanisms:
  //
  //  1. Running interpreted
  //     When executing branching/returning byte codes interpreter
  //     checks if the poll is armed, if so blocks in SS::block().
  //  2. Running in native code
  //     When returning from the native code, a Java thread must check
  //     the safepoint _state to see if we must block.  If the
  //     VM thread sees a Java thread in native, it does
  //     not wait for this thread to block.  The order of the memory
  //     writes and reads of both the safepoint state and the Java
  //     threads state is critical.  In order to guarantee that the
  //     memory writes are serialized with respect to each other,
  //     the VM thread issues a memory barrier instruction.
  //  3. Running compiled Code
  //     Compiled code reads the local polling page that
  //     is set to fault if we are trying to get to a safepoint.
  //  4. Blocked
  //     A thread which is blocked will not be allowed to return from the
  //     block condition until the safepoint operation is complete.
  //  5. In VM or Transitioning between states
  //     If a Java thread is currently running in the VM or transitioning
  //     between states, the safepointing code will poll the thread state
  //     until the thread blocks itself when it attempts transitions to a
  //     new state or locking a safepoint checked monitor.

  // We must never miss a thread with correct safepoint id, so we must make sure we arm
  // the wait barrier for the next safepoint id/counter.
  // Arming must be done after resetting _current_jni_active_count, _waiting_to_block.
...
  for (JavaThreadIteratorWithHandle jtiwh; JavaThread *cur = jtiwh.next(); ) {
    // Make sure the threads start polling, it is time to yield.
    SafepointMechanism::arm_local_poll(cur);
  }    
```

可见，`vm thread` 逐一 `arm` 所有的应用线程 。



自从 OpenJDK10 的 [JEP 312: Thread-Local Handshakes - 2017年](https://openjdk.org/jeps/312) 后，就有了非 JVM Global 的 Safepoint - Thread Safepoint 。而 JVM Global 的 Safepoint 好像也修改为基于 `Thread-Local Handshakes` 去实现，即对每一条 JavaThread 执行 `Thread-Local Handshakes`。



[src/hotspot/share/runtime/safepointMechanism.inline.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/safepointMechanism.inline.hpp#L94)

```c++
void SafepointMechanism::arm_local_poll(JavaThread* thread) {
  thread->poll_data()->set_polling_word(_poll_word_armed_value);
  thread->poll_data()->set_polling_page(_poll_page_armed_value);
}

inline void SafepointMechanism::ThreadData::set_polling_word(uintptr_t poll_value) {
  Atomic::store(&_polling_word, poll_value);
}

inline void SafepointMechanism::ThreadData::set_polling_page(uintptr_t poll_value) {
  Atomic::store(&_polling_page, poll_value);
}
```



可以用下图说明 polling_page 的切换：

![safepoint-switch-poll-page.png](./safepoint.assets/safepoint-switch-poll-page.png)

*图: polling_page 的切换. Source: [The Inner Workings of Safepoints 2023 - mostlynerdless.de](https://mostlynerdless.de/blog/2023/07/31/the-inner-workings-of-safepoints/)*





### 等待所有应用线程到达 Safepoint

然后这个  `VM Thread`   就开始等待其它应用线程（App thread） 到达（进入） safepoint 。

[src/hotspot/share/runtime/safepoint.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/safepoint.cpp#L218)

```c++
int SafepointSynchronize::synchronize_threads(jlong safepoint_limit_time, int nof_threads, int* initial_running)
{
  // Iterate through all threads until it has been determined how to stop them all at a safepoint.
  int still_running = nof_threads;
  ThreadSafepointState *tss_head = nullptr;
  ThreadSafepointState **p_prev = &tss_head;
  for (; JavaThread *cur = jtiwh.next(); ) {
    ThreadSafepointState *cur_tss = cur->safepoint_state();
    assert(cur_tss->get_next() == nullptr, "Must be null");
    if (thread_not_running(cur_tss)) {
      --still_running;
    } else {
      *p_prev = cur_tss;
      p_prev = cur_tss->next_ptr();
    }
  }
  ...
```

Stack example:
```
libc.so.6!__GI___clock_nanosleep(clockid_t clock_id, int flags, const struct timespec * req, struct timespec * rem) (clock_nanosleep.c:78)
libc.so.6!__GI___nanosleep(const struct timespec * req, struct timespec * rem) (nanosleep.c:25)
libjvm.so!os::naked_short_nanosleep(jlong ns) (/jdk/src/hotspot/os/posix/os_posix.cpp:892)
libjvm.so!back_off(int64_t start_time) (/jdk/src/hotspot/share/runtime/safepoint.cpp:212)
libjvm.so!SafepointSynchronize::synchronize_threads(jlong safepoint_limit_time, int nof_threads, int * initial_running) (/jdk/src/hotspot/share/runtime/safepoint.cpp:284)
libjvm.so!SafepointSynchronize::begin() (/jdk/src/hotspot/share/runtime/safepoint.cpp:393)
libjvm.so!VMThread::inner_execute(VMThread * const this, VM_Operation * op) (/jdk/src/hotspot/share/runtime/vmThread.cpp:428)
libjvm.so!VMThread::loop(VMThread * const this) (/jdk/src/hotspot/share/runtime/vmThread.cpp:502)
libjvm.so!VMThread::run(VMThread * const this) (/jdk/src/hotspot/share/runtime/vmThread.cpp:175)
libjvm.so!Thread::call_run(Thread * const this) (/jdk/src/hotspot/share/runtime/thread.cpp:217)
libjvm.so!thread_native_entry(Thread * thread) (/jdk/src/hotspot/os/linux/os_linux.cpp:778)
libc.so.6!start_thread(void * arg) (pthread_create.c:442)
libc.so.6!clone3() (clone3.S:81)
```



### 应用线程陷入 Safepoint

Java 线程会高频检查 safepoint flag(safepoint check/polling) ，当发现为 true（arm) 时，就到达（进入） safepoint 状态。



见 [Threads Handshake - Reach and handle](threads-handshake.md#reach) 一节。





### 执行 Stop The World 操作

当 `VM Thread`   发现所有 App thread 都到达 safepoint （真实的 STW 的开始） 。就开始执行 `safepoint operation` 。`GC 操作` 是 `safepoint operation` 其中一种可能类型。


[src/hotspot/share/runtime/vmThread.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/vmThread.cpp#L271)
```c++
void VMThread::evaluate_operation(VM_Operation* op) {
  ResourceMark rm;

  {
    PerfTraceTime vm_op_timer(perf_accumulated_vm_operation_time());
    HOTSPOT_VMOPS_BEGIN(
                     (char *) op->name(), strlen(op->name()),
                     op->evaluate_at_safepoint() ? 0 : 1);

    EventExecuteVMOperation event;
    op->evaluate();
    if (event.should_commit()) {
      post_vm_operation_event(&event, op);
    }

    HOTSPOT_VMOPS_END(
                     (char *) op->name(), strlen(op->name()),
                     op->evaluate_at_safepoint() ? 0 : 1);
  }

}
```

call stack e.g:
```
libjvm.so!VMThread::evaluate_operation(VMThread * const this, VM_Operation * op) (/jdk/src/hotspot/share/runtime/vmThread.cpp:272)
libjvm.so!VMThread::inner_execute(VMThread * const this, VM_Operation * op) (/jdk/src/hotspot/share/runtime/vmThread.cpp:435)
libjvm.so!VMThread::loop(VMThread * const this) (/jdk/src/hotspot/share/runtime/vmThread.cpp:502)
libjvm.so!VMThread::run(VMThread * const this) (/jdk/src/hotspot/share/runtime/vmThread.cpp:175)
libjvm.so!Thread::call_run(Thread * const this) (/jdk/src/hotspot/share/runtime/thread.cpp:217)
libjvm.so!thread_native_entry(Thread * thread) (/jdk/src/hotspot/os/linux/os_linux.cpp:778)
libc.so.6!start_thread(void * arg) (pthread_create.c:442)
libc.so.6!clone3() (clone3.S:81)
```

#### Stop The World - GC
[src/hotspot/share/gc/shared/gcVMOperations.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/gc/shared/gcVMOperations.hpp#L87)
```c++
// The following class hierarchy represents
// a set of operations (VM_Operation) related to GC.
//
//  VM_Operation
//    VM_GC_Sync_Operation
//      VM_GC_Operation
//        VM_GC_HeapInspection
//        VM_PopulateDynamicDumpSharedSpace
//        VM_GenCollectFull
//        VM_ParallelGCSystemGC
//        VM_CollectForAllocation
//          VM_GenCollectForAllocation
//          VM_ParallelGCFailedAllocation
//      VM_Verify
//      VM_PopulateDumpSharedSpace
//
//  VM_GC_Sync_Operation
//   - implements only synchronization with other VM operations of the
//     same kind using the Heap_lock, not actually doing a GC.
//
//  VM_GC_Operation
//   - implements methods common to all operations that perform garbage collections,
//     checking that the VM is in a state to do GC and preventing multiple GC
//     requests.
//
//  VM_GC_HeapInspection
//   - prints class histogram on SIGBREAK if PrintClassHistogram
//     is specified; and also the attach "inspectheap" operation
//
//  VM_CollectForAllocation
//  VM_GenCollectForAllocation
//  VM_ParallelGCFailedAllocation
//   - this operation is invoked when allocation is failed;
//     operation performs garbage collection and tries to
//     allocate afterwards;
//
//  VM_GenCollectFull
//  VM_ParallelGCSystemGC
//   - these operations perform full collection of heaps of
//     different kind
//
//  VM_Verify
//   - verifies the heap
//
//  VM_PopulateDynamicDumpSharedSpace
//   - populates the CDS archive area with the information from the archive file.
//
//  VM_PopulateDumpSharedSpace
//   - creates the CDS archive
//

class VM_GC_Sync_Operation : public VM_Operation {...}

class VM_GC_Operation: public VM_GC_Sync_Operation {
 protected:
  uint           _gc_count_before;         // gc count before acquiring the Heap_lock
  uint           _full_gc_count_before;    // full gc count before acquiring the Heap_lock
  bool           _full;                    // whether a "full" collection
  bool           _prologue_succeeded;      // whether doit_prologue succeeded
  GCCause::Cause _gc_cause;                // the putative cause for this gc op
  bool           _gc_locked;               // will be set if gc was locked
...}


```

从上 class 继承关系可见 `VM_GenCollectForAllocation` 实现了 `VM_Operation` 接口。


[src/hotspot/share/gc/shared/gcVMOperations.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/gc/shared/gcVMOperations.cpp#L198)
```c++
void VM_GenCollectForAllocation::doit() {
  SvcGCMarker sgcm(SvcGCMarker::MINOR);

  GenCollectedHeap* gch = GenCollectedHeap::heap();
  GCCauseSetter gccs(gch, _gc_cause);
  _result = gch->satisfy_failed_allocation(_word_size, _tlab);
  assert(_result == nullptr || gch->is_in_reserved(_result), "result not in heap");

  if (_result == nullptr && GCLocker::is_active_and_needs_gc()) {
    set_gc_locked();
  }
}
```

通过 gdb breakpoint ，可以观察到， `VM_GenCollectForAllocation._gc_cause` 类型为 `GCCause::_allocation_failure`

call stack e.g:
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


### Disarming Safepoint

[src/hotspot/share/runtime/safepointMechanism.inline.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/safepointMechanism.inline.hpp#L101)

```c++
// Disarming one thread 
void SafepointMechanism::disarm_local_poll(JavaThread* thread) {
  thread->poll_data()->set_polling_word(_poll_word_disarmed_value);
  thread->poll_data()->set_polling_page(_poll_page_disarmed_value);
}
```

### 应用线程离开 Safepoint
见 [Threads Handshake - 应用线程离开 Safepoint](/exec-engine/safepoint/threads-handshake.md#exit-safepoint) 一节


## Safepoint 问题排查
Safepoint 是 JVM 性能问题的热点爆发地。我之前写有一些文章去排查相关问题：

- [eBPF 求证坊间传闻：Java GC 日志可导致整个 JVM 服务卡顿？](https://blog.mygraphql.com/zh/notes/java/java-gc-log-stuck/)
- [eBPF 求证坊间传闻：mmap + Java Safepoint 可导致整个 JVM 服务卡顿？](https://blog.mygraphql.com/zh/notes/java/java-reach-safepoint-stalled/)



## 参考

- [HotSpot JVM Deep Dive - Safepoint - Youtube Java Channel](https://www.youtube.com/watch?v=JkbWPPNc4SI&ab_channel=Java)
- [Async-profiler - manual by use cases - krzysztofslusarski.github.io](https://krzysztofslusarski.github.io/2022/12/12/async-manual.html#tts)
- [Safepoints: Meaning, Side Effects and Overheads - psy-lob-saw.blogspot.com](https://psy-lob-saw.blogspot.com/2015/12/safepoints.html)
- [Where is my safepoint? - psy-lob-saw.blogspot.com](https://psy-lob-saw.blogspot.com/2014/03/where-is-my-safepoint.html)
- [The Inner Workings of Safepoints 2023 - mostlynerdless.de](https://mostlynerdless.de/blog/2023/07/31/the-inner-workings-of-safepoints/)
- [Robbin Ehn: Handshaking HotSpot - Youtube Java Channel - 2020](https://www.youtube.com/watch?v=VBCOfAJ409s&ab_channel=Java)
- [Robbin Ehn: HotSpot Handshaking - Jfokus 2020](https://www.jfokus.se/jfokus20-preso/Handshaking-in-HotSpot.pdf)
- [JVM Anatomy Quark #22: Safepoint Polls](https://shipilev.net/jvm/anatomy-quarks/22-safepoint-polls/)





