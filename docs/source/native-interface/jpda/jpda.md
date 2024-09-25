# JPDA

## Java 调试支持技术栈



学习 Java 技术栈时，有一个很容易让人混乱的东西：一堆 Java JEP(JDK Enhancement Proposals) 技术名称和规范，叠加上 Java 几十年的历史变化，过期文档。对于我们这种非英语母语的人，面对一堆英文已经吃力，还要记住一堆缩写，简直想放弃了。很多 JEP  就是定义规范接口或数据结构，只是说明了Java 技术栈的一个水平切面。实现上联系不上技术规范与技术规范之间、实现与实现之间的全景关系图。让人很难看清楚技术栈全景关系。



Java 调试支持技术栈也有这个问题。下图尝试总结一下技术栈的依赖关系。


:::{figure-md} 图: Java 调试支持技术栈

<img src="/native-interface/jpda/debugging-tec-stack.drawio.svg" alt="图: Java 调试支持技术栈">

*图: Java 调试支持技术栈*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fdebugging-tec-stack.drawio.svg)*

## 参考
- [A Short Primer on Java Debugging Internals - Johannes-Bechberger@foojay.io](https://foojay.io/today/a-short-primer-on-java-debugging-internals/)
- [Virtual Threads and Debugger Support - OpenJDK Wiki](https://wiki.openjdk.org/display/loom/Debugger+Support)
