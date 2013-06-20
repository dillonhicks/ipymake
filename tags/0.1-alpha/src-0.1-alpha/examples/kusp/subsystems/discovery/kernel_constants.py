sig2String = {
	# mapping of signal numbers to signal names
	1 : "SIGHUP",
 	2 : "SIGINT",
   	3 : "SIGQUIT",
   	4 : "SIGILL",
	5 : "SIGTRAP",
	6 : "SIGABRT",
	6 : "SIGIOT",
   	7 : "SIGBUS",
  	8 : "SIGFPE",
  	9 : "SIGKILL",
   	10 : "SIGUSR1",
  	11 : "SIGSEGV",
  	12 : "SIGUSR2",
   	13 : "SIGPIPE",
   	14 : "SIGALRM",
   	15 : "SIGTERM",
   	16 : "SIGSTKFLT",
   	17 : "SIGCLD",
   	17 : "SIGCHLD",
   	18 : "SIGCONT",
	19 : "SIGSTOP",
	20 : "SIGTSTP",
   	21 : "SIGTTIN",
   	22 : "SIGTTOU",
   	23 : "SIGURG", 
	24 : "SIGXCPU",
	25 : "SIGXFSZ",      
	26 : "SIGVTALRM",   
   	27 : "SIGPROF",
	28 : "SIGWINCH",

	# Number 29 is also used for SIGPOLL, but we only report SIGIO
	# 29 : "SIGPOLL",
   	29 : "SIGIO",
   	30 : "SIGPWR",
	31 : "SIGSYS",

	# Number 31 is also used for SIGUNUSED, but we only report SIGSYS
	# 31 : "SIGUNUSED"
}

ptraceReq2String = {
	# mapping of ptrace request argument to a string
	0 : "PTRACE_TRACEME",
	1 : "PTRACE_PEEKTEXT",
	2 : "PTRACE_PEEKDATA",
	3 : "PTRACE_PEEKUSR",
	4 : "PTRACE_POKETEXT",
	5 : "PTRACE_POKEDATA",
	6 : "PTRACE_POKEUSR",
	7 : "PTRACE_CONT",
	8 : "PTRACE_KILL",
	9 : "PTRACE_SINGLESTEP",
	12 : "PTRACE_GETREGS",
	13 : "PTRACE_SETREAGS",
	14 : "PTRACE_GETFPREGS",
	15 : "PTRACE_SETFPREGS",
	16 : "PTRACE_ATTACH",
	17 : "PTRACE_DETACH",
	18 : "PTRACE_GETFPXREGS",
	19 : "PTRACE_SETFPXREGS",
	21 : "PTRACE_OLDSETOPTIONS",
	24 : "PTRACE_SYSCALL",
	25 : "PTRACE_GET_THREAD_AREA",
	26 : "PTRACE_SET_THREAD_AREA",
	31 : "PTRACE_SYSEMU",
	32 : "PTRACE_SYSEMU_SINGLESTEP",
	0x4200 : "PTRACE_SETOPTIONS",
	0x4201 : "PTRACE_GETEVENTMSG",
	0x4202 : "PTRACE_GETSIGINFO",
	0x4203 : "PTRACE_SETSIGINFO"
}

# Clone Flags
CSIGNAL              = 0x000000ff	# signal mask to be sent at exit 
CLONE_VM             = 0x00000100	# set if VM shared between processes 
CLONE_FS             = 0x00000200	# set if fs info shared between processes 
CLONE_FILES          = 0x00000400	# set if open files shared between processes 
CLONE_SIGHAND        = 0x00000800	# set if signal handlers and blocked signals shared 
CLONE_PTRACE         = 0x00002000	# set if we want to let tracing continue on the child too 
CLONE_VFORK          = 0x00004000	# set if the parent wants the child to wake it up on mm_release 
CLONE_PARENT         = 0x00008000	# set if we want to have the same parent as the cloner 
CLONE_THREAD         = 0x00010000	# Same thread group? 
CLONE_NEWNS          = 0x00020000	# New namespace group? 
CLONE_SYSVSEM        = 0x00040000	# share system V SEM_UNDO semantics 
CLONE_SETTLS         = 0x00080000	# create a new TLS for the child 
CLONE_PARENT_SETTID  = 0x00100000	# set the TID in the parent 
CLONE_CHILD_CLEARTID = 0x00200000	# clear the TID in the child 
CLONE_DETACHED	     = 0x00400000	# Unused, ignored 
CLONE_UNTRACED	     = 0x00800000	# set if the tracing process can't force CLONE_PTRACE on this clone 
CLONE_CHILD_SETTID   = 0x01000000	# set the TID in the child 
CLONE_STOPPED	     = 0x02000000	# Start in stopped state 
CLONE_NEWUTS	     = 0x04000000	# New utsname group? 
CLONE_NEWIPC	     = 0x08000000	# New ipcs 
CLONE_NEWUSER	     = 0x10000000	# New user namespace 

# Shared Memory Definitions
IPC_PRIVATE 	= 0
IPC_CREAT 	= 00001000
IPC_EXCL 	= 00002000
IPC_NOWAIT 	= 00004000
SHM_RDONLY	= 010000
SHM_RND		= 020000
SHM_REMAP	= 040000
SHM_EXEC	= 0100000
SHM_R		= 0400
SHM_W		= 0200
SHM_LOCK	= 11
SHM_UNLOCK	= 12
SHM_STAT	= 13
SHM_INFO	= 14

DSCVR_NULL_SYSID = "Null File"

shmStringTable = {
	IPC_PRIVATE : "IPC_PRIVATE",
	SHM_LOCK    : "SHM_LOCK",
	SHM_UNLOCK  : "SHM_UNLOCK",
	SHM_STAT    : "SHM_STAT",
	SHM_INFO    : "SHM_INFO",
	IPC_CREAT   : "IPC_CREAT",
	IPC_EXCL    : "IPC_EXCL",
	IPC_NOWAIT  : "IPC_NOWAIT",
	SHM_RDONLY  : "SHM_RDONLY",
	SHM_RND     : "SHM_RND",
	SHM_REMAP   : "SHM_REMAP",
	SHM_EXEC    : "SHM_EXEC",
	SHM_R       : "SHM_R",
	SHM_W       : "SHM_W"
}

# File modes
FMODE_READ   = 1
FMODE_WRITE  = 2
FMODE_LSEEK  = 4
FMODE_PREAD  = 8
FMODE_PWRITE = FMODE_PREAD
FMODE_EXEC   = 16

fileModeStringTable = {
	FMODE_READ   : "READ",
	FMODE_WRITE  : "WRITE",
	FMODE_LSEEK  : "LSEEK",
	FMODE_PREAD  : "PREAD | PWRITE",
	FMODE_EXEC   : "EXEC",
}

AF_UNIX = 1
AF_INET = 2


# Task States
TASK_RUNNING         = 0
TASK_RUNNING_MUTEX   = 1
TASK_INTERRUPTIBLE   = 2
TASK_UNINTERRUPTIBLE = 4
TASK_STOPPED         = 8
TASK_TRACED          = 16
EXIT_ZOMBIE          = 32
EXIT_DEAD            = 64
TASK_NONINTERACTIVE  = 128
TASK_DEAD            = 256

taskStateStringTable = {
	TASK_RUNNING         : "TASK_RUNNING",
	TASK_RUNNING_MUTEX   : "TASK_RUNNING_MUTEX",
	TASK_INTERRUPTIBLE   : "TASK_INTERRUPTIBLE",
	TASK_UNINTERRUPTIBLE : "TASK_UNINTERRUPTIBLE",
	TASK_STOPPED         : "TASK_STOPPED",
	TASK_TRACED          : "TASK_TRACED",
	EXIT_ZOMBIE          : "EXIT_ZOMBIE",
	EXIT_DEAD            : "EXIT_DEAD",
	TASK_NONINTERACTIVE  : "TASK_NONINTERACTIVE",
	TASK_DEAD            : "TASK_DEAD",
}

def stateNum2String(state_num):
	if taskStateStringTable.has_key(state_num):
		return taskStateStringTable[state_num]
	else:
		print "Warning, invalid signum"
		return "INVALID"

def signum2String(signum):
	if sig2String.has_key(signum):
		return sig2String[signum]
	else:
		print "Warning, invalid signum"
		return "INVALID"

def ptraceRequest2String(request):
	if ptraceReq2String.has_key(request):
		return ptraceReq2String[request]
	else:
		print "Warning, invalid ptrace request"
		return "INVALID"

def fileMode2String(mode):
	str = "( "

	if FMODE_READ & mode:
		str += fileModeStringTable[FMODE_READ]
		str += " | "
	if FMODE_WRITE & mode:
		str += fileModeStringTable[FMODE_WRITE]
		str += " | "
	if FMODE_LSEEK & mode:
		str += fileModeStringTable[FMODE_LSEEK]
		str += " | "
	if FMODE_PREAD & mode:
		str += fileModeStringTable[FMODE_PREAD]
		str += " | "
	if FMODE_EXEC & mode:
		str += fileModeStringTable[FMODE_EXEC]
		str += " | "

	if str.endswith("| "):
		str = str[:-2]
	str += ")"
	return str
	
			
def shmgetFlags2String(flag):

	str = ""

	if IPC_CREAT & flag:
		str += shmStringTable[IPC_CREAT]
		str += " | "
	if IPC_EXCL & flag:
		str += shmStringTable[IPC_EXCL]
		str += " | "
	if IPC_NOWAIT & flag:
		str += shmStringTable[IPC_NOWAIT]
		str += " | "
	
	str += "0"

	flag &= ~(IPC_CREAT | IPC_EXCL | IPC_NOWAIT)
	str += "%d" % (flag >> 6)
	flag >>= 3
	str += "%d" % (flag >> 3)
	flag >>= 3
	str += "%d" % (flag)

	return str

def shmatFlags2String(flag):

	str = ""
	hasFlag = False

	if SHM_RDONLY & flag:
		str += shmStringTable[SHM_RDONLY]
		str += " | "
		hasFlag = True
	if SHM_RND & flag:
		str += shmStringTable[SHM_RND]
		str += " | "
		hasFlag = True
	if SHM_REMAP & flag:
		str += shmStringTable[SHM_REMAP]
		str += " | "
		hasFlag = True
	if SHM_EXEC & flag:
		str += shmStringTable[SHM_EXEC]
		hasFlag = True

	if not hasFlag:
		str = "None"

	return str



fctlLocking2String = {
	7: "F_SETLKW",
	6: "F_SETLK",
	4: "F_SETFL",
	0: "F_DUPFD",
	2: "LOCK_EX",
	8: "LOCK_UN",
	1: "LOCK_SH",
	32: "LOCK_MAND"
}
