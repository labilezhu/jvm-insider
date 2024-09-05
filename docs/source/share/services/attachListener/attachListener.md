# Attach Listener

## 运行时动态 JVM Attach 机制

既然已经说了 JStack 那么就以 jstack 为例，顺便说说 JVM Attach 机制吧。其实 JVM Attach 机制也是 JVMTI 的一部分。


:::{figure-md} 图: JVM attach 机制

<img src="/share/services/attachListener/jvm-attach.drawio.svg" alt="图: JVM attach 机制">

*图: JVM attach 机制*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fjvm-attach.drawio.svg)*




:::{figure-md} 图: JVM attach 机制(Java 10 之前)

<img src="/share/services/attachListener/jvm-attach-before-java10.drawio.svg" alt="图: JVM attach 机制(Java 10 之前)">

*图: JVM attach 机制(Java 10 之前)*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fjvm-attach-before-java10.drawio.svg)*