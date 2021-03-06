import os
import sys
import shlex
import signal
import writeLog
import Command
from Error_handle import Error_handle

SHELL_STATUS_RUN = 0
SHELL_STATUS_STOP = 1

EXECUTE_QUIT = False
EXECUTE_NONE = False

MAX_CMD_HISTORYLINE = 1000
USER_HOME = "/home/" + os.getlogin()
CMD_HISTORY_FILE = USER_HOME + "/.shell_history"
CMD_ALIASES = USER_HOME + "/.shell_aliases"


BACKGROUND = False

LAST_PID = 0


def handle_signal(signum, frame):
    """

    :param signum:
    :param frame:
    :return:
    """
    #print("signal: " + str(signum) + "\n")
    if signum == signal.SIGINT:
        # print("pid = %d" % os.getpid())
        sys.stdout.write('\n')
        sys.stdout.write(prompt())
        sys.stdout.flush()


def prompt():
    cwd = os.getcwd().split('/')[-1]
    if not cwd:
        cwd = '/'

    line = '[' + os.getlogin() + '@' + os.uname()[1] + cwd + ']$ '
    return line


def read_cmd():
    global EXECUTE_NONE, EXECUTE_QUIT
    cmd_string = sys.stdin.readline()
    # print(cmd_string)
    # print(len(cmd_string))
    none_space_cmd = cmd_string.replace('\t', '').replace('\n', '').replace(' ', '')


    #len(ctrl-D) == 0
    if len(cmd_string) == 0:
        #print("len == 0")
        EXECUTE_QUIT = True
        return
    elif "exit" in cmd_string or "logout" in cmd_string:
        EXECUTE_QUIT = True
        return
    else:
        if len(none_space_cmd) == 0:
            EXECUTE_NONE = True
            return
        else:
            cmd_string = cmd_string.replace("~", USER_HOME)
            have_command, command = writeLog.search_alias(cmd_string)
            if have_command:
                return command
            return cmd_string


def get_filename(cmd, pattern):
    start = cmd.find(pattern, 0, len(cmd))
    file_name = []
    while start != -1:
        index = start + len(pattern)
        while cmd[index] == pattern:
            index = index + 1

        if index != start + len(pattern):
            start = cmd.find(pattern, index, len(cmd))
            continue

        file_name_index = [index, index]
        while cmd[index] == " " or cmd[index] == "\t":
            index = index + 1
            continue
        file_name_index[0] = index
        while index < len(cmd):
            if cmd[index] != "\0" and cmd[index] != " " \
                    and cmd[index] != "\t" and cmd[index] != ">>" \
                    and cmd[index] != ">" and cmd[index] != "<" \
                    and cmd[index] != "|" and cmd[index] != "&" and cmd[index] != "\n":
                index = index + 1
            else:
                break

        file_name_index[1] = index
        if file_name_index[1] > file_name_index[0]:
            #print(cmd[file_name_index[0]:file_name_index[1]])
            file_name.append(cmd[file_name_index[0]:file_name_index[1]])

        start = cmd.find(pattern, index, len(cmd))

    return file_name


def tokenize(cmd_string):
    return shlex.split(cmd_string)

# cat < test.txt | grep -n public > test2.txt
def parse(cmd_string):
    cmd_list = []
    cmd_string = cmd_string.split("|")
    #print(len(cmd_string))
    #print(cmd_string)
    for index in range(len(cmd_string)):
        cmd = Command.Command()
        if "<" in cmd_string[index]:
            file_name = get_filename(cmd_string[index], "<")
            if len(file_name) != 0:
                cmd.infile_name = file_name[0]
                cmd_string[index] = cmd_string[index].replace("<", " ")
                cmd_string[index] = cmd_string[index].replace(file_name[0], " ")
            #cmd.infd = os.open(cmd.infile_name, os.O_RDONLY)

        if ">" in cmd_string[index]:
            file_name = get_filename(cmd_string[index], ">")
            for file_i in range(len(file_name)):
                cmd.outfile_name.append([file_name[file_i], os.O_WRONLY | os.O_CREAT])
                cmd_string[index] = cmd_string[index].replace(">", " ")
                cmd_string[index] = cmd_string[index].replace(file_name[file_i], " ")
            #cmd.outfd = os.open(file_name, os.O_WRONLY | os.O_CREAT)

        if ">>" in cmd_string[index]:
            file_name = get_filename(cmd_string[index], ">>")
            for file_i in range(len(file_name)):
                cmd.outfile_name.append([file_name[file_i], os.O_APPEND])
                cmd_string[index] = cmd_string[index].replace(">>", " ")
                cmd_string[index] = cmd_string[index].replace(file_name[file_i], " ")
            #cmd.outfd = os.open(file_name, os.O_WRONLY | os.O_APPEND)

        if "&" in cmd_string[index]:
            if index != len(cmd_string) - 1:

                Error_handle.error_handle(Error_handle.SYNTAX_ERROR)
            else:
                cmd_string[index] = cmd_string[index].replace("&", " ")
                global BACKGROUND
                BACKGROUND = True
        #print(cmd_string[index])
        cmd.cmd_args = tokenize(cmd_string[index])
        cmd_list.append(cmd)

    return cmd_list
    pass


def execute(cmd_list):
    for index in range(len(cmd_list)):
        if index != len(cmd_list) - 1:
            fd = os.pipe()
            cmd_list[index].outfd = fd[1]
            cmd_list[index + 1].infd = fd[0]

        if index == 0 and len(cmd_list[index].infile_name) != 0:
            cmd_list[index].infd = os.open(cmd_list[index].infile_name, os.O_RDONLY)

        if len(cmd_list[index].outfile_name) != 0:
            # print(cmd_list[index].outfile_name[-1][0])
            if cmd_list[index].outfile_name[-1][1] == os.O_WRONLY | os.O_CREAT:
                cmd_list[index].outfd = os.open(cmd_list[index].outfile_name[-1][0], os.O_WRONLY | os.O_CREAT)
            elif cmd_list[index].outfile_name[-1][1] == os.O_APPEND:
                cmd_list[index].outfd = os.open(cmd_list[index].outfile_name[-1][0], os.O_WRONLY | os.O_APPEND | os.O_CREAT)
            else:
                print("open outfile error")
        # 因为父进程不会等待子进程（后台进程）的推出，所以为了避免僵尸进程，忽略SIGCHLD信号
        if BACKGROUND:
            signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        else:
            signal.signal(signal.SIGCHLD, signal.SIG_DFL)

        if builtin(cmd_list[index]):
            if cmd_list[index].infd != 0:
                os.close(cmd_list[index].infd)
            if cmd_list[index].outfd != 1:
                os.close(cmd_list[index].outfd)
            continue

        forkexec(cmd_list[index])

        if cmd_list[index].infd != 0:
            os.close(cmd_list[index].infd)
        if cmd_list[index].outfd != 1:
            os.close(cmd_list[index].outfd)

        if not BACKGROUND:
            while True:
                wpid, status = os.wait()
                # print("wait %d" % wpid)
                if wpid == LAST_PID:
                    break

        # cmd = cmd_list[index]
        # #if index != len(cmd_list) - 1:
        #
        # if len(cmd.infile_name) != 0:
        #     cmd.infd = os.open(cmd.infile_name, os.O_RDONLY)
        #     os.close(0)
        #     os.dup(cmd.infd)
        #
        # #for len(cmd.)


def builtin(cmd_obj):
    if "cd" in cmd_obj.cmd_args:
        if len(cmd_obj.cmd_args) == 1:
            path = USER_HOME
        else:
            path = cmd_obj.cmd_args[1]
        if os.path.exists(path):
            os.chdir(path)
        else:
            sys.stdout.write('cd: cannot access \'%s\': No such file or directory\n' % path)
            sys.stdout.flush()
            try:
                os.kill(os.getpid(), 9)
            except OSError:
                print("OSError")
        return True
    elif "history" in cmd_obj.cmd_args:
        return True
    else:
        return False


def forkexec(cmd_obj):
    # print(cmd_tokens)
    # print(cmd_obj.outfd)
    # print(cmd_obj.infd)
    pid = os.fork()
    if pid == 0:
        if BACKGROUND and cmd_obj.infd == 0:
            cmd_obj.infd = os.open("/dev/null", os.O_RDONLY)
        # 为什么一定要将0绑定输入，1绑定输出，
        # 因为0,1默认情况下是指标准输入与标准输出
        # 所以命令执行完毕后的结果一般也是直接写入fd=1的标准输出上，改成0,1后可以使得原来输出到终端上的信息输出
        # 到管道中，从而使得另一个命令从管道中读取信息
        # print(cmd_obj.cmd_args)
        # print(cmd_obj.cmd_args[0] + " " + str(cmd_obj.infd) + " " + str(cmd_obj.outfd))
        os.dup2(cmd_obj.infd, 0)
        # if cmd_obj.infd != 0:
        #     print("here infd")
        #     os.close(0)
        #     os.dup(cmd_obj.infd)

        os.dup2(cmd_obj.outfd, 1)
        # if cmd_obj.outfd != 1:
        #     print("here outfd")
        #     os.close(1)
        #     os.dup(cmd_obj.outfd)

        # print(cmd_obj.cmd_args[0] + " " + str(cmd_obj.infd) + " " + str(cmd_obj.outfd))
        # ctrl-c发送SIGINT信号的时候，是给组内的每个进程发送，
        if not BACKGROUND:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGQUIT, signal.SIG_DFL)
            # print("%d what" % os.getpid())
        try:
            os.execvp(cmd_obj.cmd_args[0], cmd_obj.cmd_args)

        except FileNotFoundError:
            sys.stdout.write("%s: command not found\n" % cmd_obj.cmd_args[0])
            sys.stdout.flush()
            try:
                os.kill(os.getpid(), 9)
            except OSError:
                print("OSError")
        except IndexError:
            pass
        except OSError:
            pass
        except TypeError:
            pass

    elif pid > 0:
        global LAST_PID
        LAST_PID = pid
        #print("last"+str(LAST_PID))
        # if not SET_PROCESS_GROUP_ID:
        #     SET_PROCESS_GROUP_ID = True
        #     os.setpgid(0, 0)
            # print("here %d" % os.getpgid(pid))

        if BACKGROUND:
            sys.stdout.write("process id %d.\n" % pid)
            sys.stdout.flush()

    return SHELL_STATUS_RUN


def init():
    global LAST_PID, BACKGROUND
    LAST_PID = 0
    BACKGROUND = False


def shell_loop():
    # print(os.tcgetpgrp(0))
    global EXECUTE_NONE, EXECUTE_QUIT
    while True:
        init()
        sys.stdout.write(prompt())
        sys.stdout.flush()

        cmd_string = read_cmd()
        if EXECUTE_NONE:
            EXECUTE_NONE = False
            continue
        elif EXECUTE_QUIT:
            EXECUTE_QUIT = False
            break
        else:
            pass

        cmd_list = parse(cmd_string)
        writeLog.write_cmd_history(cmd_string)
        execute(cmd_list)


def test():
    # test = "ls   -l"
    # print(test.replace(" ", ""))

    # open("test", "w")

    # test = "read -n1"
    # test = tokenize(test)
    # os.execvp(test[0], test)

    # ch = sys.stdin.read(1)
    # print(ord(ch) == 27)
    # print(ord('A'))
    # ch = ch.replace("\n", "")
    # print(ch == "^[[A")

    # str = "grep -n public > test2.txt"
    # str = str.split("<")
    # print(str)
    # print(len(str))

    # cmd_string = "cat < test.txt | grep - n public > test2.txt"
    # if "|" in cmd_string:
    #     cmd_string = cmd_string.split("|")
    #     print(range(len(cmd_string)))
    #     for index in range(len(cmd_string)):
    #         print(cmd_string[index])

    # cmd_fd = [0, 1]
    # cmd_fd[0] = os.open("test.txt", os.O_RDONLY)
    # cmd_fd[1] = os.open("result.txt", os.O_WRONLY)
    # print(cmd_fd[0])
    # print(cmd_fd[1])
    # pid = os.fork()
    # if pid == 0:
    #     if cmd_fd[0] != 0:
    #         os.close(0)
    #         print(os.dup(cmd_fd[0]))
    #         #print(cmd_fd[0])
    #     if cmd_fd[1] != 1:
    #         os.close(1)
    #         print(os.dup(cmd_fd[1]))
    #
    #     text = os.read(0, 20)
    #     os.write(1, text)
    #
    # else:
    #     pass

    #0代表标准输入，1代表标准输出
    # txt = os.read(0, 10)
    # os.write(1, txt)

    # cmd_string = "cat < test.txt >> test1.txt | grep - n public >> test2.txt"
    # print(get_filename(cmd_string, ">>"))

    # cmd_string = "cat < test.txt >> test1.txt | grep - n public >> test2.txt"
    # xms = Command.Command()
    # xms = parse(cmd_string)
    # for cmd in xms:
    #    # print(cmd.infile_name)
    #     print(cmd.outfile_name)


    # fd = os.pipe()
    # print(fd)
    # fd = os.pipe()
    # print(fd)
    # str = "i am who"
    # os.write(fd[1], str.encode("utf-8"))
    # print(os.read(fd[0], 20))

    #print(Error_handle.SYNTAX_ERROR)

    # print("%d" % signal.SIGINT)
    pass


def main():
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGQUIT, handle_signal)

    shell_loop()
    # test()
    pass


if __name__ == "__main__":
    main()


