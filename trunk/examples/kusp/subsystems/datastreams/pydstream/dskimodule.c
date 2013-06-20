#define KUSP_DEBUG

#include <Python.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <dski.h>
#include <sys/poll.h>
#include <pthread.h>
#include <signal.h>
#include <string.h>
#include <stdlib.h>

#include <kusp_common.h>
#include <mutex.h>


struct reader_thread_data {
	int relay_file;
	int output_file;
	int produced_file;
	int consumed_file;

	char *relay_buffer;
	pthread_t thread;
	pthread_mutex_t mutex;

	size_t n_subbufs;
	size_t subbuf_size;

	size_t produced;
	size_t consumed;
	size_t max_backlog;

	int cpu;
};

static int process_subbufs(struct reader_thread_data *self)
{
	size_t i, start_subbuf, end_subbuf, subbuf_idx, subbufs_consumed = 0;
	size_t subbufs_ready = self->produced - self->consumed;
	char *subbuf_ptr;
	unsigned padding;
	int len;


	start_subbuf = self->consumed % self->n_subbufs;
	end_subbuf = start_subbuf + subbufs_ready;
	for (i = start_subbuf; i < end_subbuf; i++) {
		subbuf_idx = i % self->n_subbufs;
		subbuf_ptr = self->relay_buffer + subbuf_idx * self->subbuf_size;
		padding = *((unsigned *)subbuf_ptr);


		subbuf_ptr += sizeof(padding);
		len = (self->subbuf_size - sizeof(padding)) - padding;


		if (write(self->output_file, subbuf_ptr, len) < 0) {
			eprintf("Couldn't write to output file for cpu %d,"
					"exiting: errcode = %d: %s\n",
					self->cpu, errno, strerror(errno));
			exit(1);
		}
		subbufs_consumed++;
	}

	return subbufs_consumed;
}

static void check_buffer(struct reader_thread_data *self)
{
	size_t subbufs_consumed;

	lseek(self->produced_file, 0, SEEK_SET);
	if (read(self->produced_file, &self->produced,
		 sizeof(self->produced)) < 0) {
		eprintf("Couldn't read from produced file for cpu %d, "
				"exiting: errcode = %d: %s\n", self->cpu,
				errno, strerror(errno));
		exit(1);
	}

	subbufs_consumed = process_subbufs(self);
	if (subbufs_consumed) {
		if (subbufs_consumed == self->n_subbufs)
			eprintf("cpu %d buffer full. "
					"Consider using a larger buffer size.\n",
					self->cpu);
		if (subbufs_consumed > self->max_backlog) {
			self->max_backlog = subbufs_consumed;
		}
		self->consumed += subbufs_consumed;

		if (write(self->consumed_file, &subbufs_consumed,
			  sizeof(subbufs_consumed)) < 0) {
			eprintf("Couldn't write to consumed file for cpu %d, "
					"exiting: errcode = %d: %s\n",
					self->cpu, errno, strerror(errno));
			exit(1);
		}
	}
}


static struct reader_thread_data *reader_thread_create(
		int relay_file, int output_file,
		int produced_file, int consumed_file, size_t n_subbufs,
		size_t subbuf_size, int cpu)
{
	struct reader_thread_data *self;
	size_t total_bufsize;

	self = malloc(sizeof(*self));
	memset(self, 0, sizeof(*self));

	self->relay_file = relay_file;
	self->output_file = output_file;
	self->produced_file = produced_file;
	self->consumed_file = consumed_file;
	self->n_subbufs = n_subbufs;
	self->subbuf_size = subbuf_size;
	self->cpu = cpu;
	km_mutex_init(&self->mutex, NULL);


	total_bufsize = self->subbuf_size * self->n_subbufs;

	self->relay_buffer = mmap(NULL, total_bufsize, PROT_READ,
			MAP_PRIVATE | MAP_POPULATE, self->relay_file, 0);

	if (self->relay_buffer == MAP_FAILED) {
		eprintf("Couldn't mmap relay file, total_bufsize (%d) "
			" = subbuf_size (%d) * n_subbufs(%d), error = %s \n",
			total_bufsize, subbuf_size, n_subbufs, strerror(errno));

		close(relay_file);
		close(output_file);
		return NULL;
	}

	dprintf("Created reader thread for cpu %d\n", self->cpu);

	return self;
}

static void reader_thread_destroy(void *ptr)
{
	struct reader_thread_data *self = (struct reader_thread_data *)ptr;
	dprintf("Destroying reader thread for cpu %d\n", self->cpu);

	size_t total_bufsize = self->subbuf_size * self->n_subbufs;

	km_mutex_lock(&self->mutex);

	pthread_cancel(self->thread);

	check_buffer(self);

	munmap(self->relay_buffer, total_bufsize);

	free(self);
}


static int file_conv(PyObject *object, int *fdp)
{
	int fd = PyObject_AsFileDescriptor(object);

	if (fd < 0)
		return 0;

	*fdp = fd;
	return 1;
}


static PyObject *
dski_reader_thread_create(PyObject *self, PyObject *args)
{
	int relay_file, output_file, produced_file, consumed_file = 0;
	int n_subbufs, subbuf_size, cpu = 0;
	void *obj;

	if (!PyArg_ParseTuple(args, "O&O&O&O&iii",
			file_conv, &relay_file, file_conv, &output_file,
			file_conv, &produced_file, file_conv, &consumed_file,
			&n_subbufs, &subbuf_size, &cpu)) {
		return NULL;
	}

	obj = reader_thread_create(relay_file, output_file, produced_file,
			consumed_file, n_subbufs, subbuf_size, cpu);

	return PyCObject_FromVoidPtr(obj, NULL);

}


void *reader_thread(void *p)
{
	struct reader_thread_data *self = (struct reader_thread_data*)p;

	int rc;
	struct pollfd pollfd;

	/*
	 * since this is a thread in the Python interpretor's address space, it
	 * may receive signals. if Python code is waiting on signals, then it
	 * will receive them non-deterministically, as this thread may be the
	 * lucky recepient, in which case, python cannot notify any 'python
	 * code' waiting on a signal.
	 */
	sigset_t sigs;

	sigfillset(&sigs);

	if (pthread_sigmask(SIG_BLOCK, &sigs, NULL)) {
		fprintf(stderr, "reader thread pthread_sigmask failed: %s\n",
				strerror(errno));
	}

	do {
		pollfd.fd = self->relay_file;
		pollfd.events = POLLIN;
		rc = poll(&pollfd, 1, -1);
		if (rc < 0) {
			if (errno != EINTR) {
				eprintf("poll error: %s\n",strerror(errno));
				return NULL;
			}
			eprintf("poll warning: %s\n",strerror(errno));
			rc = 0;
		}

		km_mutex_lock(&self->mutex);
		//pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, NULL);
		check_buffer(self);
		//pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
		km_mutex_unlock(&self->mutex);

	} while (1);
}


static PyObject*
dski_reader_thread_run(PyObject *s, PyObject *args)
{

	PyObject *obj;

	if (!PyArg_ParseTuple(args, "O", &obj)) {
		return NULL;
	}

	struct reader_thread_data *self = (struct reader_thread_data*)PyCObject_AsVoidPtr(obj);

	pthread_create(&self->thread, NULL, reader_thread, self);

	return Py_None;
}

static PyObject *
dski_reader_thread_kill(PyObject *self, PyObject *args)
{
	PyObject *obj;

	if (!PyArg_ParseTuple(args, "O", &obj)) {
		return NULL;
	}

	reader_thread_destroy(PyCObject_AsVoidPtr(obj));

	return Py_None;

}


static PyObject *
dski_apply_task_filter(PyObject *self, PyObject *args){
	int fd, ret, resp;
	long pid;
	const char *dstrm;
	char *ccsm_set_name;
	struct dski_ioc_filter_ctrl fctrl;

	ccsm_set_name = malloc(sizeof(*ccsm_set_name) * NAME_MAX+1);
	if(!ccsm_set_name)
			return PyErr_NoMemory();

	if(!PyArg_ParseTuple(args, "O&slsi",file_conv, &fd, &dstrm, &pid, &ccsm_set_name, &resp))
		return NULL;

	strcpy(fctrl.datastream, dstrm);
	fctrl.params.task_filter.set_name = ccsm_set_name;
	fctrl.params.task_filter.pid = pid;
	fctrl.params.task_filter.match_response = resp;
	strcpy(fctrl.filtername, FLTR_TASK);

	ret = ioctl(fd, DSKI_FILTER_APPLY, &fctrl);
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject *
dski_apply_pid_filter(PyObject *self, PyObject *args)
{
	int fd, ret;
	const char *dstrm;
	PyObject *pidslist, *pid;
	Py_ssize_t size, i;
	struct dski_ioc_filter_ctrl fctrl;
	struct dski_pid_filter_elem *pids;
	int resp;
	char *name;

	if (!PyArg_ParseTuple(args, "O&sO!i", file_conv, &fd, &dstrm,
				&PyList_Type, &pidslist, &resp))
		return NULL;

	size = PyList_Size(pidslist);
	pids = malloc(sizeof(*pids)*size);
	if (!pids)
		return PyErr_NoMemory();

	for (i = 0; i < size; i++) {

		PyObject *pidtpl = PyList_GetItem(pidslist, i);

		pid = PyTuple_GetItem(pidtpl, 0);

		pids[i].match_response = PyInt_AsLong(PyTuple_GetItem(pidtpl, 1));
		pids[i].name[0] = '\0';
		pids[i].pid = 0;

		if (PyInt_Check(pid)) {
			pids[i].pid = PyInt_AsLong(pid);

			if (pids[i].pid == -1 && PyErr_Occurred()) {
				free(pids);
				return NULL;
			}
		} else if (PyString_Check(pid)) {
			if (PyString_Size(pid) > NAME_MAX) {
				free(pids);
				PyErr_SetString(PyExc_TypeError, "pid string too long");
				return NULL;
			}

			name = PyString_AsString(pid);
			if (!name) {
				free(pids);
				return NULL;
			}

			strcpy(pids[i].name, name);

		} else {
			free(pids);
			PyErr_SetString(PyExc_TypeError, "pids must be ints or strings");
			return NULL;
		}
	}


	strcpy(fctrl.datastream, dstrm);
	fctrl.params.pidfilter.pid_array_size = sizeof(*pids)*size;
	fctrl.params.pidfilter.pids = pids;
	fctrl.params.pidfilter.default_response = resp;
	strcpy(fctrl.filtername, FLTR_PID);

	ret = ioctl(fd, DSKI_FILTER_APPLY, &fctrl);
	if (ret < 0) {
		free(pids);
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	free(pids);

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject *
dski_ips_query_internal(int fd)
{
	struct dski_ioc_datastream_ip_info *info;
	struct dski_ioc_datastream_ip_ctrl ctrl;
	int ret, cnt, i;
	PyObject *list, *tuple;
	size_t size;

	size = 1024;
again:
	ctrl.size = size;
	ctrl.info = malloc(ctrl.size);
	if (!ctrl.info)
		return PyErr_NoMemory();

 	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_IPS_QUERY, &ctrl);
 	Py_END_ALLOW_THREADS
 	if (ret < 0) {
 		PyErr_SetFromErrno(PyExc_IOError);
		free(ctrl.info);
 		return NULL;
 	}

	if (ctrl.size > size) {
		size = ctrl.size;
		free(ctrl.info);
		goto again;
	}

	if (ctrl.size == 0) {
		free(ctrl.info);
		return Py_BuildValue("[]");
	}

	cnt = ctrl.size / sizeof(*info);
	info = ctrl.info;

	list = PyList_New(0);
	if (!list) {
		free(ctrl.info);
 		return NULL;
 	}

	for (i = 0; i < cnt; i++) {
		tuple = PyTuple_New(6);
		PyTuple_SetItem(tuple, 0, PyString_FromString(info[i].group));
		PyTuple_SetItem(tuple, 1, PyString_FromString(info[i].name));
		PyTuple_SetItem(tuple, 2, PyString_FromString(info[i].edf));
		PyTuple_SetItem(tuple, 3, PyInt_FromLong(info[i].type));
		PyTuple_SetItem(tuple, 4, PyLong_FromLongLong((long long)info[i].id));
		PyTuple_SetItem(tuple, 5, PyString_FromString(info[i].desc));
		PyList_Append(list, tuple);
	}

	free(info);
	return list;
}

static PyObject *
dski_ips_query(PyObject *self, PyObject *args)
{
	int fd;

 	if (!PyArg_ParseTuple(args, "O&", file_conv, &fd))
 		return NULL;

	return dski_ips_query_internal(fd);
}

static PyObject *
dski_apply_strace_filter(PyObject *self, PyObject *args)
{
	int fd, ret;
	const char *dstrm;
	struct dski_ioc_filter_ctrl fctrl;
	char *ta_name;

	ta_name = malloc(sizeof(*ta_name) * NAME_MAX+1);
	if(!ta_name)
		return PyErr_NoMemory();

	if (!PyArg_ParseTuple(args, "O&ss", file_conv, &fd, &dstrm,&ta_name))
		return NULL;

	printf("fd:%d, ta_name: %s\n", fd, ta_name);

	strcpy(fctrl.datastream, dstrm);
	fctrl.params.dscvr_filter.name = ta_name;
	strcpy(fctrl.filtername, FLTR_CCSM_STRACE);
	ret = ioctl(fd, DSKI_FILTER_APPLY, &fctrl);
	if (ret < 0) {
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_apply_discovery_filter(PyObject *self, PyObject *args)
{
	int fd, ret;
	const char *dstrm;
	struct dski_ioc_filter_ctrl fctrl;
	char *ta_name;

	ta_name = malloc(sizeof(*ta_name) * NAME_MAX+1);
	if(!ta_name)
		return PyErr_NoMemory();

	if (!PyArg_ParseTuple(args, "O&ss", file_conv, &fd, &dstrm,&ta_name))
		return NULL;

	printf("fd:%d, ta_name: %s\n", fd, ta_name);

	strcpy(fctrl.datastream, dstrm);
	fctrl.params.dscvr_filter.name = ta_name;
	strcpy(fctrl.filtername, FLTR_CCSM_TRACEME);
	ret = ioctl(fd, DSKI_FILTER_APPLY, &fctrl);
	if (ret < 0) {
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

// Passing information to the systemMonitor Active filter.
static PyObject *
dski_apply_systemMonitor_filter(PyObject *self, PyObject *args)
{
	int fd, ret, sysNum, userid;
	const char *dstrm;
	PyObject *list, *sysLst;
	PyObject *pystr, *pyint;
	Py_ssize_t i, listsize, sysLstSize;
	struct dski_ioc_filter_ctrl fctrl;
	struct dski_monitor_list *lis, *tempList, *tmpLis;
	struct dski_monitor_sysList *tempSys, *sys, *tmpSys;
	char  *names, *procfile_name;

	procfile_name = malloc(sizeof(*procfile_name) * NAME_MAX+1);
	if(!procfile_name)
		return PyErr_NoMemory();

	if (!PyArg_ParseTuple(args, "O&ssO!O!i", file_conv, &fd, &dstrm,
				&procfile_name, &PyList_Type, &list, &PyList_Type, &sysLst, &userid))
		return NULL;

	// start parsing the shared libraries list
	listsize=PyList_Size(list);
	lis = NULL;

	for (i =0; i<listsize;i++){
		pystr = PyList_GetItem(list, i);
		if (PyString_Check(pystr)) {
			tmpLis = malloc(sizeof(*lis));
			if (!tmpLis){
				printf("No Memory\n");
				return NULL;
			}

			names =	PyString_AsString(pystr);
			strcpy(tmpLis->shLibName, names);
			tmpLis->next = NULL;

			if (lis == NULL){
				lis = tmpLis;
			}else {
				for (tempList = lis; tempList->next != NULL; tempList=tempList->next){
					continue;
				}
				tempList->next = tmpLis;
			}
		} else {
			PyErr_SetString(PyExc_TypeError, "dskimodule: shared library names must be strings");
			return NULL;
		}
	}

	// start parsing the system calls list.
	sysLstSize=PyList_Size(sysLst);
	sys = NULL;

	for (i=0;i<sysLstSize;i++){
		pyint = PyList_GetItem(sysLst, i);
		if (PyInt_Check(pyint)){
			tempSys = malloc(sizeof(*sys));
			if(!tempSys){
				printf("No Memory\n");
				return NULL;
			}
		sysNum = PyInt_AsLong(pyint);
		tempSys->num = sysNum;
		tempSys->next = NULL;

		if (sys == NULL){
			sys = tempSys;
		} else {
			for (tmpSys = sys;tmpSys->next !=NULL;tmpSys = tmpSys->next){
				continue;
			}
			tmpSys->next = tempSys;
		}
	    } else {
		PyErr_SetString(PyExc_TypeError, "dskimodule: system calls must be numbers");
		return NULL;
	    }
	}

	strcpy(fctrl.datastream, dstrm);
	fctrl.params.smon_filter.lists = lis;
	fctrl.params.smon_filter.sysLs = sys;
	fctrl.params.smon_filter.procfile_name = procfile_name;
	fctrl.params.smon_filter.userid = userid;
	strcpy(fctrl.filtername, FLTR_SMONITOR);

	ret = ioctl(fd, DSKI_FILTER_APPLY, &fctrl);
	if (ret < 0) {
		for (tempList = lis; tempList !=NULL;) {
			tmpLis = tempList;
			tempList = tempList->next;
			free(tmpLis);
		}

		for (tmpSys = sys; tmpSys !=NULL;){
			tempSys = tmpSys;
			tmpSys = tmpSys->next;
			free(tempSys);
		}

		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	for (tempList = lis; tempList !=NULL;) {
		tmpLis = tempList;
		tempList = tempList->next;
		free(tmpLis);
	}

	for (tmpSys = sys; tmpSys !=NULL;){
		tempSys = tmpSys;
		tmpSys = tmpSys->next;
		free(tempSys);
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_relay_dir(PyObject *self, PyObject *args)
{
	int fd, ret;
	char name[NAME_MAX+1];

 	if (!PyArg_ParseTuple(args, "O&", file_conv, &fd))
 		return NULL;

	memset(name, 0, sizeof(name));
	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_RELAY_DIR, name);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	return PyString_FromString(name);
}

static PyObject *
dski_datastream_create(PyObject *self, PyObject *args)
{
	struct dski_ioc_datastream_ctrl dctrl;
	const char *name;
	int fd, ret;

	if (!PyArg_ParseTuple(args, "O&s", file_conv, &fd, &name))
		return NULL;

	strncpy(dctrl.name, name, DS_STR_LEN);

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_DS_CREATE, &dctrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_datastream_enable(PyObject *self, PyObject *args)
{
	struct dski_ioc_datastream_ctrl dctrl;
	const char *name;
	int fd, ret;

	if (!PyArg_ParseTuple(args, "O&s", file_conv, &fd, &name))
		return NULL;

	strncpy(dctrl.name, name, DS_STR_LEN);

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_DS_ENABLE, &dctrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_datastream_disable(PyObject *self, PyObject *args)
{
	struct dski_ioc_datastream_ctrl dctrl;
	const char *name;
	int fd, ret;

	if (!PyArg_ParseTuple(args, "O&s", file_conv, &fd, &name))
		return NULL;

	strncpy(dctrl.name, name, DS_STR_LEN);

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_DS_DISABLE, &dctrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_datastream_assign_chan(PyObject *self, PyObject *args)
{
	struct dski_ioc_datastream_ctrl dctrl;
	const char *name;
	int fd, channel_id, ret;

	if (!PyArg_ParseTuple(args, "O&si", file_conv, &fd, &name, &channel_id))
		return NULL;

	strncpy(dctrl.name, name, DS_STR_LEN);
	dctrl.channel_id = channel_id;

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_DS_ASSIGN_CHAN, &dctrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_datastream_destroy(PyObject *self, PyObject *args)
{
	struct dski_ioc_datastream_ctrl dctrl;
	const char *name;
	int fd, ret;

	if (!PyArg_ParseTuple(args, "O&s", file_conv, &fd, &name))
		return NULL;

	strncpy(dctrl.name, name, DS_STR_LEN);



	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_DS_DESTROY, &dctrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_channel_open(PyObject *self, PyObject *args)
{
	struct dski_ioc_channel_ctrl chan_ctrl;
	unsigned int subbuf_size, num_subbufs;
	int fd, ret, timeout = 0;
	unsigned int flags;

	if (!PyArg_ParseTuple(args, "O&III|I", file_conv, &fd,
				&subbuf_size, &num_subbufs, &flags, &timeout))
		return NULL;

	chan_ctrl.subbuf_size = subbuf_size;
	chan_ctrl.num_subbufs = num_subbufs;
	chan_ctrl.timeout = timeout;
	chan_ctrl.flags = flags;

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_CHANNEL_OPEN, &chan_ctrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	return PyInt_FromLong(ret);
}

static PyObject *
dski_channel_close(PyObject *self, PyObject *args)
{
	struct dski_ioc_channel_ctrl chan_ctrl;
	int fd, ret, channel_id;

	if (!PyArg_ParseTuple(args, "O&i", file_conv, &fd, &channel_id))
		return NULL;

	chan_ctrl.channel_id = channel_id;

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_CHANNEL_CLOSE, &chan_ctrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_channel_flush(PyObject *self, PyObject *args)
{
	struct dski_ioc_channel_ctrl chan_ctrl;
	int fd, ret, channel_id;

	if (!PyArg_ParseTuple(args, "O&i", file_conv, &fd, &channel_id))
		return NULL;

	chan_ctrl.channel_id = channel_id;

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_CHANNEL_FLUSH, &chan_ctrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_entity_enable(PyObject *self, PyObject *args)
{
	struct dski_ioc_entity_ctrl ectrl;
	const char *dstrm;
	int fd, ret;
	long long id;

	if (!PyArg_ParseTuple(args, "O&sL", file_conv, &fd, &dstrm, &id))
		return NULL;

	strncpy(ectrl.datastream, dstrm, DS_STR_LEN);
	ectrl.id = (unsigned int)id;
	ectrl.config_info = NULL;
	ectrl.flags = ENTITY_ENABLE;

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_ENTITY_CONFIGURE, &ectrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
dski_histogram_enable(PyObject *self, PyObject *args)
{
	struct dski_ioc_entity_ctrl ectrl;
	union ds_entity_info einfo;
	const char *dstrm;
	int fd, ret;
	unsigned int buckets, tune_amount;
	long long id, min, max;

	if (!PyArg_ParseTuple(args, "O&sLLLII", file_conv, &fd, &dstrm, &id,
				&min, &max, &buckets, &tune_amount))
		return NULL;

	strncpy(ectrl.datastream, dstrm, DS_STR_LEN);
	ectrl.id = (unsigned int)id;
	einfo.hist_info.lowerbound = min;
	einfo.hist_info.upperbound = max;
	einfo.hist_info.buckets = buckets;
	einfo.hist_info.tune_amount = tune_amount;
	ectrl.config_info = &einfo;
	ectrl.flags = ENTITY_ENABLE;

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_ENTITY_CONFIGURE, &ectrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject *
dski_entity_disable(PyObject *self, PyObject *args)
{
	struct dski_ioc_entity_ctrl ectrl;
	const char *dstrm;
	int fd, ret;
	long long id;

	if (!PyArg_ParseTuple(args, "O&sL", file_conv, &fd, &dstrm, &id))
		return NULL;

	strncpy(ectrl.datastream, dstrm, DS_STR_LEN);
	ectrl.id = (unsigned int)id;
	ectrl.flags = ENTITY_DISABLE;

	Py_BEGIN_ALLOW_THREADS
	ret = ioctl(fd, DSKI_ENTITY_CONFIGURE, &ectrl);
	Py_END_ALLOW_THREADS
	if (ret < 0) {
		PyErr_SetFromErrno(PyExc_IOError);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef DSKIMethods[] = {
	{"ips_query", dski_ips_query, METH_VARARGS, "ips query"},
	{"relay_dir", dski_relay_dir, METH_VARARGS, "relay dir"},
	{"apply_pid_filter", dski_apply_pid_filter, METH_VARARGS, "pid filter"},

	{"apply_discovery_filter", dski_apply_discovery_filter, METH_VARARGS,
		"discovery filter"},
	
	{"apply_strace_filter", dski_apply_strace_filter, METH_VARARGS,
		"strace filter"},

	{"apply_systemMonitor_filter", dski_apply_systemMonitor_filter, METH_VARARGS,
		"System Monitor filter"},

	{"apply_task_filter", dski_apply_task_filter, METH_VARARGS,
		"CCSM based Per Task Filter"},

	{"datastream_create", dski_datastream_create, METH_VARARGS,
		"create a named datastream"},

	{"datastream_enable", dski_datastream_enable, METH_VARARGS,
		"enable an existing datastream"},

	{"datastream_disable", dski_datastream_disable, METH_VARARGS,
		"disable an existing datastream"},

	{"assign_channel", dski_datastream_assign_chan, METH_VARARGS,
		"assign a channel to a datastream"},

	{"datastream_destroy", dski_datastream_destroy, METH_VARARGS,
		"destroy a named datastream"},

	{"channel_open", dski_channel_open, METH_VARARGS,
		"create a named channel"},

	{"channel_close", dski_channel_close, METH_VARARGS,
		"destroy a named channel"},

	{"channel_flush", dski_channel_flush, METH_VARARGS,
		"flush a named channel"},

	{"entity_enable", dski_entity_enable, METH_VARARGS,
		"enable entity by composite-id"},

	{"histogram_enable", dski_histogram_enable, METH_VARARGS,
		"enable histogram by composite-id, with parameters"},

	{"entity_disable", dski_entity_disable, METH_VARARGS,
		"enable entity by composite-id"},

	{"reader_thread_run", dski_reader_thread_run, METH_VARARGS,
		"turn on mmap reader thread"},

	{"reader_thread_create", dski_reader_thread_create, METH_VARARGS,
		"turn on mmap reader thread"},

	{"reader_thread_kill", dski_reader_thread_kill, METH_VARARGS,
		"kill mmap reader thread"},

	{NULL, NULL, 0, NULL}
};

static void
setint(PyObject *d, const char *name, long value)
{
	PyObject *o = PyInt_FromLong(value);
	if (o && PyDict_SetItemString(d, name, o) == 0) {
		Py_DECREF(o);
	}
}


PyMODINIT_FUNC
initdski_mod(void)
{
	PyObject *dict, *module;

	module = Py_InitModule("dski_mod", DSKIMethods);
	if (module == NULL)
		return;

	dict = PyModule_GetDict(module);
	if (!dict)
		return;

	setint(dict, "DS_CHAN_TRIG", DS_CHAN_TRIG);
	setint(dict, "DS_CHAN_CONT", DS_CHAN_CONT);
	setint(dict, "DS_CHAN_MMAP", DS_CHAN_MMAP);

}
