# X86 64bit Calling Convention

## Registers



X86 64bit Registers:

| 64-bit register | Lower 32 bits | Lower 16 bits | Lower 8 bits |
|-----------------|---------------|---------------|--------------|
|       rax       |      eax      |      ax       |      al      |
|       rbx       |      ebx      |      bx       |      bl      |
|       rcx       |      ecx      |      cx       |      cl      |
|       rdx       |      edx      |      dx       |      dl      |
|       rsi       |      esi      |      si       |     sil      |
|       rdi       |      edi      |      di       |     dil      |
|       rbp       |      ebp      |      bp       |     bpl      |
|       rsp       |      esp      |      sp       |     spl      |
|       r8        |      r8d      |      r8w      |     r8b      |
|       r9        |      r9d      |      r9w      |     r9b      |
|       r10       |     r10d      |     r10w      |     r10b     |
|       r11       |     r11d      |     r11w      |     r11b     |
|       r12       |     r12d      |     r12w      |     r12b     |
|       r13       |     r13d      |     r13w      |     r13b     |
|       r14       |     r14d      |     r14w      |     r14b     |
|       r15       |     r15d      |     r15w      |     r15b     |



Linux X86 64bit Register Calling Convention :

| Register  |                 Purpose                 | Saved across calls |
|-----------|-----------------------------------------|--------------------|
|   %rax    |       temp register; return value       |        No          |
|   %rbx    |              callee-saved               |        Yes         |
|   %rcx    | used to pass 4th argument to functions  |        No          |
|   %rdx    | used to pass 3rd argument to functions  |        No          |
|   %rsp    |              stack pointer              |        Yes         |
|   %rbp    |       callee-saved; base pointer        |        Yes         |
|   %rsi    | used to pass 2nd argument to functions  |        No          |
|   %rdi    | used to pass 1st argument to functions  |        No          |
|   %r8     | used to pass 5th argument to functions  |        No          |
|   %r9     | used to pass 6th argument to functions  |        No          |
| %r10-r11  |               temporary                 |        No          |
| %r12-r15  |         callee-saved registers          |        Yes         |



## OpenJDK CallingSequences

> Source: https://wiki.openjdk.org/display/HotSpot/CallingSequences





### Native Code - Registers and Stack

On systems which support argument registers, leftward arguments are packed into registers until the registers run out, and then stack locations are used.



| value        | x86_64 |
| ------------ | ------ |
| native sp    | RSP    |
| return pc    | RSP(0) |
| int result   | RAX    |
| long result  | RAX    |
| float result | XMM0   |



### Interpreted Code

>https://wiki.openjdk.org/display/HotSpot/CallingSequences
>
>The following interpreter register assignments do not participate in calling conventions, but are given here for reference. Note that the Java stack pointer is the native stack pointer on x86 systems.
>
>| value           | x86_64 |
>| --------------- | ------ |
>| interp. java sp | RSP    |
>| interp. fp      | RBP    |



(jit-code-registers)=

### JIT 生成代码的寄存器分类

#### 固定寄存器

> https://wiki.openjdk.org/display/HotSpot/CallingSequences
>
> Certain registers may be reserved, by both the interpreter and compiler, to refer to current thread and the base of the heap (if compressed oops are enabled).
>
> | value      | x86_64 |
> | ---------- | ------ |
> | JavaThread | R15    |
> | HeapBase   | R12    |

- $r12 - 存放 Java Heap base (if compressed oops are enabled)
- $r15 - 存放 thread local 的 JavaThread 指针



#### 非固定(通用)寄存器

For compiled code, the integer register assignments are different between Java and C. They are shifted to allow JNI wrappers to insert an extra leading argument without moving arguments around. 目的是 JNI Call 时减少 Java arg 到 C arg 的 register copy 。



| X86 Register         | RSI   | RDX   | RCX   | R8    | R9    | RDI   |
| -------------------- | ----- | ----- | ----- | ----- | ----- | ----- |
| Linux X86 C argument | C #1  | C #2  | C #3  | C #4  | C #5  | C #0  |
| Java register arg    | int#0 | int#1 | int#2 | int#3 | int#4 | int#5 |



#### 非固定(通用)寄存器在 Frame 间保存

- $rbp - 由 `callee-saved` 
- 其它通用寄存器 - 由 `caller-saved`



### RBP - PreserveFramePointer

> 很多 stack 分析工具以是 RBP 为 stack walking  的 Frame Pointer 去实时获取应用 frame stack 的。原理见：[Preserving the base pointer](https://eli.thegreenplace.net/2011/09/06/stack-frame-layout-on-x86-64)

由于 默认启动下，OpenJDK 没按 X86 Calling Convention 去使用 RBP ，这让以 RBP 为 stack walking 的工具不能正常工作 。所以后来加入了 `-XX:+PreserveFramePointer` java 参数，可以让 OpenJDK 

- [Use RBP register as proper frame pointer in JIT compiled code on x86 - bugs.openjdk.org](https://bugs.openjdk.org/browse/JDK-8068945)
- [CPU Flame Graphs - brendangregg.com](https://www.brendangregg.com/FlameGraphs/cpuflamegraphs.html#Java)







## 参考

- [CallingSequences - openjdk.org](https://wiki.openjdk.org/display/HotSpot/CallingSequences)
- [Assembly 2: Calling convention - cs61.seas.harvard.edu](https://cs61.seas.harvard.edu/site/2018/Asm2/)
- [x86 calling conventions - wikipedia.org](https://en.wikipedia.org/wiki/X86_calling_conventions#x86-64_calling_conventions)
- [The 64 bit x86 C Calling Convention](https://aaronbloomfield.github.io/pdr/book/x86-64bit-ccc-chapter.pdf)
- [x86 Assembly, 64 bit](https://aaronbloomfield.github.io/pdr/book/x86-64bit-asm-chapter.pdf)
- [X86-64 Architecture Guide - scripts.mit.edu](http://6.s081.scripts.mit.edu/sp18/x86-64-architecture-guide.html)
- [x64 Architecture - microsoft.com](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/x64-architecture)