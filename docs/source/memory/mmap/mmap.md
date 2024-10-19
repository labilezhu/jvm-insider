# MMap - OS Memory Area



## Inspect



### pmap Linux command



### jcmd System.map

[The jcmd Command - OpenJDK23 - docs.oracle.com](https://docs.oracle.com/en/java/javase/23/docs/specs/man/jcmd.html)

> ## Synopsis
>
> `jcmd` [*pid* | *main-class*] *command*... | `PerfCounter.print` | `-f` *filename*
>
> `jcmd` [`-l`]
>
> ```
> jcmd` `-h
> ```
>
> 
>
> ## Commands for jcmd
>
> `System.map` \[_options_\] (Linux only)
>
> Prints an annotated process memory map of the VM process.
>
> Impact: Low
>
> **Note:**
>
> The following _options_ must be specified using either _key_ or _key_`=`_value_ syntax.
>
> _options_:
>
> - `-H`: (Optional) Human readable format (BOOLEAN, false)


```bash
/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/jcmd 168171 System.map
```




### Java options:  -XX:+PrintMemoryMapAtExit

Java options:  `-XX:+PrintMemoryMapAtExit` .  Print an annotated memory map at exit.

[Understanding JVM Memory Layout with OpenJDK24’s New PrintMemoryMapAtExit VM Option - foojay.io - 2024](https://foojay.io/today/understanding-jvm-memory-layout-with-openjdk24s-new-printmemorymapatexit-vm-option/) :

```bash
java -XX:+UnlockDiagnosticVMOptions -XX:+PrintMemoryMapAtExit -XX:NativeMemoryTracking=summary ReadMappedFile
```



```
from               to                        vsize prot          rss      hugetlb pgsz notes            info                                  file
========================================================================================================================================================================
0x0000000689400000-0x00000006a0c00000    394264576 rw-p     17076224            0 4K   com              JAVAHEAP                              -
0x00000006a0c00000-0x00000007ffc00000   5888802816 ---p            0            0 4K   -                JAVAHEAP                              -
0x00000007ffc00000-0x00000007ffd21000      1183744 rw-p      1183744            0 4K   com              JAVAHEAP                              /big/jdks/jdk24/lib/server/classes.jsa
0x00000007ffd21000-0x0000000800000000      3010560 rw-p            0            0 4K   com              JAVAHEAP                              -
0x00007f0000000000-0x00007f0000d90000     14221312 rw-p     14098432            0 4K   com              CDS                                   /big/jdks/jdk24/lib/server/classes.jsa
0x00007f0000d90000-0x00007f0001000000      2555904 ---p            0            0 4K   -                CDS                                   -
0x00007f0001000000-0x00007f0001010000        65536 rw-p        28672            0 4K   com              CLASS                                 -
0x00007f0001010000-0x00007f0001040000       196608 ---p            0            0 4K   -                CLASS                                 -
0x00007f0001040000-0x00007f0001050000        65536 rw-p        36864            0 4K   com              CLASS                                 -
0x00007f0001050000-0x00007f0041000000   1073414144 ---p            0            0 4K   -                CLASS                                 -
0x0000b49b739f0000-0x0000b49b739f1000         4096 r-xp         4096            0 4K   com              -                                     /big/jdks/jdk24/bin/java
0x0000b49b73a01000-0x0000b49b73a02000         4096 r--p         4096            0 4K   com              -                                     /big/jdks/jdk24/bin/java
0x0000b49b73a02000-0x0000b49b73a03000         4096 rw-p         4096            0 4K   com              -                                     /big/jdks/jdk24/bin/java
0x0000b49ba384e000-0x0000b49ba3881000       208896 rw-p       159744            0 4K   com              -                                     [heap]
...
0x0000ec2570000000-0x0000ec25700b0000       720896 rw-p       712704            0 4K   com              META                                  -
0x0000ec25700b0000-0x0000ec2570400000      3473408 ---p            0            0 4K   -                META                                  -
...
0x0000ec2580fbf000-0x0000ec2580fcf000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec2580fcf000-0x0000ec25811cd000      2088960 rw-p        12288            0 4K   com              STACK-1696938-GC-Thread               -
0x0000ec25811cd000-0x0000ec25811dd000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec25811dd000-0x0000ec25813db000      2088960 rw-p        12288            0 4K   com              STACK-1696937-GC-Thread               -
0x0000ec25813db000-0x0000ec25813eb000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec25813eb000-0x0000ec25815e9000      2088960 rw-p        12288            0 4K   com              STACK-1696936-GC-Thread               -
0x0000ec25815e9000-0x0000ec25815ed000        16384 ---p            0            0 4K   -                -                                     -
0x0000ec25815ed000-0x0000ec25817e7000      2072576 rw-p        32768            0 4K   com              -                                     -
0x0000ec2581808000-0x0000ec258180c000        16384 ---p            0            0 4K   com              STACK-1696934-Common-Cleaner          -
0x0000ec258180c000-0x0000ec2581a06000      2072576 rw-p        94208            0 4K   com              STACK-1696934-Common-Cleaner          -
0x0000ec2581a06000-0x0000ec2581a0a000        16384 ---p            0            0 4K   com              STACK-1696933-Notification-Thread     -
0x0000ec2581a0a000-0x0000ec2581c04000      2072576 rw-p        12288            0 4K   com              STACK-1696933-Notification-Thread     -
0x0000ec2581c04000-0x0000ec2581c08000        16384 ---p            0            0 4K   com              STACK-1696932-C1-CompilerThread0      -
0x0000ec2581c08000-0x0000ec2581e02000      2072576 rw-p        20480            0 4K   com              STACK-1696932-C1-CompilerThread0      -
0x0000ec2581e02000-0x0000ec2581e06000        16384 ---p            0            0 4K   com              STACK-1696931-C2-CompilerThread0      -
0x0000ec2581e06000-0x0000ec2584000000     35627008 rw-p        32768            0 4K   com              GC                                    -
0x0000ec2584000000-0x0000ec2584021000       135168 rw-p         4096            0 4K   -                -                                     -
0x0000ec2584021000-0x0000ec2588000000     66973696 ---p            0            0 4K   -                -                                     -
0x0000ec2588000000-0x0000ec2588021000       135168 rw-p         4096            0 4K   -                -                                     -
0x0000ec2588021000-0x0000ec258c000000     66973696 ---p            0            0 4K   -                -                                     -
0x0000ec258c000000-0x0000ec258c021000       135168 rw-p        12288            0 4K   -                -                                     -
0x0000ec258c021000-0x0000ec2590000000     66973696 ---p            0            0 4K   -                -                                     -
0x0000ec2590020000-0x0000ec259002c000        49152 r-xp        49152            0 4K   com              -                                     /big/jdks/jdk24/lib/libnet.so
0x0000ec259002c000-0x0000ec259003b000        61440 ---p            0            0 4K   com              -                                     /big/jdks/jdk24/lib/libnet.so
0x0000ec259003b000-0x0000ec259003c000         4096 r--p         4096            0 4K   com              -                                     /big/jdks/jdk24/lib/libnet.so
0x0000ec259003c000-0x0000ec259003d000         4096 rw-p         4096            0 4K   com              -                                     /big/jdks/jdk24/lib/libnet.so
0x0000ec2590040000-0x0000ec2590044000        16384 ---p            0            0 4K   com              STACK-1696930-Monitor-Deflation-Thread -
0x0000ec2590044000-0x0000ec259023e000      2072576 rw-p        12288            0 4K   com              STACK-1696930-Monitor-Deflation-Thread -
0x0000ec259023e000-0x0000ec2590242000        16384 ---p            0            0 4K   com              STACK-1696929-Service-Thread          -
0x0000ec2590242000-0x0000ec259043c000      2072576 rw-p        12288            0 4K   com              STACK-1696929-Service-Thread          -
0x0000ec259043c000-0x0000ec2590440000        16384 ---p            0            0 4K   com              STACK-1696928-Signal-Dispatcher       -
0x0000ec2590440000-0x0000ec259063a000      2072576 rw-p        12288            0 4K   com              STACK-1696928-Signal-Dispatcher       -
0x0000ec259063a000-0x0000ec259063e000        16384 ---p            0            0 4K   com              STACK-1696927-Finalizer               -
0x0000ec259063e000-0x0000ec2590838000      2072576 rw-p        90112            0 4K   com              STACK-1696927-Finalizer               -
0x0000ec2590838000-0x0000ec259083c000        16384 ---p            0            0 4K   com              STACK-1696926-Reference-Handler       -
0x0000ec259083c000-0x0000ec2590a36000      2072576 rw-p        94208            0 4K   com              STACK-1696926-Reference-Handler       -
0x0000ec2590a36000-0x0000ec2590a46000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec2590a46000-0x0000ec2590c44000      2088960 rw-p        16384            0 4K   com              STACK-1696925-VM-Thread               -
...
0x0000ec2591470000-0x0000ec2591480000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec2591480000-0x0000ec259167e000      2088960 rw-p        12288            0 4K   com              STACK-1696921-GC-Thread               -
0x0000ec259167e000-0x0000ec259168e000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec259168e000-0x0000ec259188c000      2088960 rw-p        12288            0 4K   com              -                                     -
0x0000ec259188c000-0x0000ec259189c000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec259189c000-0x0000ec259207a000      8249344 rw-p        12288            0 4K   com              STACK-1696919-GC-Thread,GC            -
0x0000ec259207a000-0x0000ec259783a000     92012544 ---p            0            0 4K   -                GC                                    -
0x0000ec259783a000-0x0000ec2597906000       835584 rw-p       770048            0 4K   com              GC                                    -
0x0000ec2597906000-0x0000ec25983fe000     11501568 ---p            0            0 4K   -                GC                                    -
0x0000ec25983fe000-0x0000ec2598400000         8192 rw-p         8192            0 4K   com              GC                                    -
0x0000ec2598400000-0x0000ec2598670000      2555904 rwxp       651264            0 4K   com              CODE                                  -
0x0000ec2598670000-0x0000ec259f937000    120352768 ---p            0            0 4K   -                CODE                                  -
0x0000ec259f937000-0x0000ec259fba7000      2555904 rwxp       626688            0 4K   com              CODE                                  -
0x0000ec259fba7000-0x0000ec259fec7000      3276800 ---p            0            0 4K   -                CODE                                  -
0x0000ec259fec7000-0x0000ec25a0137000      2555904 rwxp       237568            0 4K   com              CODE                                  -
0x0000ec25a0137000-0x0000ec25a7400000    120360960 ---p            0            0 4K   -                CODE                                  -
0x0000ec25a7400000-0x0000ec25afe3e000    144957440 r--s      1114112            0 4K   com              -                                     /big/jdks/jdk24/lib/modules
0x0000ec25afe40000-0x0000ec25afe50000        65536 r--s        65536            0 4K   com              -                                     /tmp/bigfile
```



- 变更跟踪：[Provide a diagnostic PrintMemoryMapAtExit switch on Linux - Enhancement issue on bugs.openjdk.org](https://bugs.openjdk.org/browse/JDK-8334026?page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel)

