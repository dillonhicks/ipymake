def pmap(params, names):
	ret = {}
	for i in range(len(names)):
		ret[names[i]] = params[i]
	return ret


def sys_readwrite(data):
	data["params"] = pmap(data["raw_params"], ["fd", "buf_ptr", "count"])
	return data


socketmap = {
	1 : 'sock:sys_socket',
	2 : 'sock:sys_bind',
	3 : 'sock:sys_connect',
	4 : 'sock:sys_listen',
	5 : 'sock:sys_accept',
	6 : 'sock:sys_getsockname',
	7 : 'sock:sys_getpeername',
	8 : 'sock:sys_socketpair',
	9 : 'sock:sys_send',
	10: 'sock:sys_recv',
	11: 'sock:sys_sendto',
	12: 'sock:sys_recvfrom',
	13: 'sock:sys_shutdown',
	14: 'sock:sys_setsockopt',
	15: 'sock:sys_getsockopt',
	16: 'sock:sys_sendmsg',
	17: 'sock:sys_recvmsg'
}
def sys_socketcall(data):
	try:
		data["name"] = socketmap[data["raw_params"][0]]
	except KeyError:
		data["name"] = "sock:unknown"

	return data

# --------- SYSTEM CALLS -----------------

systab = {
	 0: ('sys_restart_syscall', None),
	 1: ('sys_exit', ["error_code"]),
	 2: ('sys_fork', None),
	 3: ('sys_read', sys_readwrite), # as an example
	 4: ('sys_write',  ["fd", "buf_ptr", "count"]),
	 5: ('sys_open', ["filename", "flags", "mode"]),
	 6: ('sys_close', ["fd"]),
	 7: ('sys_waitpid', ["pid", "stat_addr", "options"]),
	 8: ('sys_creat', None),
	 9: ('sys_link', None),
	 10: ('sys_unlink', None),
	 11: ('sys_execve', None),
	 12: ('sys_chdir', None),
	 13: ('sys_time', ["tloc"]),
	 14: ('sys_mknod', None),
	 15: ('sys_chmod', None),
	 16: ('sys_lchown16', None),
	 17: ('sys_ni_syscall', None),
	 18: ('sys_stat', None),
	 19: ('sys_lseek', None),
	 20: ('sys_getpid', None),
	 21: ('sys_mount', None),
	 22: ('sys_oldumount', None),
	 23: ('sys_setuid16', None),
	 24: ('sys_getuid16', None),
	 25: ('sys_stime', None),
	 26: ('sys_ptrace', None),
	 27: ('sys_alarm', None),
	 28: ('sys_fstat', ["fd", "statbuf"]),
	 29: ('sys_pause', None),
	 30: ('sys_utime', None),
	 31: ('sys_ni_syscall', None),
	 32: ('sys_ni_syscall', None),
	 33: ('sys_access', None),
	 34: ('sys_nice', ["increment"]),
	 35: ('sys_ni_syscall', []),
	 36: ('sys_sync', None),
	 37: ('sys_kill', ["pid", "sig"]),
	 38: ('sys_rename', None),
	 39: ('sys_mkdir', None),
	 40: ('sys_rmdir', None),
	 41: ('sys_dup', None),
	 42: ('sys_pipe', None),
	 43: ('sys_times', None),
	 44: ('sys_ni_syscall', None),
	 45: ('sys_brk', ["brk"]),
	 46: ('sys_setgid16', None),
	 47: ('sys_getgid16', None),
	 48: ('sys_signal', None),
	 49: ('sys_geteuid16', None),
	 50: ('sys_getegid16', None),
	 51: ('sys_acct', None),
	 52: ('sys_umount', None),
	 53: ('sys_ni_syscall', None),
	 54: ('sys_ioctl', None),
	 55: ('sys_fcntl', None),
	 56: ('sys_ni_syscall', None),
	 57: ('sys_setpgid', None),
	 58: ('sys_ni_syscall', None),
	 59: ('sys_olduname', None),
	 60: ('sys_umask', None),
	 61: ('sys_chroot', None),
	 62: ('sys_ustat', None),
	 63: ('sys_dup2', None),
	 64: ('sys_getppid', None),
	 65: ('sys_getpgrp', None),
	 66: ('sys_setsid', None),
	 67: ('sys_sigaction', None),
	 68: ('sys_sgetmask', None),
	 69: ('sys_ssetmask', None),
	 70: ('sys_setreuid16', None),
	 71: ('sys_setregid16', None),
	 72: ('sys_sigsuspend', None),
	 73: ('sys_sigpending', None),
	 74: ('sys_sethostname', None),
	 75: ('sys_setrlimit', None),
	 76: ('sys_old_getrlimit', None),
	 77: ('sys_getrusage', None),
	 78: ('sys_gettimeofday', None),
	 79: ('sys_settimeofday', None),
	 80: ('sys_getgroups16', None),
	 81: ('sys_setgroups16', None),
	 82: ('old_select', None),
	 83: ('sys_symlink', None),
	 84: ('sys_lstat', None),
	 85: ('sys_readlink', None),
	 86: ('sys_uselib', None),
	 87: ('sys_swapon', None),
	 88: ('sys_reboot', None),
	 89: ('old_readdir', None),
	 90: ('old_mmap', None),
	 91: ('sys_munmap', None),
	 92: ('sys_truncate', None),
	 93: ('sys_ftruncate', None),
	 94: ('sys_fchmod', None),
	 95: ('sys_fchown16', None),
	 96: ('sys_getpriority', None),
	 97: ('sys_setpriority', None),
	 98: ('sys_ni_syscall', None),
	 99: ('sys_statfs', None),
	 100: ('sys_fstatfs', None),
	 101: ('sys_ioperm', None),
	 102: ('sys_socketcall', sys_socketcall),
	 103: ('sys_syslog', None),
	 104: ('sys_setitimer', None),
	 105: ('sys_getitimer', None),
	 106: ('sys_newstat', None),
	 107: ('sys_newlstat', None),
	 108: ('sys_newfstat', None),
	 109: ('sys_uname', None),
	 110: ('sys_iopl', None),
	 111: ('sys_vhangup', None),
	 112: ('sys_ni_syscall', None),
	 113: ('sys_vm86old', None),
	 114: ('sys_wait4', None),
	 115: ('sys_swapoff', None),
	 116: ('sys_sysinfo', None),
	 117: ('sys_ipc', None),
	 118: ('sys_fsync', None),
	 119: ('sys_sigreturn', None),
	 120: ('sys_clone', None),
	 121: ('sys_setdomainname', None),
	 122: ('sys_newuname', None),
	 123: ('sys_modify_ldt', None),
	 124: ('sys_adjtimex', None),
	 125: ('sys_mprotect', None),
	 126: ('sys_sigprocmask', None),
	 127: ('sys_ni_syscall', None),
	 128: ('sys_init_module', None),
	 129: ('sys_delete_module', None),
	 130: ('sys_ni_syscall', None),
	 131: ('sys_quotactl', None),
	 132: ('sys_getpgid', None),
	 133: ('sys_fchdir', None),
	 134: ('sys_bdflush', None),
	 135: ('sys_sysfs', None),
	 136: ('sys_personality', None),
	 137: ('sys_ni_syscall', None),
	 138: ('sys_setfsuid16', None),
	 139: ('sys_setfsgid16', None),
	 140: ('sys_llseek', None),
	 141: ('sys_getdents', None),
	 142: ('sys_select', None),
	 143: ('sys_flock', None),
	 144: ('sys_msync', None),
	 145: ('sys_readv', None),
	 146: ('sys_writev', None),
	 147: ('sys_getsid', None),
	 148: ('sys_fdatasync', None),
	 149: ('sys_sysctl', None),
	 150: ('sys_mlock', None),
	 151: ('sys_munlock', None),
	 152: ('sys_mlockall', None),
	 153: ('sys_munlockall', None),
	 154: ('sys_sched_setparam', None),
	 155: ('sys_sched_getparam', None),
	 156: ('sys_sched_setscheduler', None),
	 157: ('sys_sched_getscheduler', None),
	 158: ('sys_sched_yield', None),
	 159: ('sys_sched_get_priority_max', None),
	 160: ('sys_sched_get_priority_min', None),
	 161: ('sys_sched_rr_get_interval', None),
	 162: ('sys_nanosleep', None),
	 163: ('sys_mremap', None),
	 164: ('sys_setresuid16', None),
	 165: ('sys_getresuid16', None),
	 166: ('sys_vm86', None),
	 167: ('sys_ni_syscall', None),
	 168: ('sys_poll', None),
	 169: ('sys_nfsservctl', None),
	 170: ('sys_setresgid16', None),
	 171: ('sys_getresgid16', None),
	 172: ('sys_prctl', None),
	 173: ('sys_rt_sigreturn', None),
	 174: ('sys_rt_sigaction', None),
	 175: ('sys_rt_sigprocmask', None),
	 176: ('sys_rt_sigpending', None),
	 177: ('sys_rt_sigtimedwait', None),
	 178: ('sys_rt_sigqueueinfo', None),
	 179: ('sys_rt_sigsuspend', None),
	 180: ('sys_pread64', None),
	 181: ('sys_pwrite64', None),
	 182: ('sys_chown16', None),
	 183: ('sys_getcwd', None),
	 184: ('sys_capget', None),
	 185: ('sys_capset', None),
	 186: ('sys_sigaltstack', None),
	 187: ('sys_sendfile', None),
	 188: ('sys_ni_syscall', None),
	 189: ('sys_ni_syscall', None),
	 190: ('sys_vfork', None),
	 191: ('sys_getrlimit', None),
	 192: ('sys_mmap2', None),
	 193: ('sys_truncate64', None),
	 194: ('sys_ftruncate64', None),
	 195: ('sys_stat64', None),
	 196: ('sys_lstat64', None),
	 197: ('sys_fstat64', ["fd", "statbuf"]),
	 198: ('sys_lchown', None),
	 199: ('sys_getuid', None),
	 200: ('sys_getgid', None),
	 201: ('sys_geteuid', None),
	 202: ('sys_getegid', None),
	 203: ('sys_setreuid', None),
	 204: ('sys_setregid', None),
	 205: ('sys_getgroups', None),
	 206: ('sys_setgroups', None),
	 207: ('sys_fchown', None),
	 208: ('sys_setresuid', None),
	 209: ('sys_getresuid', None),
	 210: ('sys_setresgid', None),
	 211: ('sys_getresgid', None),
	 212: ('sys_chown', None),
	 213: ('sys_setuid', None),
	 214: ('sys_setgid', None),
	 215: ('sys_setfsuid', None),
	 216: ('sys_setfsgid', None),
	 217: ('sys_pivot_root', None),
	 218: ('sys_mincore', None),
	 219: ('sys_madvise', None),
	 220: ('sys_getdents64', None),
	 221: ('sys_fcntl64', None),
	 222: ('sys_ni_syscall', None),
	 223: ('sys_ni_syscall', None),
	 224: ('sys_gettid', None),
	 225: ('sys_readahead', None),
	 226: ('sys_setxattr', None),
	 227: ('sys_lsetxattr', None),
	 228: ('sys_fsetxattr', None),
	 229: ('sys_getxattr', None),
	 230: ('sys_lgetxattr', None),
	 231: ('sys_fgetxattr', None),
	 232: ('sys_listxattr', None),
	 233: ('sys_llistxattr', None),
	 234: ('sys_flistxattr', None),
	 235: ('sys_removexattr', None),
	 236: ('sys_lremovexattr', None),
	 237: ('sys_fremovexattr', None),
	 238: ('sys_tkill', None),
	 239: ('sys_sendfile64', None),
	 240: ('sys_futex', None),
	 241: ('sys_sched_setaffinity', None),
	 242: ('sys_sched_getaffinity', None),
	 243: ('sys_set_thread_area', None),
	 244: ('sys_get_thread_area', None),
	 245: ('sys_io_setup', None),
	 246: ('sys_io_destroy', None),
	 247: ('sys_io_getevents', None),
	 248: ('sys_io_submit', None),
	 249: ('sys_io_cancel', None),
	 250: ('sys_fadvise64', None),
	 251: ('sys_ni_syscall', None),
	 252: ('sys_exit_group', None),
	 253: ('sys_lookup_dcookie', None),
	 254: ('sys_epoll_create', None),
	 255: ('sys_epoll_ctl', None),
	 256: ('sys_epoll_wait', None),
	 257: ('sys_remap_file_pages', None),
	 258: ('sys_set_tid_address', None),
	 259: ('sys_timer_create', None),
	 260: ('sys_timer_settime', None),
	 261: ('sys_timer_gettime', None),
	 262: ('sys_timer_getoverrun', None),
	 263: ('sys_timer_delete', None),
	 264: ('sys_clock_settime', None),
	 265: ('sys_clock_gettime', None),
	 266: ('sys_clock_getres', None),
	 267: ('sys_clock_nanosleep', None),
	 268: ('sys_statfs64', None),
	 269: ('sys_fstatfs64', None),
	 270: ('sys_tgkill', None),
	 271: ('sys_utimes', None),
	 272: ('sys_fadvise64_64', None),
	 273: ('sys_ni_syscall', None),
	 274: ('sys_mbind', None),
	 275: ('sys_get_mempolicy', None),
	 276: ('sys_set_mempolicy', None),
	 277: ('sys_mq_open', None),
	 278: ('sys_mq_unlink', None),
	 279: ('sys_mq_timedsend', None),
	 280: ('sys_mq_timedreceive', None),
	 281: ('sys_mq_notify', None),
	 282: ('sys_mq_getsetattr', None),
	 283: ('sys_kexec_load', None),
	 284: ('sys_waitid', None),
	 285: ('sys_ni_syscall', None),
	 286: ('sys_add_key', None),
	 287: ('sys_request_key', None),
	 288: ('sys_keyctl', None),
	 289: ('sys_ioprio_set', None),
	 290: ('sys_ioprio_get', None),
	 291: ('sys_inotify_init', None),
	 292: ('sys_inotify_add_watch', None),
	 293: ('sys_inotify_rm_watch', None),
	 294: ('sys_migrate_pages', None),
	 295: ('sys_openat', None),
	 296: ('sys_mkdirat', None),
	 297: ('sys_mknodat', None),
	 298: ('sys_fchownat', None),
	 299: ('sys_futimesat', None),
	 300: ('sys_fstatat64', None),
	 301: ('sys_unlinkat', None),
	 302: ('sys_renameat', None),
	 303: ('sys_linkat', None),
	 304: ('sys_symlinkat', None),
	 305: ('sys_readlinkat', None),
	 306: ('sys_fchmodat', None),
	 307: ('sys_faccessat', None),
	 308: ('sys_pselect6', None),
	 309: ('sys_ppoll', None),
	 310: ('sys_unshare', None),
	 311: ('sys_set_robust_list', None),
	 312: ('sys_get_robust_list', None),
	 313: ('sys_splice', None),
	 314: ('sys_sync_file_range', None),
	 315: ('sys_tee', None),
	 316: ('sys_vmsplice', None),
	 317: ('sys_move_pages', None),
	 318: ('sys_getcpu', None),
	 319: ('sys_epoll_pwait', None)
}
