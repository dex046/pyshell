from shell import MAX_CMD_HISTORYLINE
from shell import CMD_ALIASES
from shell import CMD_HISTORY_FILE
from shell import USER_HOME
import os
import shlex


def write_cmd_history(cmd_tokens):

    if not os.path.exists(CMD_HISTORY_FILE):
        os.system('touch %s' % CMD_HISTORY_FILE)
        print("create %s file" % CMD_HISTORY_FILE)
        #print("create file")

    cmd_len = len(open(CMD_HISTORY_FILE, "r").readlines())

    if cmd_len >= MAX_CMD_HISTORYLINE:
        history = open(CMD_HISTORY_FILE, "r")
        lines = history.readlines()
        history.close()

        lines.remove(lines[0])

        history = open(CMD_HISTORY_FILE, "w")
        history.write("".join(lines))
        history.flush()
        history.close()

    history = open(CMD_HISTORY_FILE, "a")
    for string in cmd_tokens:
        history.write(string + " ")
    history.write("\n")

    history.flush()
    history.close()


def read_cmd_history():
    pass


def write_cmd_error_log():
    pass


def search_alias(cmd_string):
    aliases = open(CMD_ALIASES, "r")
    cmd_string = cmd_string.replace("\n", "")
    #print(cmd_string)
    for line in aliases:
        line = line.split("#")
        if "" == line[0].replace(" ", "").replace("\t", "").replace("\n", ""):
            #print("this is # line")
            pass
        else:
            alias_line = line[0].split("=")
            if "alias" in alias_line[0] and cmd_string in alias_line[0]:
                alias_line[0] = alias_line[0].replace(" ", "").replace("\t", "").replace("\n", "")
                if alias_line[0] == "alias" + cmd_string:
                    return [True, alias_line[1]]
                else:
                    return [False, ""]
            else:
                continue

    return [False, ""]

