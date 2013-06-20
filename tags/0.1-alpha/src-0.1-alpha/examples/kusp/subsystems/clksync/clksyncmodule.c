/*
 * OLD Python wrapper for clksyncapi. Included until swig auto wrapper generation
 * is fully functional.
 */
#include <Python.h>
#include <clksyncapi.h>
#include <kusp_common.h>


static PyObject *clksync_error;



static PyObject *
clksyncmod_set_freq(PyObject *self, PyObject *args)
{
	unsigned long tsckhz;
	int fd;

	if (!PyArg_ParseTuple(args, "iL", &fd, &tsckhz))
		return NULL;


	int retval = clksync_set_freq(fd, tsckhz);

	if (retval < 0) {
		return PyErr_SetFromErrno(clksync_error);
	}

	Py_RETURN_NONE;
}

static PyObject *
clksyncmod_adj_time(PyObject *self, PyObject *args)
{
	struct timespec adj;
	int fd;

	if (!PyArg_ParseTuple(args, "ill", &fd, &adj.tv_sec, &adj.tv_nsec))
		return NULL;

	int retval = clksync_adj_time(fd, &adj);
	if (retval < 0) {
		return PyErr_SetFromErrno(clksync_error);
	}

	Py_RETURN_NONE;
}

static PyObject *
clksyncmod_get_info(PyObject *self, PyObject *args)
{
	clksync_info_t *nfo;

	if (!PyArg_ParseTuple(args, "")) {
		return NULL;
	}


	nfo = get_time_info();


	PyObject *result = PyDict_New();
	PyObject *ts = PyLong_FromUnsignedLongLong(nfo->ts);
	PyObject *tsckhz = PyLong_FromUnsignedLong(nfo->tsckhz);
	PyObject *tv_sec = PyLong_FromLong(nfo->time.tv_sec);
	PyObject *tv_nsec = PyLong_FromLong(nfo->time.tv_nsec);
	PyObject *shift = PyLong_FromUnsignedLong((unsigned long)nfo->shift);
	PyObject *mult = PyLong_FromUnsignedLong((unsigned long)nfo->mult);

	PyDict_SetItemString(result, "ts", ts);
	PyDict_SetItemString(result, "tsckhz", tsckhz);
	PyDict_SetItemString(result, "tv_sec", tv_sec);
	PyDict_SetItemString(result, "tv_nsec", tv_nsec);
	PyDict_SetItemString(result, "shift", shift);
	PyDict_SetItemString(result, "mult", mult);
	free(nfo);

	return result;
}





static PyMethodDef ClksyncapiMethods[] = {
	{"set_freq", clksyncmod_set_freq, METH_VARARGS,
		"set frequency"},
	{"adj_time", clksyncmod_adj_time, METH_VARARGS,
		"adjust time"},
	{"get_info", clksyncmod_get_info, METH_VARARGS,
		"get information"},
	{0,0,0,0}
};



PyMODINIT_FUNC
initclksync_mod(void)
{
	PyObject *module, *dict;
	module = Py_InitModule("clksync_mod", ClksyncapiMethods);
	dict = PyModule_GetDict(module);
	clksync_error = PyErr_NewException("clksync_mod.error", NULL, NULL);
	PyDict_SetItemString(dict, "error", clksync_error);
}

