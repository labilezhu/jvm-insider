# JavaThread Polling 与 Reach Safepoint



(javathread-state)=
## JavaThread - State
见 [Threads Handshake - JavaThread - State](threads-handshake.md#javathread-state) 一节。





(polling)=
## Polling
见 [Threads Handshake - Polling](threads-handshake.md#polling) 一节。


:::{figure-md}

<img src="/exec-engine/threads/vm-threads-cooperative/vm-operation.drawio.svg" alt="图:VM Operations">

*图:VM Operations*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fvm-operation.drawio.svg)*



(reach)=
## Reach and handle
见 [Threads Handshake - Reach and handle](threads-handshake.md#reach) 一节。



## Wait to exit global safepoint

call stack:

```
libc.so.6!syscall() (syscall.S:38)
libjvm.so!futex(volatile int * addr, int futex_op, int op_arg) (/jdk/src/hotspot/os/linux/waitBarrier_linux.cpp:49)
libjvm.so!LinuxWaitBarrier::wait(LinuxWaitBarrier * const this, int barrier_tag) (/jdk/src/hotspot/os/linux/waitBarrier_linux.cpp:76)
libjvm.so!WaitBarrierType<LinuxWaitBarrier>::wait(WaitBarrierType<LinuxWaitBarrier> * const this, int barrier_tag) (/jdk/src/hotspot/share/utilities/waitBarrier.hpp:128)
libjvm.so!SafepointSynchronize::block(JavaThread * thread) (/jdk/src/hotspot/share/runtime/safepoint.cpp:742)
libjvm.so!SafepointMechanism::process(JavaThread * thread, bool allow_suspend, bool check_async_exception) (/jdk/src/hotspot/share/runtime/safepointMechanism.cpp:148)
libjvm.so!SafepointMechanism::process_if_requested(JavaThread * thread, bool allow_suspend, bool check_async_exception) (/jdk/src/hotspot/share/runtime/safepointMechanism.inline.hpp:83)
libjvm.so!SafepointMechanism::process_if_requested_with_exit_check(JavaThread * thread, bool check_async_exception) (/jdk/src/hotspot/share/runtime/safepointMechanism.inline.hpp:88)
libjvm.so!ThreadSafepointState::handle_polling_page_exception(ThreadSafepointState * const this) (/jdk/src/hotspot/share/runtime/safepoint.cpp:985)
libjvm.so!SafepointSynchronize::handle_polling_page_exception(JavaThread * thread) (/jdk/src/hotspot/share/runtime/safepoint.cpp:778)
[Unknown/Just-In-Time compiled code] (Unknown Source:0)
```



相关代码：

```c++
// Process pending operation.
void ThreadSafepointState::handle_polling_page_exception() {
...
    // Process pending operation
    // We never deliver an async exception at a polling point as the
    // compiler may not have an exception handler for it (polling at
    // a return point is ok though). We will check for a pending async
    // exception below and deoptimize if needed. We also cannot deoptimize
    // and still install the exception here because live registers needed
    // during deoptimization are clobbered by the exception path. The
    // exception will just be delivered once we get into the interpreter.
    SafepointMechanism::process_if_requested_with_exit_check(self, false /* check asyncs */);
```



```c++
// Implementation of Safepoint blocking point

void SafepointSynchronize::block(JavaThread *thread) {

  // Threads shouldn't block if they are in the middle of printing, but...
  ttyLocker::break_tty_lock_for_safepoint(os::current_thread_id());

  ...
  JavaThreadState state = thread->thread_state();
  thread->frame_anchor()->make_walkable();

  uint64_t safepoint_id = SafepointSynchronize::safepoint_counter();

  // We have no idea where the VMThread is, it might even be at next safepoint.
  // So we can miss this poll, but stop at next.

  // Load dependent store, it must not pass loading of safepoint_id.
  thread->safepoint_state()->set_safepoint_id(safepoint_id); // Release store

  // This part we can skip if we notice we miss or are in a future safepoint.
  OrderAccess::storestore();
  // Load in wait barrier should not float up
  thread->set_thread_state_fence(_thread_blocked);

  _wait_barrier->wait(static_cast<int>(safepoint_id));
```







## 参考

- [Robbin Ehn: Handshaking HotSpot - Youtube Java Channel - 2020](https://www.youtube.com/watch?v=VBCOfAJ409s&ab_channel=Java)
- [HotSpot JVM Deep Dive - Safepoint - Youtube Java Channel](https://www.youtube.com/watch?v=JkbWPPNc4SI&ab_channel=Java)
- [Async-profiler - manual by use cases - krzysztofslusarski.github.io](https://krzysztofslusarski.github.io/2022/12/12/async-manual.html#tts)
- [Safepoints: Meaning, Side Effects and Overheads - psy-lob-saw.blogspot.com](https://psy-lob-saw.blogspot.com/2015/12/safepoints.html)
- [Where is my safepoint? - psy-lob-saw.blogspot.com](https://psy-lob-saw.blogspot.com/2014/03/where-is-my-safepoint.html)
- [The Inner Workings of Safepoints 2023 - mostlynerdless.de](https://mostlynerdless.de/blog/2023/07/31/the-inner-workings-of-safepoints/)



























