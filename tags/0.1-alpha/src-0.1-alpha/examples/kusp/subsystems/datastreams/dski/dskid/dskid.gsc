#!pykusp.parsers.group_sched_parser
computation 'dfl_thread' {
	'comment' =  ''
	'commend' =  'Direct Logging Thread'
	'joiner_type' =  'process'
}
computation 'kdsd_mgnt' {
	'comment' =  'Buffer Management Kernel Thread'
	'joiner_type' =  'process'
}
computation 'dski_daemon' {
	'comment' =  'Userspace DSKI Daemon'
	'joiner_type' = 'process'
}

sdf 'DSKI BMKT SDF' {
	'comment' =  'dski_bmkt_sdf_abi.h'
	'group' =  <>
	'member' = <>
}
group 'direct_file_kernel_threads' {
	'comment' =  ''
	'sdf' =  sdf('DSKI BMKT SDF') {}
	'members' =  [
		computation('kdsd_mgnt') {}
		computation('dfl_thread') {}
		computation('dski_daemon') {}
	]
}
