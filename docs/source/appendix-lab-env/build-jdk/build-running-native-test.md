# 构建与运行原生测试

参考：

> - https://htmlpreview.github.io/?https://raw.githubusercontent.com/openjdk/jdk/master/doc/testing.html
> - https://openjdk.org/projects/code-tools/jtreg/intro.html



## jtreg test framework



```bash
cd /home/labile/opensource/jdk/build
curl -O -L -v https://ci.adoptium.net/view/Dependencies/job/dependency_pipeline/lastSuccessfulBuild/artifact/jtreg/jtreg-7.4+1.tar.gz
tar -xvf ./jtreg-7.4+1.tar.gz

```

--with-jtreg=/home/labile/opensource/jdk/build/jtreg



### debug jtreg test

> https://foojay.io/today/debugging-openjdk-tests-in-vscode-without-losing-your-mind/

```bash
../vsreg/vsreg.py "ASGCT debug" -- make test TEST=jtreg:test/hotspot/jtreg/serviceability/AsyncGetCallTrace JTREG="VERBOSE=all" CONF=linux-x86_64-server-slowdebug
```





## googletest test framework

```bash
cd /home/labile/opensource/jdk/build
git clone -b v1.14.0 https://github.com/google/googletest
```

--with-gtest=/home/labile/opensource/jdk/build/googletest



```bash
/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/gtest/gtestLauncher --gtest_list_tests -jdk:/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/jdk | less



/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/gtest/gtestLauncher -jdk:/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/jdk --gtest_filter="*LogTagSet*"
```



### debug gtest

`launch.json` of vscode:

```json
{
            "name": "gtestLauncher",
            "type": "cppdbg",
            "request": "launch",
            "program": "/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/gtest/gtestLauncher",
            "args": [
                "-jdk:/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/jdk",
                "--gtest_filter='*ArgumentsTest*'" //added my me
            ],
            "stopAtEntry": false,
            "cwd": "/home/labile/opensource/jdk",
            "environment": [],
            "externalConsole": false,
            "preLaunchTask": "Make 'exploded-image'",
            "osx": {
                "MIMode": "lldb",
                "internalConsoleOptions": "openOnSessionStart",
                "args": [
                    "--gtest_color=no",
                    "-jdk:/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/jdk"
                ]
            },
            "linux": {
                "MIMode": "gdb",
                "setupCommands": [
                    {
                        "text": "handle SIGSEGV noprint nostop",
                        "description": "Disable stopping on signals handled by the JVM"
                    }
                ]
            }
        }
```





## run test

```bash
cd /home/labile/opensource/jdk

bash configure --with-debug-level=slowdebug --with-native-debug-symbols=internal --with-jvm-variants=server --with-target-bits=64 \
  --with-conf-name=linux-x86_64-server-slowdebug \
  --with-jtreg=/home/labile/opensource/jdk/build/jtreg \
  --with-gtest=/home/labile/opensource/jdk/build/googletest

make clean CONF=linux-x86_64-server-slowdebug
make test TEST="tier1" CONF=linux-x86_64-server-slowdebug
# make test-tier1 CONF=linux-x86_64-server-slowdebug




cd /home/labile/opensource/jdk
make test TEST="gtest:LogTagSet"

make test TEST="hotspot:hotspot_gc" JTREG="JOBS=1;TIMEOUT_FACTOR=8;JAVA_OPTIONS=-XshowSettings -Xlog:gc+ref=debug"

make test TEST="jtreg:test/hotspot:hotspot_gc test/hotspot/jtreg/native_sanity/JniVersion.java"

```



###  test selection

> https://htmlpreview.github.io/?https://raw.githubusercontent.com/openjdk/jdk/master/doc/testing.html
>
> The test specifications given in `TEST` is parsed into fully qualified test descriptors, which clearly and unambiguously show which tests will be run. As an example, `:tier1` will expand to include all subcomponent test directories that define `tier1`, for example: `jtreg:$(TOPDIR)/test/hotspot/jtreg:tier1 jtreg:$(TOPDIR)/test/jdk:tier1 jtreg:$(TOPDIR)/test/langtools:tier1 ...`. You can always submit a list of fully qualified test descriptors in the `TEST` variable if you want to shortcut the parser.



#### tiered test

> https://htmlpreview.github.io/?https://raw.githubusercontent.com/openjdk/jdk/master/doc/testing.html
>
> Ideally, all tests are run for every change but this may not be practical due to the limited testing resources, the scope of the change, etc.
>
> The source tree currently defines a few common test groups in the relevant `TEST.groups` files. There are test groups that cover a specific component, for example `hotspot_gc`. It is a good idea to look into `TEST.groups` files to get a sense what tests are relevant to a particular JDK component.
>
> Component-specific tests may miss some unintended consequences of a change, so other tests should also be run. Again, it might be impractical to run all tests, and therefore *tiered* test groups exist. Tiered test groups are not component-specific, but rather cover the significant parts of the entire JDK.
>
> Multiple tiers allow balancing test coverage and testing costs. Lower test tiers are supposed to contain the simpler, quicker and more stable tests. Higher tiers are supposed to contain progressively more thorough, slower, and sometimes less stable tests, or the tests that require special configuration.
>
> Contributors are expected to run the tests for the areas that are changed, and the first N tiers they can afford to run, but at least tier1.


