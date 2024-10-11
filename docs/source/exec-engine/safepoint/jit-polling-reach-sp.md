# JIT 编译后的 Polling 与 Reach Safepoint



## Base

$RBP `callee-saved` others are `caller-saved`
$r12 - Java Heap base
$r15 - 存放 本线程的  JavaThread 指针



## Polling



## Reach and handle



### Signal Handle



JVM 启动初始化时，JVM 自用的 Signal Handler 安装：

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
  set_signal_handler(SIGSEGV);
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
    stub = SharedRuntime::polling_page_safepoint_handler_blob()->entry_point();
  }
  log_debug(safepoint)("... found polling page %s exception at pc = "
                       INTPTR_FORMAT ", stub =" INTPTR_FORMAT,
                       at_poll_return ? "return" : "loop",
                       (intptr_t)pc, (intptr_t)stub);
  return stub;
}

// JVM 启动初始化时，SafepointBlob Stub 机器码生成
static  _polling_page_safepoint_handler_blob = generate_handler_blob(CAST_FROM_FN_PTR(address, SafepointSynchronize::handle_polling_page_exception), POLL_AT_LOOP);
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



































