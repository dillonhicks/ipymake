#include <Python.h>
#include <dsui.h>
#include <hashtable.h>
#include <misc.h>
/**
 * DSUI - Datastreams User Interface
 *        Python Bindings
 *
 * Author: Andrew Boie
 */


static void cleanup_callback(void) {
	dsui_cleanup();
}

static int active_ds = -1;
static char *active_log = NULL;

static struct datastream_ip *get_ip(char *group, char *name,
		int type, char *info)
{
	struct datastream_ip *ip;

	ip = dsui_get_ip_byname(group, name);

	if (ip) {
		return ip;
	}

	ip = dsui_create_ip(group, name, type, info);

	if (active_ds != -1) {
		dsui_enable_ip(active_ds, ip, NULL);
	}

	return ip;
}

static PyObject *dsuimod_init(PyObject *self, PyObject *args)
{
	char *filename;
	int buffers;

	if (!PyArg_ParseTuple(args, "si", &filename, &buffers)) {
		return NULL;
	}

	active_log = dsui_open_output_file(strdup(filename));
	active_ds = dsui_open_datastream(active_log, buffers, STREAM_NORMAL_MODE);
	dsui_enable_all_ips(active_ds);

	return PyInt_FromLong((long)active_ds);
}

static PyObject *dsuimod_declare(PyObject *self, PyObject *args)
{
	char *group, *name;

	if (!PyArg_ParseTuple(args, "ss",
		&group, &name)) {
		return NULL;
	}

	get_ip(group, name, DS_EVENT_TYPE,
			strdup("print_pickle"));

	Py_RETURN_NONE;
}

static PyObject *dsuimod_print(PyObject *self, PyObject *args)
{
	char *msg;

	if (!PyArg_ParseTuple(args, "s", &msg)) {
		return NULL;
	}

	dsui_printf(msg);

	Py_RETURN_NONE;
}

static PyObject *dsuimod_event(PyObject *self, PyObject *args)
{
	unsigned int tag = 0;
	char *data = NULL;
	int size = 0;
	char *group, *name;
	struct datastream_ip *ip;

	if (!PyArg_ParseTuple(args, "ss|Iz#",
		&group, &name, &tag, &data, &size)) {
		return NULL;
	}

	ip = get_ip(group, name, DS_EVENT_TYPE,
			strdup("print_pickle"));

	if (*ip->next) {
		dsui_event_log(ip, tag, size, data);
	}

	Py_RETURN_NONE;
}

static PyObject *dsuimod_write_time_state(PyObject *self, PyObject *args)
{
	if (active_log) {
		dsui_write_time_state(active_log);
	}

	Py_RETURN_NONE;

}

static PyObject *dsuimod_close(PyObject *self, PyObject *args)
{
	dsui_cleanup();
	Py_RETURN_NONE;

}


static PyMethodDef DsuiMethods[] = {
	{"init", dsuimod_init, METH_VARARGS,
		"initialize dsui"},
	{"log_event", dsuimod_event, METH_VARARGS,
		"log event"},
	{"declare", dsuimod_declare, METH_VARARGS,
		"declare event"},
	{"printf", dsuimod_print, METH_VARARGS,
		"print a string"},
	{"write_time", dsuimod_write_time_state, METH_VARARGS,
		"write timekeeping info"},
	{"close", dsuimod_close, METH_VARARGS,
		"close dsui and all output files"},
	{NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initdsui_mod(void)
{
	Py_InitModule("dsui_mod", DsuiMethods);
	Py_AtExit(cleanup_callback);
}


