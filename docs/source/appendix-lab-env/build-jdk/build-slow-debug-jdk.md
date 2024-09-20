# JDK 构建、调试环境

本书的操作环境如下：
- 操作系统： Ubuntu 22.04.4 LTS (kernel: 6.8.0-40-generic)
- CPU Arch: x86_64

## Git repo

```bash
cd /home/labile/opensource/
git clone https://github.com/openjdk/jdk/
git checkout tags/jdk-21+35 -b jdk-21+35
```
以下假设 JDK 源码绝对路径为： `/home/labile/opensource/jdk`

## 构建 OpenJDK


> 参考：https://openjdk.org/groups/build/doc/building.html

### 构建的依赖

```bash
sudo apt install openjdk-21-jdk
sudo apt-get install libasound2-dev
sudo apt-get install libcups2-dev
sudo apt-get install libfontconfig1-dev
```

构建过程要用到 Java。好奇的人会思考这是个[鸡生蛋蛋生鸡](https://zh.wikipedia.org/zh-hans/%E5%85%88%E6%9C%89%E9%B8%A1%E8%BF%98%E6%98%AF%E5%85%88%E6%9C%89%E8%9B%8B)的问题。

> [**循環論證**（circular argument）、**循環推理**（**循環推論**；circular reasoning）](https://zh.wikipedia.org/wiki/%E5%BE%AA%E7%92%B0%E8%AB%96%E8%AD%89)

其实构建依赖的 Java 的版本，一般是允许比构建的目标版本低的。所以好像问题解决了。



### 构建配置

#### hsdis 工具分析 JVM 编译生成的代码

由于打算用 hsdis 工具分析 JVM 编译生成的代码。即反汇编 JIT/Interpreter 的机器代码。所以要让 JDK 支持 hsdis 。


> 参考:
> - https://mail.openjdk.org/pipermail/core-libs-dev/2022-February/086176.html
> - https://git.openjdk.java.net/jdk/pull/7578

因为会使用 hsdis 工具分析 JVM 内部数据，所以 `./configure ` 要加上 `--enable-hsdis-bundling  --with-hsdis=binutils --with-binutils-src=/home/labile/opensource/jdk/external-libs/binutils/binutils-2.37` 。 参数 `--enable-hsdis-bundling` 让 JDK 内置 hsdis 实现，就不需要后面自己 copy .so 文件了。

由于 license 问题，要自己下载 binutils 源码：

```bash
mkdir /home/labile/opensource/jdk/external-libs/
cd /home/labile/opensource/jdk/external-libs/
curl -L -O https://ftp.gnu.org/gnu/binutils/binutils-2.37.tar.gz
tar -xvf binutils-2.37.tar.gz
```

#### configure jdk build

```bash
bash ./configure --with-debug-level=slowdebug --with-native-debug-symbols=internal --with-jvm-variants=server --with-target-bits=64 --enable-hsdis-bundling  --with-hsdis=binutils --with-binutils-src=/home/labile/opensource/jdk/external-libs/binutils/binutils-2.37 --with-conf-name=linux-x86_64-server-slowdebug-hsdis
```

`--with-debug-level` 的定义如下：

> See the definition [here](http://hg.openjdk.java.net/jdk/jdk/file/c3066f7465fa/make/autoconf/jdk-options.m4#l40):
>
> ```java
> ###############################################################################
> # Set the debug level
> #    release: no debug information, all optimizations, no asserts.
> #    optimized: no debug information, all optimizations, no asserts, HotSpot target is 'optimized'.
> #    fastdebug: debug information (-g), all optimizations, all asserts
> #    slowdebug: debug information (-g), no optimizations, all asserts
> AC_DEFUN_ONCE([JDKOPT_SETUP_DEBUG_LEVEL],
> ```

同一个 JDK git work dir 支持使用多个 build profile(conf-name) 配置，来让测试者可以快速切换。用 `--with-conf-name=` 指定 `conf-name`(配置名)。


输出：

```
====================================================
A new configuration has been successfully created in
/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis
using configure arguments '...'.

Configuration summary:
* Name:           linux-x86_64-server-slowdebug-hsdis
* Debug level:    slowdebug
* HS debug level: debug
* JVM variants:   server
* JVM features:   server: 'cds compiler1 compiler2 epsilongc g1gc jfr jni-check jvmci jvmti management parallelgc serialgc services shenandoahgc vm-structs zgc' 
* OpenJDK target: OS: linux, CPU architecture: x86, address length: 64
* Version string: 21-internal-adhoc.labile.jdk (21-internal)
* Source date:    1723623824 (2024-08-14T08:23:44Z)

Tools summary:
* Boot JDK:       openjdk version "21.0.4" 2024-07-16 OpenJDK Runtime Environment (build 21.0.4+7-Ubuntu-1ubuntu222.04) OpenJDK 64-Bit Server VM (build 21.0.4+7-Ubuntu-1ubuntu222.04, mixed mode, sharing) (at /usr/lib/jvm/java-21-openjdk-amd64)
* Toolchain:      gcc (GNU Compiler Collection)
* C Compiler:     Version 11.4.0 (at /usr/bin/gcc)
* C++ Compiler:   Version 11.4.0 (at /usr/bin/g++)
```

由于 jdk 支持多配置 build profile 并存，配置 profile 在 jdk 中正式名是 `Configuration Name` 或 `CONF_NAME` 。

从上面输出可见，`CONF_NAME` 命名为： `linux-x86_64-server-slowdebug-hsdis` 。

这个名字也会在目录中看到：`./build/linux-x86_64-server-slowdebug-hsdis



### 构建

```bash
cd /home/labile/opensource/jdk
/usr/bin/gmake CONF_NAME=linux-x86_64-server-slowdebug-hsdis LOG=info,cmdlines jdk
```



### 测试构建结果

```bash
./build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java 
```



## IDE

很多高手都不用 GUI ，用 vim 等等。但我还不是高手，所以我用 VSCode 来帮助我浏览代码与调试代码。其实 OpenJDK 源码库中，已经有如何使用 VSCode 的说明：[IDE support in the JDK](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/doc/ide.md#visual-studio-code)



```bash
make vscode-project CONF=linux-x86_64-server-slowdebug
```



这个命令生成了：

`./build/linux-x86_64-server-slowdebug-hsdis/jdk.code-workspace`

这个 VSCode worksplace 配置文件。其内容大体如下：

```json
{
	"folders": [
		{
			"name": "Source root",
			"path": "/home/labile/opensource/jdk"
		},
		{
			"name": "Build artifacts",
			"path": "/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis
		}
	],
	"extensions": {
		"recommendations": [
			"ms-vscode.cpptools"
		]
	},
	"settings": {
		// Configure cpptools IntelliSense
		"C_Cpp.intelliSenseCachePath": "/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis.vscode",
		"C_Cpp.default.compileCommands": "/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/compile_commands.json",
		"C_Cpp.default.cppStandard": "c++14",
		"C_Cpp.default.compilerPath": "/usr/bin/g++ ",

		// Additional conventions
		"files.associations": {
			"*.gmk": "makefile"
		},

		// Having these enabled slow down task execution
		"typescript.tsc.autoDetect": "off",
		"gulp.autoDetect": "off",
		"npm.autoDetect": "off",
		"grunt.autoDetect": "off",
		"jake.autoDetect": "off",

		// Certain types of files are not relevant for the file browser
		"files.exclude": {
			"**/.git": true,
			"**/.hg": true,
			"**/.DS_Store": true,
		},

		// Files that may be interesting to browse manually, but avoided during searches
		"search.exclude": {
			"**/*.class": true,
			"**/*.jsa": true,
			"**/*.vardeps": true,
			"**/*.o": true,
			"**/*.obj": true,
			"**/*.d": true,
			"**/*.d.*": true,
			"**/*_batch*": true,
			"**/*.marker": true,
			"**/compile-commands/": true,
			"**/objs": true,
			"**/launcher-objs": true,
			"**/*.cmdline": true,
			"**/*.log": true,
			".vscode": true,
			".clangd": true
		},

		// Trailing whitespace should never be used in this project
		"files.trimTrailingWhitespace": true,
		"java.project.sourcePaths": [
			"src/java.base/linux/classes",
			"src/java.base/share/classes"
		],
		"makefile.configureOnOpen": false,
		"debug.disassemblyView.showSourceCode": true
	}
}
```



其中 `"C_Cpp.default.compileCommands": "/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/compile_commands.json"`下面将会提到。



然后用 vscode 重新打开这个文件：

To use `./build/linux-x86_64-server-slowdebug-hsdis/jdk.code-workspace`, choose `File -> Open Workspace...` in Visual Studio Code。







### 编译数据库

[编译数据库(Compilation Database) ](https://clang.llvm.org/docs/JSONCompilationDatabase.html) 可以让 IDE 知道跨文件和目录的代码之间的关系。用这个关系就可以方便地在 IDE 实现代码跳转功能。

```bash
make compile-commands CONF=linux-x86_64-server-slowdebug
```

这会生成 `./build/linux-x86_64-server-slowdebug-hsdis compile_commands.json` 文件。下面是其中一行采样内容：

```json
{ "directory": "/home/labile/opensource/jdk/make", "file": "/home/labile/opensource/jdk/src/java.management/share/native/libmanagement/MemoryManagerImpl.c", "command": "/usr/bin/gcc -I/home/labile/opensource/jdk/build/support/modules_include/java.base -I/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/support/modules_include/java.base/linux -I/home/labile/opensource/jdk/src/java.base/share/native/libjava -I/home/labile/opensource/jdk/src/java.base/unix/native/libjava -I/home/labile/opensource/jdk/src/hotspot/share/include -I/home/labile/opensource/jdk/src/hotspot/os/posix/include -pipe -fstack-protector -DLIBC=gnu -D_GNU_SOURCE -D_REENTRANT -D_LARGEFILE64_SOURCE -DLINUX -DDEBUG -fstack-protector-all --param ssp-buffer-size=1 -g -gdwarf-4 -std=c11 -fno-strict-aliasing -Wall -Wextra -Wformat=2 -Wpointer-arith -Wsign-compare -Wunused-function -Wundef -Wunused-value -Wreturn-type -Wtrampolines -m64 -D_LITTLE_ENDIAN -DARCH='\"amd64\"' -Damd64 -D_LP64=1 -fno-omit-frame-pointer -fno-delete-null-pointer-checks -fno-lifetime-dse -fPIC -fvisibility=hidden -I/home/labile/opensource/jdk/src/java.management/share/native/libmanagement -I/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/support/headers/java.management -g -gdwarf-4 -Wno-unused-parameter -Wno-unused -Werror -O0 -c -o /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/support/native/java.management/libmanagement/MemoryManagerImpl.o /home/labile/opensource/jdk/src/java.management/share/native/libmanagement/MemoryManagerImpl.c -frandom-seed=\"MemoryManagerImpl.c\"" },
```



VSCode 的 clangd 插件，用到分析这个文件。

















