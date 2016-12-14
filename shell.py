import os
import sys
import shlex
import exception
from subprocess import call
import signal
import writeLog

SHELL_STATUS_RUN = 0
SHELL_STATUS_STOP = 1

EXECUTE_QUIT = False
EXECUTE_NONE = False


MAX_CMD_HISTORYLINE = 1000
USER_HOME = "/home/" + os.getlogin()
CMD_HISTORY_FILE = USER_HOME + "/.shell_history"
CMD_ALIASES = USER_HOME + "/.shell_aliases"



def handle_signal(signum, frame):
    """

    :param signum:
    :param frame:
    :return:
    """
    #print("signal: " + str(signum) + "\n")
    if signum == signal.SIGINT:
        sys.stdout.write('\n')
        sys.stdout.write(prompt())
        sys.stdout.flush()


def prompt():
    username = os.getlogin()
    hostname = os.uname()[1]
    cwd = os.getcwd().split('/')[-1]
    if not cwd:
        cwd = '/'

    line = '[' + username + '@' + hostname + cwd + ']$ '
    return line


def read_cmd():
    global EXECUTE_NONE, EXECUTE_QUIT
    cmd_string = sys.stdin.readline()
    #print(cmd_string)
    none_space_cmd = cmd_string.replace('\t', '').replace('\n', '').replace(' ', '')


    #len(ctrl-D) == 0
    if len(cmd_string) == 0:
        print("len == 0")
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
            alias_line = writeLog.search_alias(cmd_string)
            print(alias_line)
            if alias_line[0]:
                return alias_line[1]
            return cmd_string


def tokenize(cmd_string):
    return shlex.split(cmd_string)


def execute(cmd_tokens):
    fin = sys.stdin
    fout = sys.stdout
    ferr = sys.stderr

    #print(cmd_tokens)
    pid = os.fork()
    if pid == 0:
        # try:
        if 'cd' in cmd_tokens:
            path = cmd_tokens[1]
            if os.path.exists(path):
                os.chdir(path)
            else:
                sys.stdout.write('cd: cannot access \'%s\': No such file or directory\n' % path)
                sys.stdout.flush()
                try:
                    os.kill(os.getpid(), 9)
                except OSError:
                    print("OSError")
        else:
            try:
                os.execvp(cmd_tokens[0], cmd_tokens)

            except FileNotFoundError:
                sys.stdout.write("%s: command not found\n" % cmd_tokens[0])
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
        while True:
            wpid, status = os.waitpid(pid, 0)
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                break
    return SHELL_STATUS_RUN


def shell_loop():
    global EXECUTE_NONE, EXECUTE_QUIT
    while True:
        sys.stdout.write(prompt())
        sys.stdout.flush()

        cmd_string = read_cmd()
        if EXECUTE_NONE == True:
            EXECUTE_NONE = False
            continue
        elif EXECUTE_QUIT == True:
            print("EXECUTE_QUIT")
            EXECUTE_QUIT = False
            break
        else:
            pass

        cmd_tokens = tokenize(cmd_string)
        writeLog.write_cmd_history(cmd_tokens)
        execute(cmd_tokens)


def test():
    # test = "ls   -l"
    # print(test.replace(" ", ""))

    # open("test", "w")
    pass


def main():
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGQUIT, handle_signal)

    shell_loop()
    # test()
    pass


if __name__ == "__main__":
    main()


