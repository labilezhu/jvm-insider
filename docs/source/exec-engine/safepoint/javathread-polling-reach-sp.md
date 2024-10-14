# JavaThread Polling 与 Reach Safepoint




(javathread_state)=
## JavaThread - State



Safepoint 机制的实现依赖于 [JavaThread](/exec-engine/threads/java-thread/java-thread.md) 。



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



![HotSpot JVM Deep Dive - Safepoint 9-43 screenshot](./jit-polling-reach-sp.assets/java-thread-state-machine.png)

*图: JavaThread 状态机。Source: [Java Thread state machine](https://youtu.be/JkbWPPNc4SI?si=c5YYAKHYBPROZAZ_&t=576)*



> [来自: HotSpot JVM Deep Dive - Safepoint](https://www.youtube.com/watch?v=JkbWPPNc4SI&ab_channel=Java)
>
> This is the state machine for the java thread and we can further classify it into the following categories:
>
> - `mutable thread state` it's a state in which the thread can mute it the java heap or its thread local gc routes
> - `immutable thread states` is a state where the threat can do none of these things
> - `transition states` which act like bridges between the mutable and the immutable states a transition state has a **safe point check** or a **poll instruction** together with appropriate fencing



这是 Java 线程的状态机，我们可以进一步将其分为以下类别：

- `mutable thread state 可变线程状态` 线程可以修改 Java 堆或其线程本地 GC 数据
- `immutable thread states 不可变线程状态` 不能修改 oop 的状态
- `transition states 过渡状态` 充当`mutable thread state`和`immutable thread states` 之间的桥梁，过渡状态具有 **safe point check** 或 **轮询指令** 以及适当的隔离



> [来自: HotSpot JVM Deep Dive - Safepoint](https://youtu.be/JkbWPPNc4SI?si=YIq5HIHvSQFcC4U9&t=597)
>
> Let's for example take a look at this situation:
> we have a new thread comes into being it starts running in the `VM state`.
> Let's say this thread now wants to execute some java code. In order to do that it will need to traverse a transition into the `java state` and as that the transition as we said contains a `save point check`. Some notable transitions here is that the `java code(java state)` can transition to `VM state` and to `Native state` **without** performing save point checks instead the save point check is performed when the thread returns to `state java`.
>
> 
>
> Another important takeaway here is that code executing in `state native` is considered safe this means that during a safe point java threads can actually continue running native code and this also means that counter to the intuitive notion that a safe point involves blocking or halting all java threads it only means that they do not executein a sense a sensitive `mutable state`



关于 `transition states` 的作用 ，让我们看一下这种情况：
我们有一个新的线程出现，一开始在 `VM state` 中运行。
假设这个线程现在要执行一些 Java 代码。为了做到这一点，它将需要间接跳转到  ` java state` ，这个跳转包含 safepoint check。 值得注意的是，Java 代码（`Java state`） 可以直接跳转到 `VM state` 和  `native state` ，**无需** 执行 safepoint check，但在线程返回到 `Java state` 时执行，需要 safepoint check 。



另一个要注意的是，在`native state`下执行的代码被认为是安全的，这意味着在安全点期间，java 线程实际上可以继续运行 native code ，这也意味着，与安全点会阻塞或停止所有 java 线程的直观想法相反，安全点只意味着不执行敏感的 `mutable state` 操作。



## 基础知识

### JIT 生成代码的寄存器分类

#### 固定寄存器

- $r12 - 存放 Java Heap base
- $r15 - 存放 thread local 的 JavaThread 指针

### 寄存器在 Frame 间保存
- $rbp - 由 `callee-saved` 
- 其它通用寄存器 - 由 `caller-saved`


(polling)=

## Polling

Java 线程会高频检查 safepoint flag(safepoint check/polling) ，当发现为 true（arm) 时，就到达（进入） safepoint 状态。



### JVM 初始化

JVM 在启动时，就已经初始化了两个 Memory Page ，用于 safepoint 。一个 bad_page 不可读，如在它上执行 `test` x86指令，线程会因收到信号而挂起并跳转到信号处理器代码 。一个 good_page 可读，可正常执行 `test` x86指令：



Stack:

```
libjvm.so!SafepointMechanism::default_initialize() (/jdk/src/hotspot/share/runtime/safepointMechanism.cpp:68)
libjvm.so!SafepointMechanism::pd_initialize() (/jdk/src/hotspot/share/runtime/safepointMechanism.hpp:56)
libjvm.so!SafepointMechanism::initialize() (/jdk/src/hotspot/share/runtime/safepointMechanism.cpp:171)
libjvm.so!Threads::create_vm(JavaVMInitArgs * args, bool * canTryAgain) (/jdk/src/hotspot/share/runtime/threads.cpp:492)
libjvm.so!JNI_CreateJavaVM_inner(JavaVM ** vm, void ** penv, void * args) (/jdk/src/hotspot/share/prims/jni.cpp:3577)
libjvm.so!JNI_CreateJavaVM(JavaVM ** vm, void ** penv, void * args) (/jdk/src/hotspot/share/prims/jni.cpp:3668)
libjli.so!InitializeJVM(JavaVM ** pvm, JNIEnv ** penv, InvocationFunctions * ifn) (/jdk/src/java.base/share/native/libjli/java.c:1506)
libjli.so!JavaMain(void * _args) (/jdk/src/java.base/share/native/libjli/java.c:415)
libjli.so!ThreadJavaMain(void * args) (/jdk/src/java.base/unix/native/libjli/java_md.c:650)
libc.so.6!start_thread(void * arg) (pthread_create.c:442)
libc.so.6!clone3() (clone3.S:81)
```





[src/hotspot/share/runtime/safepointMechanism.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/safepointMechanism.cpp#L74)

```c++
uintptr_t SafepointMechanism::_poll_word_armed_value;
uintptr_t SafepointMechanism::_poll_page_armed_value;

//   const static intptr_t _poll_bit = 1;

void SafepointMechanism::default_initialize() {
  // Poll bit values
  _poll_word_armed_value    = poll_bit();
  _poll_word_disarmed_value = ~_poll_word_armed_value;

...
    // Polling page
    const size_t page_size = os::vm_page_size();
    const size_t allocation_size = 2 * page_size;
    char* polling_page = os::reserve_memory(allocation_size);
    os::commit_memory_or_exit(polling_page, allocation_size, false, "Unable to commit Safepoint polling page");
    MemTracker::record_virtual_memory_type((address)polling_page, mtSafepoint);

    char* bad_page  = polling_page;
    char* good_page = polling_page + page_size;

    os::protect_memory(bad_page,  page_size, os::MEM_PROT_NONE);
    os::protect_memory(good_page, page_size, os::MEM_PROT_READ);

    log_info(os)("SafePoint Polling address, bad (protected) page:" INTPTR_FORMAT ", good (unprotected) page:" INTPTR_FORMAT, p2i(bad_page), p2i(good_page));

    // Poll address values
    _poll_page_armed_value    = reinterpret_cast<uintptr_t>(bad_page); // <<<<<<<
    _poll_page_disarmed_value = reinterpret_cast<uintptr_t>(good_page); // <<<<<<<
    _polling_page = (address)bad_page; // <<<<<<<
}
```




(do_polling)=

### 真正 Polling



先看看相关的数据结构：

[src/hotspot/share/runtime/javaThread.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/javaThread.hpp#L246)

```c++
class JavaThread: public Thread {
    ...
 private:
  SafepointMechanism::ThreadData _poll_data;
  ThreadSafepointState*          _safepoint_state;              // Holds information about a thread during a safepoint
  address                        _saved_exception_pc;           // Saved pc of instruction where last implicit exception happened
```



[src/hotspot/share/runtime/safepointMechanism.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/safepointMechanism.hpp#L68)

```c++
class SafepointMechanism {
...
  static address _polling_page;
...    
  struct ThreadData {
    volatile uintptr_t _polling_word;
    volatile uintptr_t _polling_page;
    ...
  };
```

从上面代码，可以猜到 `SafepointMechanism._polling_page` 是个 Global var。对应着 Global Safepoint。 而  `JavaThread._poll_data._polling_page` 是 Thread Local 的，对应着 Thread-Local Handshakes 。

自从 OpenJDK10 的 [JEP 312: Thread-Local Handshakes - 2017年](https://openjdk.org/jeps/312) 后，就有了非 JVM Global 的 Safepoint - Thread Safepoint 。而 JVM Global 的 Safepoint 好像也修改为基于 `Thread-Local Handshakes` 去实现，即对每一条 JavaThread 执行 `Thread-Local Handshakes`。



在 OpenJDK10 时，可以通过 `-XX:-ThreadLocalHandshakes` 去禁用 ThreadLocalHandshakes ，但以下几个过程后就不可以禁用了：

- Deprecated in JDK13
- Obsoleted in JDK14
- Expired in JDK15

原因当然是 OpenJDK 已经强依赖于这个特性了： [Obsolete ThreadLocalHandshakes - bugs.openjdk.org](https://bugs.openjdk.org/browse/JDK-8220049) .



#### JIT 编译后的 Polling

可以用下图说明 polling_page 的切换：

![safepoint-switch-poll-page.png](./javathread-polling-reach-sp.assets/safepoint-switch-poll-page.png)

*图: polling_page 的切换. Source: [The Inner Workings of Safepoints 2023 - mostlynerdless.de](https://mostlynerdless.de/blog/2023/07/31/the-inner-workings-of-safepoints/)*



![image-20241012232124643](./javathread-polling-reach-sp.assets/image-20241012232124643.png)

*图: JavaThread 与 R15 寄存器. Source: [Robbin Ehn: Handshaking HotSpot - Youtube Java Channel - 2020](https://www.youtube.com/watch?v=VBCOfAJ409s&ab_channel=Java)*



上图意为，读取本线程对应的 JavaThread._poll_data(SafepointMechanism::ThreadData).polling_page 指向的地址。其中 R15 寄存器一般会指向本线程对应的  JavaThread。



```c++
// Generated poll in JIT 
// poll-offset: JavaThread._poll_data(SafepointMechanism::ThreadData).polling_page 在 JavaThread 的 offset
// thread_reg: 一般指 R15 寄存器,用于保存本线程对应的 JavaThread
mov poll-offset + thread_reg, reg 
test rax, reg
```

Source: [Robbin Ehn: Handshaking HotSpot - Youtube Java Channel - 2020](https://www.youtube.com/watch?v=VBCOfAJ409s&ab_channel=Java)



上面显示需要两条机器指令，才能完成 polling。如果你看过 [OpenJDK11 之前的资料](https://psy-lob-saw.blogspot.com/2014/03/where-is-my-safepoint.html)，之前应该就一条机器指令就够了：

```
test   DWORD PTR [rip+0xa2b0966],eax  
```



主要原因是  OpenJDK11 默认启用 [JEP 312: Thread-Local Handshakes](https://openjdk.org/jeps/312) 的设计，要求每条 Thread 有自己的 polling_page 指针，所以需要多一条机器命令来多一层寻址。



#### Non-JIT Polling

//TBD



(reach)=
## Reach and handle

在 VMThread arm safepoint (详见本书的 [Safepoint - Arm Safepoint - 标记所有线程](/exec-engine/safepoint/safepoint.md#arming_safepoint)） 后。polling 的应用线程最终会感知到 safepoint 的聚集要求(arming)。



- 对于 绿色 `immutable thread state` 状态的 JavaThread:  

  `vm thread`  通过 `arm` Java 线程的 polling page，这实际上在 arm safepoint 期间阻止了线程从所有绿色 `immutable thread state` 中唤醒/返回后，转换到任何红色 unsafe `mutable thread state` 。见 [src/hotspot/share/utilities/globalDefinitions.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/utilities/globalDefinitions.hpp#L1030)：

  ```c++
  // Each state has an associated xxxx_trans state, which is an intermediate state used when a thread is in
  // a transition from one state to another. These extra states makes it possible for the safepoint code to
  // handle certain thread_states without having to suspend the thread - making the safepoint code faster.
  ```

  

![HotSpot JVM Deep Dive - Safepoint 19-43 screenshot](./jit-polling-reach-sp.assets/disable-to-mutable-thread-state-by-sp-check.png)

*图: 当 JavaThread  被`arm`  polling page 后的状态机变化 。Source: [HotSpot JVM Deep Dive - Safepoint](https://youtu.be/JkbWPPNc4SI?si=c5YYAKHYBPROZAZ_&t=576)*



- 对于 红色 `mutable thread state` 状态的 JavaThread: 

  `vm thread`  通过 `arm` Java 线程的 polling page， 触发 Java 线程从 `mutable thread state` 转换为 `immutable thread state` 状态。并且作为此转换的结果，线程本地 GC 树被同步到 JavaThread 对象。

  对于 `VM state` 的线程，这意味着需要等待线程自行完成转换。`VM state` 中只有少数几个地方显式执行安全点检查。例如，在争夺 `VM mutex 互斥锁`或 `VM monitor` 时。此设计的前提是 Java 线程应尽可能少地处于 `VM state`。但对于在 `state java`  下运行的线程，情况有所不同。

  



下图举一个例子，尝试说明在几种线程状态和操作系统调度环境下，线程到达 Safepoint (GetStackTrace 需要 Stop The World) 的情况。



![SafepointOverheads.png](./jit-polling-reach-sp.assets/SafepointOverheads.png)

*图:  几种状态和系统调度环境下，线程到达 Safepoint 的情况. Source: [Safepoints: Meaning, Side Effects and Overheads - psy-lob-saw.blogspot.com](https://psy-lob-saw.blogspot.com/2015/12/safepoints.html)*



- 绿色箭头：java state thread and running **on CPU**
- 黄色箭头：java state thread and **off CPU** (因 CPU 资源不足等原因)
- 红色箭头：JNI state thread



从 VMThread arm safepoint 到 应用线程 Reach Safepoint 的延迟，叫 `Time To Safe Point(TTSP)` ：

每个线程在进行 safepoint check 时如发现 safepoint arming 都会进入安全点。但到达 safepoint check  前需要执行机器指令的数量不是固定的。上图中，我们可以看到：

- J1 直接命中安全点轮询并被暂停。J2 和 J3 正在争夺可用的 CPU 时间。J3 抢占了一些 CPU 时间，将 J2 推入运行队列，但 J2 并未进入安全点。J3 到达安全点并暂停，从而腾出内核，让 J2 取得足够的进展，进入安全点轮询。

- J4 和 J5 在执行 JNI 代码(`JNI state`)时属于`Immutable thread state`，它们不受 Safepoint 挂起影响。请注意，J5 在 Stop The World 执行到一半时试图离开 JNI，并在恢复执行 Java 代码前被暂停。重要的是，我们观察到不同线程到达安全点的时间各不相同，有些线程暂停的时间比其他线程长，Java 线程花很长时间到达安全点可能会耽误其他线程。



OpenJDK9 前，用 `-XX:+PrintGCApplicationStoppedTime` 可以打印出 TTSP 。OpenJDK9 后，由于采用了 `Unified Logging for GC logging` 的设计，配置修改成：
`-Xlog:safepoint` 。



### Signal Handle



JVM 启动初始化时，安装了JVM 自用的 Signal Handler ：

Stack :

```
libjvm.so!PosixSignals::install_sigaction_signal_handler(sigaction * sigAct, sigaction * oldSigAct, int sig, sa_sigaction_t handler) (/jdk/src/hotspot/os/posix/signals_posix.cpp:900)
libjvm.so!set_signal_handler(int sig) (/jdk/src/hotspot/os/posix/signals_posix.cpp:1271)
libjvm.so!install_signal_handlers() (/jdk/src/hotspot/os/posix/signals_posix.cpp:1313)
libjvm.so!PosixSignals::init() (/jdk/src/hotspot/os/posix/signals_posix.cpp:1855) // <<<<----
libjvm.so!os::init_2() (/jdk/src/hotspot/os/linux/os_linux.cpp:4613)
libjvm.so!Threads::create_vm(JavaVMInitArgs * args, bool * canTryAgain) (/jdk/src/hotspot/share/runtime/threads.cpp:482)
libjvm.so!JNI_CreateJavaVM_inner(JavaVM ** vm, void ** penv, void * args) (/jdk/src/hotspot/share/prims/jni.cpp:3577)
libjvm.so!JNI_CreateJavaVM(JavaVM ** vm, void ** penv, void * args) (/jdk/src/hotspot/share/prims/jni.cpp:3668)
libjli.so!InitializeJVM(JavaVM ** pvm, JNIEnv ** penv, InvocationFunctions * ifn) (/jdk/src/java.base/share/native/libjli/java.c:1506)
libjli.so!JavaMain(void * _args) (/jdk/src/java.base/share/native/libjli/java.c:415)
libjli.so!ThreadJavaMain(void * args) (/jdk/src/java.base/unix/native/libjli/java_md.c:650)
libc.so.6!start_thread(void * arg) (pthread_create.c:442)
libc.so.6!clone3() (clone3.S:81)
```



[src/hotspot/os/posix/signals_posix.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/os/posix/signals_posix.cpp#L1313)

```c++
// install signal handlers for signals that HotSpot needs to
// handle in order to support Java-level exception handling.
void install_signal_handlers() {
...    
  set_signal_handler(SIGSEGV); // <<<<<<<
...
}

void set_signal_handler(int sig) {
...
  struct sigaction sigAct;
  int ret = PosixSignals::install_sigaction_signal_handler(&sigAct, &oldAct,
                                                           sig, javaSignalHandler); // <<<<----
}

// Entry point for the hotspot signal handler.
static void javaSignalHandler(int sig, siginfo_t* info, void* context) {
  // Do not add any code here!
  // Only add code to either JVM_HANDLE_XXX_SIGNAL or PosixSignals::pd_hotspot_signal_handler.
  (void)JVM_HANDLE_XXX_SIGNAL(sig, info, context, true);
}

int JVM_HANDLE_XXX_SIGNAL(int sig, siginfo_t* info,
                          void* ucVoid, int abort_if_unrecognized)
{
  // Call platform dependent signal handler.
  if (!signal_was_handled) {
    JavaThread* const jt = (t != nullptr && t->is_Java_thread()) ? JavaThread::cast(t) : nullptr;
    signal_was_handled = PosixSignals::pd_hotspot_signal_handler(sig, info, uc, jt); // <<<<----
  }
...
}
```



Signal Handler 实现：

[src/hotspot/os_cpu/linux_x86/os_linux_x86.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/os_cpu/linux_x86/os_linux_x86.cpp#L207)

```c++
bool PosixSignals::pd_hotspot_signal_handler(int sig, siginfo_t* info,
                                             ucontext_t* uc, JavaThread* thread) {
...
    if (thread->thread_state() == _thread_in_Java) {
      // Java thread running in Java code => find exception handler if any
      // a fault inside compiled code, the interpreter, or a stub

      if (sig == SIGSEGV && SafepointMechanism::is_poll_address((address)info->si_addr)) {
        stub = SharedRuntime::get_poll_stub(pc); //  <<<<----
      } else if (sig == SIGBUS /* && info->si_code == BUS_OBJERR */) {..}
      ...
      } else if (sig == SIGSEGV &&
                 MacroAssembler::uses_implicit_null_check(info->si_addr)) {
          // Determination of interpreter/vtable stub/compiled code null exception
          stub = SharedRuntime::continuation_for_implicit_exception(thread, pc, SharedRuntime::IMPLICIT_NULL);
      }
    } else if ((thread->thread_state() == _thread_in_vm ||
                thread->thread_state() == _thread_in_native) &&
               (sig == SIGBUS && /* info->si_code == BUS_OBJERR && */
               thread->doing_unsafe_access())) {
        address next_pc = Assembler::locate_next_instruction(pc);
        if (UnsafeCopyMemory::contains_pc(pc)) {
          next_pc = UnsafeCopyMemory::page_error_continue_pc(pc);
        }
        stub = SharedRuntime::handle_unsafe_access(thread, next_pc);
    }
    // jni_fast_Get<Primitive>Field can trap at certain pc's if a GC kicks in
    // and the heap gets shrunk before the field access.
    if ((sig == SIGSEGV) || (sig == SIGBUS)) {
      address addr = JNI_FastGetField::find_slowcase_pc(pc);
      if (addr != (address)-1) {
        stub = addr;
      }
    }
...
  if (stub != nullptr) {
    // save all thread context in case we need to restore it
    if (thread != nullptr) thread->set_saved_exception_pc(pc);

    os::Posix::ucontext_set_pc(uc, stub); // <<<<---- 直接修改 PC 寄存器，goto 跳到上面获取的 SafepointBlob Stub 机器码中
    return true;
  }

}
```





### SafepointBlob Stub 机器码获取 - poll_stub

[src/hotspot/share/runtime/sharedRuntime.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/sharedRuntime.cpp#L554)

```c++
address SharedRuntime::get_poll_stub(address pc) {
  address stub;
  // Look up the code blob
  CodeBlob *cb = CodeCache::find_blob(pc);

  // Should be an nmethod
  guarantee(cb != nullptr && cb->is_compiled(), "safepoint polling: pc must refer to an nmethod");

  // Look up the relocation information
  assert(((CompiledMethod*)cb)->is_at_poll_or_poll_return(pc),
      "safepoint polling: type must be poll at pc " INTPTR_FORMAT, p2i(pc));
...
  bool at_poll_return = ((CompiledMethod*)cb)->is_at_poll_return(pc);
  bool has_wide_vectors = ((CompiledMethod*)cb)->has_wide_vectors();
  if (at_poll_return) {
    assert(SharedRuntime::polling_page_return_handler_blob() != nullptr,
           "polling page return stub not created yet");
    stub = SharedRuntime::polling_page_return_handler_blob()->entry_point();
  } else if (has_wide_vectors) {
    assert(SharedRuntime::polling_page_vectors_safepoint_handler_blob() != nullptr,
           "polling page vectors safepoint stub not created yet");
    stub = SharedRuntime::polling_page_vectors_safepoint_handler_blob()->entry_point();
  } else {
    assert(SharedRuntime::polling_page_safepoint_handler_blob() != nullptr,
           "polling page safepoint stub not created yet");
    stub = SharedRuntime::polling_page_safepoint_handler_blob()->entry_point(); // <<<<<<<
  }
  log_debug(safepoint)("... found polling page %s exception at pc = "
                       INTPTR_FORMAT ", stub =" INTPTR_FORMAT,
                       at_poll_return ? "return" : "loop",
                       (intptr_t)pc, (intptr_t)stub);
  return stub;
}

// JVM 启动初始化时，SafepointBlob Stub 机器码生成
static  _polling_page_safepoint_handler_blob = generate_handler_blob(CAST_FROM_FN_PTR(address, SafepointSynchronize::handle_polling_page_exception), POLL_AT_LOOP); // <<<<<<<<<
static  _polling_page_return_handler_blob    = generate_handler_blob(CAST_FROM_FN_PTR(address, SafepointSynchronize::handle_polling_page_exception), POLL_AT_RETURN);
```



JVM 启动初始化时，SafepointBlob Stub 机器码生成：

[src/hotspot/cpu/x86/sharedRuntime_x86_64.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/cpu/x86/sharedRuntime_x86_64.cpp#L3079)

```c++
//------------------------------generate_handler_blob------
//
// Generate a special Compile2Runtime blob that saves all registers,
// and setup oopmap.
//
SafepointBlob* SharedRuntime::generate_handler_blob(address call_ptr, int poll_type) {
  assert(StubRoutines::forward_exception_entry() != nullptr,
         "must be generated before");

  ResourceMark rm;
  OopMapSet *oop_maps = new OopMapSet();
  OopMap* map;

  // Allocate space for the code.  Setup code generation tools.
  CodeBuffer buffer("handler_blob", 2048, 1024);
  MacroAssembler* masm = new MacroAssembler(&buffer);

  address start   = __ pc();
  address call_pc = nullptr;
  int frame_size_in_words;
  bool cause_return = (poll_type == POLL_AT_RETURN);
  bool save_wide_vectors = (poll_type == POLL_AT_VECTOR_LOOP);

  if (UseRTMLocking) {
    // Abort RTM transaction before calling runtime
    // because critical section will be large and will be
    // aborted anyway. Also nmethod could be deoptimized.
    __ xabort(0);
  }

  // Make room for return address (or push it again)
  if (!cause_return) {
    __ push(rbx);
  }

  // Save registers, fpu state, and flags
  map = RegisterSaver::save_live_registers(masm, 0, &frame_size_in_words, save_wide_vectors);

  // The following is basically a call_VM.  However, we need the precise
  // address of the call in order to generate an oopmap. Hence, we do all the
  // work ourselves.

  __ set_last_Java_frame(noreg, noreg, nullptr, rscratch1);  // JavaFrameAnchor::capture_last_Java_pc() will get the pc from the return address, which we store next:

  // The return address must always be correct so that frame constructor never
  // sees an invalid pc.

  if (!cause_return) {
    // Get the return pc saved by the signal handler and stash it in its appropriate place on the stack.
    // Additionally, rbx is a callee saved register and we can look at it later to determine
    // if someone changed the return address for us!
    __ movptr(rbx, Address(r15_thread, JavaThread::saved_exception_pc_offset()));
    __ movptr(Address(rbp, wordSize), rbx);
  }

  // Do the call
  __ mov(c_rarg0, r15_thread);
  __ call(RuntimeAddress(call_ptr));

  // Set an oopmap for the call site.  This oopmap will map all
  // oop-registers and debug-info registers as callee-saved.  This
  // will allow deoptimization at this safepoint to find all possible
  // debug-info recordings, as well as let GC find all oops.

  oop_maps->add_gc_map( __ pc() - start, map);

  Label noException;

  __ reset_last_Java_frame(false);

  __ cmpptr(Address(r15_thread, Thread::pending_exception_offset()), NULL_WORD);
  __ jcc(Assembler::equal, noException);

  // Exception pending

  RegisterSaver::restore_live_registers(masm, save_wide_vectors);

  __ jump(RuntimeAddress(StubRoutines::forward_exception_entry()));

  // No exception case
  __ bind(noException);

  Label no_adjust;
...
  if (!cause_return) {
    Label no_prefix, not_special;

    // If our stashed return pc was modified by the runtime we avoid touching it
    __ cmpptr(rbx, Address(rbp, wordSize));
    __ jccb(Assembler::notEqual, no_adjust);

    // Skip over the poll instruction.
    // See NativeInstruction::is_safepoint_poll()
    // Possible encodings:
    //      85 00       test   %eax,(%rax)
    //      85 01       test   %eax,(%rcx)
    //      85 02       test   %eax,(%rdx)
    //      85 03       test   %eax,(%rbx)
    //      85 06       test   %eax,(%rsi)
    //      85 07       test   %eax,(%rdi)
    //
    //   41 85 00       test   %eax,(%r8)
    //   41 85 01       test   %eax,(%r9)
    //   41 85 02       test   %eax,(%r10)
    //   41 85 03       test   %eax,(%r11)
    //   41 85 06       test   %eax,(%r14)
    //   41 85 07       test   %eax,(%r15)
    //
    //      85 04 24    test   %eax,(%rsp)
    //   41 85 04 24    test   %eax,(%r12)
    //      85 45 00    test   %eax,0x0(%rbp)
    //   41 85 45 00    test   %eax,0x0(%r13)

    __ cmpb(Address(rbx, 0), NativeTstRegMem::instruction_rex_b_prefix);
    __ jcc(Assembler::notEqual, no_prefix);
    __ addptr(rbx, 1);
    __ bind(no_prefix);
...
    // r12/r13/rsp/rbp base encoding takes 3 bytes with the following register values:
    // r12/rsp 0x04
    // r13/rbp 0x05
    __ movzbq(rcx, Address(rbx, 1));
    __ andptr(rcx, 0x07); // looking for 0x04 .. 0x05
    __ subptr(rcx, 4);    // looking for 0x00 .. 0x01
    __ cmpptr(rcx, 1);
    __ jcc(Assembler::above, not_special);
    __ addptr(rbx, 1);
    __ bind(not_special);
...
    // Adjust return pc forward to step over the safepoint poll instruction
    __ addptr(rbx, 2);
    __ movptr(Address(rbp, wordSize), rbx);
  }

  __ bind(no_adjust);
  // Normal exit, restore registers and exit.
  RegisterSaver::restore_live_registers(masm, save_wide_vectors);
  __ ret(0);

...

  // Make sure all code is generated
  masm->flush();

  // Fill-out other meta info
  return SafepointBlob::create(&buffer, oop_maps, frame_size_in_words);
}
```







## 参考

- [Robbin Ehn: Handshaking HotSpot - Youtube Java Channel - 2020](https://www.youtube.com/watch?v=VBCOfAJ409s&ab_channel=Java)
- [HotSpot JVM Deep Dive - Safepoint - Youtube Java Channel](https://www.youtube.com/watch?v=JkbWPPNc4SI&ab_channel=Java)
- [Async-profiler - manual by use cases - krzysztofslusarski.github.io](https://krzysztofslusarski.github.io/2022/12/12/async-manual.html#tts)
- [Safepoints: Meaning, Side Effects and Overheads - psy-lob-saw.blogspot.com](https://psy-lob-saw.blogspot.com/2015/12/safepoints.html)
- [Where is my safepoint? - psy-lob-saw.blogspot.com](https://psy-lob-saw.blogspot.com/2014/03/where-is-my-safepoint.html)
- [The Inner Workings of Safepoints 2023 - mostlynerdless.de](https://mostlynerdless.de/blog/2023/07/31/the-inner-workings-of-safepoints/)


























