import platform
import os

# https://stackoverflow.com/a/39819465

is32bit = (platform.architecture()[0] == '32bit')
system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if is32bit else 'System32')
bash_exe = os.path.join(system32, 'bash.exe')
