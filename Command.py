class Command:
    infd = 0
    outfd = 1
    infile_name = ""
    outfile_name = []
    cmd_args = []

    def __init__(self):
        self.infd = 0
        self.outfd = 1
        self.infile_name = ""
        self.outfile_name = []
        self.cmd_args = []