import time
import os
import signal

#测试ctrl c发出的信号是给进程还是进程组
#1 是同一个进程组收到信号，但是同一个进程组内的进程处理的信号的方式可以不同
#2 修改signal的处理方式也是针对进程组的，如果一个进程换进程组那么有可能signal的方式也会换（但是试验中好像只是接受不到信号了），
# 再将进程切换到原来的进程组则处理方式和原来一样了
#3 父进程换了和子进程相同的进程号，但是发现捕捉不到信号，换了进程组（换到不是启动程序的进程组），就收不到信号

# def signal_handle(signum, frame):
#     print("here %d" % os.getpid())
#
#
# def main():
#     print(os.getpid())
#     print(os.getpgid(0))
#     print(os.getpgid(os.getpid()))
#
#     pid = os.fork()
#     if pid == 0:
#         #signal.signal(signal.SIGINT, signal.SIG_DFL)
#         oldgid = os.getpgid(0)
#         os.setpgid(0, 0)
#         signal.signal(signal.SIGINT, signal_handle)
#         print("fork pid %d" % os.getpid())
#         print("fork pgid %d" % os.getpgid(0))
#         print("fork pgid %d" % os.getpgid(os.getpid()))
#         time.sleep(5)
#         #os.setpgid(0, oldgid)
#         #print("pgid=oldgid")
#         time.sleep(5)
#         #signal.signal(signal.SIGINT, signal_handle)
#         time.sleep(20)
#     else:
#         #signal.signal(signal.SIGINT, signal.SIG_DFL)
#         time.sleep(5)
#         os.setpgid(0, os.getpgid(pid))
#         signal.signal(signal.SIGINT, signal_handle)
#         print("father %d" % os.getpgid(0))
#         time.sleep(25)

def signal_handle(signum, frame):
    fd = os.open("signal_result.txt", os.O_WRONLY | os.O_TRUNC | os.O_CREAT)
    str = "here %d" % signum
    os.write(fd, str.encode("utf-8"))

def main():
    time.sleep(30)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handle)
    signal.signal(signal.SIGHUP, signal_handle)
    main()