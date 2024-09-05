# 源码结构

看大项目，历史久远的项目的源码，其中之一的麻烦是目录结构繁杂。下面说说 OpenJDK 的目录结构。

> https://openjdk.org/guide/

> - hotspot
>   - [cpu](https://github.com/openjdk/jdk/tree/master/src/hotspot/cpu) - Compiler, Runtime
>   - [os](https://github.com/openjdk/jdk/tree/master/src/hotspot/os) - Runtime
>   - [os_cpu](https://github.com/openjdk/jdk/tree/master/src/hotspot/os_cpu) - Compiler
>   - share
>     - [adlc](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/adlc) - Compiler
>     - [asm](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/asm) - Runtime
>     - [c1](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/c1) - Compiler
>     - [cds](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/cds) - Runtime
>     - [ci](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/ci) - Compiler
>     - [classfile](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/classfile) - Runtime
>     - [code](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/code) - Compiler
>     - [compiler](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/compiler) - Compiler
>     - [gc](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/gc) - GC
>     - [include](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/include) - HotSpot
>     - [interpreter](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/interpreter) - Runtime
>     - [jfr](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/jfr) - JFR
>     - [jvmci](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/jvmci) - Compiler
>     - [libadt](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/libadt) - Compiler
>     - [logging](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/logging) - Runtime
>     - [memory](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/memory) - GC, Runtime
>     - [metaprogramming](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/metaprogramming) - HotSpot
>     - [nmt](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/nmt) - Runtime
>     - [oops](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/oops) - GC, Runtime
>     - [opto](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/opto) - Compiler
>     - [precompiled](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/precompiled) - HotSpot
>     - [prims](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/prims) - Runtime, Serviceability
>     - [runtime](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/runtime) - Runtime
>     - [sanitizers](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/sanitizers) - Runtime
>     - [services](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/services) - Runtime
>     - [utilities](https://github.com/openjdk/jdk/tree/master/src/hotspot/share/utilities) - GC, Runtime
> - java.base
>   - Core Libs should almost always be included but Java Language, HotSpot, Security and/or I18n may also be involved.
>   - [linux]/classes
>     - [com/sun/crypto](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/com/sun/crypto) - Security
>     - [com/sun/security](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/com/sun/security) - Security
>     - [crypto](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/javax/crypto) - Security
>     - [linux]/internal
>       - [access](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/access) - Core Libs, Security
>       - [event](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/event) - JFR
>       - [foreign](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/foreign) - Core Libs
>       - [icu](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/icu) - Core Libs
>       - [io](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/io) - Core Libs
>       - [javac](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/javac) - Java Language (javac)
>       - [jimage](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/jimage) - Core Libs
>       - [jmod](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/jmod) - Core Libs
>       - [jrtfs](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/jrtfs) - Core Libs
>       - [[aix](https://github.com/openjdk/jdk/tree/master/java.base/aix/classes/jdk/internal/loader), [macosx](https://github.com/openjdk/jdk/tree/master/java.base/macosx/classes/jdk/internal/loader), [share](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/jdk/internal/loader), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/classes/jdk/internal/loader), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/classes/jdk/internal/loader)]/loader - Core Libs
>       - [logger](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/logger) - Core Libs
>       - [math](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/math) - Core Libs
>       - [[share](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/jdk/internal/misc), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/classes/jdk/internal/misc), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/classes/jdk/internal/misc)]/misc - Core Libs, HotSpot
>       - [module](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/module) - Core Libs
>       - [org/objectweb](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/org/objectweb) - Core Libs
>       - [org/xml](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/org/xml) - Core Libs
>       - [perf](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/perf) - Runtime
>       - [[linux](https://github.com/openjdk/jdk/tree/master/java.base/linux/classes/jdk/internal/platform), [share](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/jdk/internal/platform), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/classes/jdk/internal/platform), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/classes/jdk/internal/platform)]/platform - HotSpot
>       - [ref](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/ref) - Core Libs, GC
>       - [reflect](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/reflect) - Core Libs
>       - [util/random](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/util/random) - Core Libs
>       - [util/regex](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/util/regex) - Core Libs
>       - [util/xml](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/util/xml) - Core Libs
>       - [vm](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/jdk/internal/vm) - HotSpot
>     - [invoke](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/sun/invoke) - Core Libs
>     - [[share](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/java/io), [sun](https://github.com/openjdk/jdk/tree/master/java.base/windows/classes/sun/io), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/classes/java/io)]/io - Core Libs
>     - [unix]/java
>       - [[share](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/java/lang), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/classes/java/lang), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/classes/java/lang)]/lang - Core Libs
>       - [math](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/java/math) - Core Libs
>       - [time](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/java/time) - Core Libs
>     - [launcher](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/sun/launcher) - Tools, Core Libs
>     - [META-INF/services](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/META-INF/services) - Core Libs
>     - [[javax](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/javax/net), [macosx](https://github.com/openjdk/jdk/tree/master/java.base/macosx/classes/java/net)]/net - Net
>     - [[aix](https://github.com/openjdk/jdk/tree/master/java.base/aix/classes/sun/nio), [java](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/java/nio), [linux](https://github.com/openjdk/jdk/tree/master/java.base/linux/classes/sun/nio), [macosx](https://github.com/openjdk/jdk/tree/master/java.base/macosx/classes/sun/nio), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/classes/sun/nio), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/classes/sun/nio)]/nio - NIO
>     - [reflect](https://github.com/openjdk/jdk/tree/master/src/java.base/share/classes/sun/reflect) - Core Libs
>     - [[apple](https://github.com/openjdk/jdk/tree/master/java.base/macosx/classes/apple/security), [java](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/java/security), [javax](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/javax/security), [macosx](https://github.com/openjdk/jdk/tree/master/java.base/macosx/classes/apple/security), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/classes/sun/security), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/classes/sun/security)]/security - Security
>     - [[java](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/java/text), [sun](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/sun/text)]/text - I18n
>     - [[java](https://github.com/openjdk/jdk/tree/master/java.base/share/classes/java/util), [macosx](https://github.com/openjdk/jdk/tree/master/java.base/macosx/classes/sun/util), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/classes/sun/util)]/util - I18n, Core Libs
>   - [unix]/conf
>     - [sdp](https://github.com/openjdk/jdk/tree/master/src/java.base/unix/conf/sdp) - Net
>     - [security](https://github.com/openjdk/jdk/tree/master/src/java.base/share/conf/security) - Security
>   - [[share](https://github.com/openjdk/jdk/tree/master/java.base/share/legal), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/legal)]/legal
>   - [[share](https://github.com/openjdk/jdk/tree/master/java.base/share/lib/security), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/lib/security)]/lib/security - Security
>   - man
>     - [java.1](https://github.com/openjdk/jdk/tree/master/src/src/java.base/share/man/java.1) - Tools, HotSpot
>     - [keytool.1](https://github.com/openjdk/jdk/tree/master/src/src/java.base/share/man/keytool.1) - Security
>   - [unix]/native
>     - [common](https://github.com/openjdk/jdk/tree/master/src/java.base/windows/native/common)
>     - [[share](https://github.com/openjdk/jdk/tree/master/java.base/share/native/include), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/native/include), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/native/include)]/include - Runtime, Core Libs
>     - [jspawnhelper](https://github.com/openjdk/jdk/tree/master/src/java.base/unix/native/jspawnhelper) - Tools
>     - [[share](https://github.com/openjdk/jdk/tree/master/java.base/share/native/launcher), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/native/launcher), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/native/launcher)]/launcher - Tools
>     - [[aix](https://github.com/openjdk/jdk/tree/master/java.base/aix/native/libjava), [linux](https://github.com/openjdk/jdk/tree/master/java.base/linux/native/libjava), [macosx](https://github.com/openjdk/jdk/tree/master/java.base/macosx/native/libjava), [share](https://github.com/openjdk/jdk/tree/master/java.base/share/native/libjava), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/native/libjava), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/native/libjava)]/libjava - Core Libs
>     - [[share](https://github.com/openjdk/jdk/tree/master/java.base/share/native/libjimage), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/native/libjimage), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/native/libjimage)]/libjimage - Core Libs
>     - [[aix](https://github.com/openjdk/jdk/tree/master/java.base/aix/native/libjli), [macosx](https://github.com/openjdk/jdk/tree/master/java.base/macosx/native/libjli), [share](https://github.com/openjdk/jdk/tree/master/java.base/share/native/libjli), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/native/libjli), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/native/libjli)]/libjli - Tools, Core Libs
>     - [libjsig](https://github.com/openjdk/jdk/tree/master/src/java.base/unix/native/libjsig) - HotSpot
>     - [[macosx](https://github.com/openjdk/jdk/tree/master/java.base/macosx/native/libnet), [share](https://github.com/openjdk/jdk/tree/master/java.base/share/native/libnet), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/native/libnet), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/native/libnet)]/libnet - Net
>     - [[aix](https://github.com/openjdk/jdk/tree/master/java.base/aix/native/libnio), [linux](https://github.com/openjdk/jdk/tree/master/java.base/linux/native/libnio), [macosx](https://github.com/openjdk/jdk/tree/master/java.base/macosx/native/libnio), [share](https://github.com/openjdk/jdk/tree/master/java.base/share/native/libnio), [unix](https://github.com/openjdk/jdk/tree/master/java.base/unix/native/libnio), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/native/libnio)]/libnio - NIO
>     - [libosxsecurity](https://github.com/openjdk/jdk/tree/master/src/java.base/macosx/native/libosxsecurity) - Security
>     - [[aix](https://github.com/openjdk/jdk/tree/master/java.base/aix/native/libsyslookup), [share](https://github.com/openjdk/jdk/tree/master/java.base/share/native/libsyslookup), [windows](https://github.com/openjdk/jdk/tree/master/java.base/windows/native/libsyslookup)]/libsyslookup - Core Libs
>     - [libverify](https://github.com/openjdk/jdk/tree/master/src/java.base/share/native/libverify) - Runtime
>     - [libzip](https://github.com/openjdk/jdk/tree/master/src/java.base/share/native/libzip) - Core Libs
>   - share/data
>     - [blockedcertsconverter](https://github.com/openjdk/jdk/tree/master/src/java.base/share/data/blockedcertsconverter) - Security
>     - [cacerts](https://github.com/openjdk/jdk/tree/master/src/java.base/share/data/cacerts) - Security
>     - [currency](https://github.com/openjdk/jdk/tree/master/src/java.base/share/data/currency) - I18n
>     - [lsrdata](https://github.com/openjdk/jdk/tree/master/src/java.base/share/data/lsrdata) - I18n
>     - [publicsuffixlist](https://github.com/openjdk/jdk/tree/master/src/java.base/share/data/publicsuffixlist) - Client Libs
>     - [tzdata](https://github.com/openjdk/jdk/tree/master/src/java.base/share/data/tzdata) - I18n
>     - [unicodedata](https://github.com/openjdk/jdk/tree/master/src/java.base/share/data/unicodedata) - I18n
> - [java.compiler](https://github.com/openjdk/jdk/tree/master/src/java.compiler) - Java Language (javac)









