# JNI



## 本节适合什么读者

本节不是从入门到精通类型的。假设读者已经了解过 JNI 的基本使用方法和阅读过相关官方文档。

## JNI 无处不在

我以前一真觉得，JNI 不过是在 Pure Java 解决不了的底层操作或性能瓶颈时，才会使用到的技术。实现方式是写个动态链接库(*.so)，写个 java native method 就完了。最近研究了一下，发现只要使用 openjdk，基本就直接或间接使用了 JNI 了。 openjdk 内部使用 JNI 的情况后面会分析。

## JNI 相关数据结构

> Bad programmers worry about the code. Good programmers worry about data structures and their relationships.
> -- Linus Torvalds


先来看看 JNI 相关的数据结构。

![JNI Data Structure](jni-data-struct.drawio.svg)
*JNI Data Structure*

*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fblog.mygraphql.com%2Fzh%2Fnotes%2Fjava%2Fjni-junior%2Fjvmti-data-struct.drawio.svg)*



以上内容参考了： [Java Native Interface Specification](https://docs.oracle.com/en/java/javase/21/docs/specs/jni/index.html)

上图有一些文字补充：
- C/C++ 实现的 JNI 代码主要交互 API 是 `JNIInvokeInterface_` 与 `JNINativeInterface_` 
- 所有线程理论上都可以 Attach 到 JVM 上成为一个 jvm thread。参与到 Stop The World 等机制当中。
- `JNIEnv_` 实例是与线程挂钩的，不应该在线程间共享。
- 注意不同的着色代表不同的分层范畴
- 其中牵涉到引用记数和 GC

暂时是引用 [Java Native Interface Specification](https://docs.oracle.com/en/java/javase/21/docs/specs/jni/index.html) 和小部分代码整理。未再深入研究其内部的结构。





## Java Laucher 的 JNI 使用

下面以 jstack 应用程序为例，说明一下 Java Laucher 的 JNI 使用。

![Java Laucher 示例: jstack.exe](launcher.drawio.svg)
*Java Laucher 示例: jstack.exe*

*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fblog.mygraphql.com%2Fzh%2Fnotes%2Fjava%2Fjni-junior%2Flauncher.drawio.svg)*

当我了解到 jstack.exe 甚至是 java.exe 本身其实都是利用 JNI API 去嵌入 JVM(libjvm.so) 时，是有点开眼界的。其实 Java 设计之初就是支持桌面应用，Native Application 可以轻松嵌入 JVM。只是作为现在主流的后端开发界来说，已经很少提这个“初心”了。








