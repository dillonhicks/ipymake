#include <Python.h>

#include <linux/ccsm.h>
#include <ccsm.h>

static int file_conv(PyObject *object, int *fdp)
{
	int fd = PyObject_AsFileDescriptor(object);

	if (fd < 0)
		return 0;

	*fdp = fd;
	return 1;
}

static PyObject *
ccsm_mod_create_set(PyObject *self, PyObject *args)
{
	const char *set_name;
	unsigned int flags;
	int fd, ret;

	if (!PyArg_ParseTuple(args, "O&si", file_conv, &fd, &set_name,
				&flags)) {
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	ret = ccsm_create_set(fd, set_name, flags);
	Py_END_ALLOW_THREADS

	return Py_BuildValue("i", ret);
}


static PyObject *
ccsm_mod_destroy_set(PyObject *self, PyObject *args)
{
	const char *set_name;
	int fd, ret;

	if (!PyArg_ParseTuple(args, "O&s", file_conv, &fd, &set_name)) {
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	ret = ccsm_destroy_set(fd, set_name);
	Py_END_ALLOW_THREADS

	return Py_BuildValue("i", ret);
}


static PyObject *
ccsm_mod_add_member(PyObject *self, PyObject *args)
{
	const char *set_name;
	const char *member_name;
	int fd, ret;

	if (!PyArg_ParseTuple(args, "O&ss", file_conv, &fd, &set_name,
				&member_name))
		return NULL;

	Py_BEGIN_ALLOW_THREADS
	ret = ccsm_add_member(fd, set_name, member_name);
	Py_END_ALLOW_THREADS

	return Py_BuildValue("i", ret);
}


static PyObject *
ccsm_mod_remove_member(PyObject *self, PyObject *args)
{
	const char *set_name;
	const char *member_name;
	int fd, ret;

	if (!PyArg_ParseTuple(args, "O&ss", file_conv, &fd, &set_name,
				&member_name))
		return NULL;

	Py_BEGIN_ALLOW_THREADS
	ret = ccsm_remove_member(fd, set_name, member_name);
	Py_END_ALLOW_THREADS

	return Py_BuildValue("i", ret);
}

	
static PyObject *
ccsm_mod_create_component_by_pid(PyObject *self, PyObject *args)
{
	const char *component_name;
	int fd, ret, pid;

	if (!PyArg_ParseTuple(args, "O&si", file_conv, &fd, &component_name,
				&pid))
		return NULL;

	Py_BEGIN_ALLOW_THREADS
	ret = ccsm_create_component_by_pid(fd, component_name, pid);
	Py_END_ALLOW_THREADS

	return Py_BuildValue("i", ret);
}


static PyObject *
ccsm_mod_destroy_component_by_name(PyObject *self, PyObject *args)
{
	const char *component_name;
	int fd, ret;

	if (!PyArg_ParseTuple(args, "O&s", file_conv, &fd, &component_name))
		return NULL;

	Py_BEGIN_ALLOW_THREADS
	ret = ccsm_destroy_component_by_name(fd, component_name);
	Py_END_ALLOW_THREADS

	return Py_BuildValue("i", ret);
}

	
static PyObject *
ccsm_mod_destroy_component_by_pid(PyObject *self, PyObject *args)
{
	int fd, ret, pid;

	if (!PyArg_ParseTuple(args, "O&i", file_conv, &fd, &pid))
		return NULL;

	Py_BEGIN_ALLOW_THREADS
	ret = ccsm_destroy_component_by_pid(fd, pid);
	Py_END_ALLOW_THREADS

	return Py_BuildValue("i", ret);
}

#if 0
static PyObject *
ccsm_set_params(PyObject *self, PyObject *args)
{
	const char *set_name;
	const char *param_ptr;
	unsigned int type;
	int fd, ret;
	size_t size;

	if (!PyArg_ParseTuple(args, "O&ss#i", file_conv, &fd, &group_name,
				&param, &size, &type))
		return NULL;

	Py_BEGIN_ALLOW_THREADS
	ret = ccsm_set_param(fd, set_name, (void*)param_ptr, type);
	Py_END_ALLOW_THREADS

	return Py_BuildValue("i", ret);
}

static PyObject *
ccsm_get_params(PyObject *self, PyObject *args)
{
  int fd;
  char *set_name;
  unsigned int type;
  size_t size;
  
  if (!PyArg_ParseTuple(args, "O&sIi", file_conv, &fd, &set_name, &size, &type))
    return NULL;
  
  void * param_ptr = malloc(size);

  int result = ccsm_get_params(fd, set_name, param_ptr, type);
  PyObject * retval;
  if (result == 0) {
    retval = PyString_FromStringAndSize(param_ptr, size);
  } else {
    retval = Py_BuildValue("i", result);
  } 
  free(param_ptr);
  return retval;
}
#endif

static PyMethodDef CCSMmethods[] = {
//	{"open", ccsm_mod_open, METH_VARARGS, ""},  	  //may not be necessary
	{"create_set", ccsm_mod_create_set, METH_VARARGS, ""},
	{"destroy_set", ccsm_mod_destroy_set, METH_VARARGS, ""},
	{"add_member", ccsm_mod_add_member, METH_VARARGS, ""},
	{"remove_member", ccsm_mod_remove_member, METH_VARARGS, ""},
	{"create_component_by_pid", ccsm_mod_create_component_by_pid, METH_VARARGS, ""},
	{"destroy_component_by_name", ccsm_mod_destroy_component_by_name, METH_VARARGS, ""},
	{"destroy_component_by_pid", ccsm_mod_destroy_component_by_pid, METH_VARARGS, ""},
//	{"set_params", ccsm_mod_set_params, METH_VARARGS, ""},
//	{"get_params", ccsm_mod_get_params, METH_VARARGS, ""},
	{NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initccsm_mod(void)
{
	PyObject *dict, *module;

	module = Py_InitModule("ccsm_mod", CCSMmethods);
	if (module == NULL)
		return;

	dict = PyModule_GetDict(module);
	if (!dict)
		return;
}
