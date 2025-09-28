@rem
@rem Copyright 2015 the original author or authors.
@rem
@rem Licensed under the Apache License, Version 2.0 (the "License");
@rem you may not use this file except in compliance with the License.
@rem You may obtain a copy of the License at
@rem
@rem      https://www.apache.org/licenses/LICENSE-2.0
@rem
@rem Unless required by applicable law or agreed to in writing, software
@rem distributed under the License is distributed on an "AS IS" BASIS,
@rem WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@rem See the License for the specific language governing permissions and
@rem limitations under the License.
@rem

@if "%DEBUG%"=="" @echo off
@rem ##########################################################################
@rem
@rem  osmosis startup script for Windows
@rem
@rem ##########################################################################

@rem Set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" setlocal

set DIRNAME=%~dp0
if "%DIRNAME%"=="" set DIRNAME=.
@rem This is normally unused
set APP_BASE_NAME=%~n0
set APP_HOME=%DIRNAME%..

@rem Resolve any "." and ".." in APP_HOME to make it shorter.
for %%i in ("%APP_HOME%") do set APP_HOME=%%~fi

@rem Add default JVM options here. You can also use JAVA_OPTS and OSMOSIS_OPTS to pass JVM options to this script.
set DEFAULT_JVM_OPTS=

@rem Find java.exe
if defined JAVA_HOME goto findJavaFromJavaHome

set JAVA_EXE=java.exe
%JAVA_EXE% -version >NUL 2>&1
if %ERRORLEVEL% equ 0 goto execute

echo.
echo ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.
echo.
echo Please set the JAVA_HOME variable in your environment to match the
echo location of your Java installation.

goto fail

:findJavaFromJavaHome
set JAVA_HOME=%JAVA_HOME:"=%
set JAVA_EXE=%JAVA_HOME%/bin/java.exe

if exist "%JAVA_EXE%" goto execute

echo.
echo ERROR: JAVA_HOME is set to an invalid directory: %JAVA_HOME%
echo.
echo Please set the JAVA_HOME variable in your environment to match the
echo location of your Java installation.

goto fail

:execute
@rem Setup the command line

set CLASSPATH=%APP_HOME%\lib\osmosis-0.49.2.jar;%APP_HOME%\lib\osmosis-extract-0.49.2.jar;%APP_HOME%\lib\osmosis-apidb-0.49.2.jar;%APP_HOME%\lib\osmosis-areafilter-0.49.2.jar;%APP_HOME%\lib\osmosis-dataset-0.49.2.jar;%APP_HOME%\lib\osmosis-pbf-0.49.2.jar;%APP_HOME%\lib\osmosis-pbf2-0.49.2.jar;%APP_HOME%\lib\osmosis-pgsimple-0.49.2.jar;%APP_HOME%\lib\osmosis-pgsnapshot-0.49.2.jar;%APP_HOME%\lib\osmosis-replication-0.49.2.jar;%APP_HOME%\lib\osmosis-set-0.49.2.jar;%APP_HOME%\lib\osmosis-tagfilter-0.49.2.jar;%APP_HOME%\lib\osmosis-tagtransform-0.49.2.jar;%APP_HOME%\lib\osmosis-xml-0.49.2.jar;%APP_HOME%\lib\osmosis-core-0.49.2.jar;%APP_HOME%\lib\commons-dbcp-1.4.jar;%APP_HOME%\lib\spring-jdbc-5.3.30.jar;%APP_HOME%\lib\postgis-jdbc-2021.1.0.jar;%APP_HOME%\lib\osmosis-hstore-jdbc-0.49.2.jar;%APP_HOME%\lib\postgresql-42.6.0.jar;%APP_HOME%\lib\jpf-1.5.jar;%APP_HOME%\lib\osmpbf-1.5.0.jar;%APP_HOME%\lib\mysql-connector-j-8.0.33.jar;%APP_HOME%\lib\protobuf-java-3.25.0.jar;%APP_HOME%\lib\guava-32.1.3-jre.jar;%APP_HOME%\lib\commons-io-2.15.0.jar;%APP_HOME%\lib\commons-csv-1.10.0.jar;%APP_HOME%\lib\commons-codec-1.16.0.jar;%APP_HOME%\lib\commons-compress-1.24.0.jar;%APP_HOME%\lib\commons-pool-1.5.4.jar;%APP_HOME%\lib\spring-tx-5.3.30.jar;%APP_HOME%\lib\spring-beans-5.3.30.jar;%APP_HOME%\lib\spring-core-5.3.30.jar;%APP_HOME%\lib\checker-qual-3.37.0.jar;%APP_HOME%\lib\commons-logging-1.0.4.jar;%APP_HOME%\lib\failureaccess-1.0.1.jar;%APP_HOME%\lib\listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar;%APP_HOME%\lib\jsr305-3.0.2.jar;%APP_HOME%\lib\error_prone_annotations-2.21.1.jar;%APP_HOME%\lib\postgis-geometry-2021.1.0.jar;%APP_HOME%\lib\slf4j-api-1.7.32.jar;%APP_HOME%\lib\spring-jcl-5.3.30.jar


@rem Execute osmosis
"%JAVA_EXE%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% %OSMOSIS_OPTS%  -classpath "%CLASSPATH%" org.openstreetmap.osmosis.core.Osmosis %*

:end
@rem End local scope for the variables with windows NT shell
if %ERRORLEVEL% equ 0 goto mainEnd

:fail
rem Set variable OSMOSIS_EXIT_CONSOLE if you need the _script_ return code instead of
rem the _cmd.exe /c_ return code!
set EXIT_CODE=%ERRORLEVEL%
if %EXIT_CODE% equ 0 set EXIT_CODE=1
if not ""=="%OSMOSIS_EXIT_CONSOLE%" exit %EXIT_CODE%
exit /b %EXIT_CODE%

:mainEnd
if "%OS%"=="Windows_NT" endlocal

:omega
