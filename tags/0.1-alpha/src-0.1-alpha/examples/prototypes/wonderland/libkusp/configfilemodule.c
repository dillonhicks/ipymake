#include <Python.h>
#include <configfile.h>
#include <kusp_common.h>
#include <hashtable.h>
#include <linkedlist.h>
#include "kusp_private.h"

// author: Andrew Boie

static PyObject* translate_list(list_t *list, PyObject *topcontext);
static PyObject* translate_dictionary(hashtable_t *config,
		PyObject *topcontext);
static PyObject* translate_invocation(invocation_t *invoc,
		PyObject *topcontext);

int untranslate(PyObject *obj, value_t *val);


static PyObject*
translate_value(value_t *val, PyObject *topcontext) {
	//val = follow(val);

	switch (val->type) {
	case DICTTYPE:
		return translate_dictionary(val->value.h, topcontext);
	case LISTTYPE:
		return translate_list(val->value.l, topcontext);
	case INTTYPE:
		return PyInt_FromLong((long)val->value.i);
	case LONGTYPE:
		return PyLong_FromLongLong(val->value.g);
	case DOUBLETYPE:
		return PyFloat_FromDouble(val->value.d);
	case STRINGTYPE:
		return PyString_FromString(val->value.s);
	case INVOTYPE:
		return translate_invocation(val->value.v, topcontext);
	case BOOLTYPE:
		if (val->value.i) {
			Py_RETURN_TRUE;
		} else {
			Py_RETURN_FALSE;
		}
		break;
	case REFTYPE:
		return PyTuple_Pack(2, topcontext,
			PyString_FromString(val->value.s));
	}

	return NULL;
}

int untranslate(PyObject *obj, value_t *val)
{
	memset(val, 0, sizeof(*val));

	if (PyDict_Check(obj)) {
		int pos = 0;
		PyObject *pkey, *pval;
		val->type = DICTTYPE;
		val->value.h = create_dictionary();
		while (PyDict_Next(obj, &pos, &pkey, &pval)) {
			value_t *val2 = malloc(sizeof(*val2));

			if (untranslate(pval, val2) == 0) {
				free(val2);
				free_config(val->value.h);
				return 0;
			}
			hashtable_insert(val->value.h,
					strdup(PyString_AsString(pkey)),
					val2);
		}
	} else if (PyTuple_Check(obj)) {
		value_t *val2;
		val->type = INVOTYPE;
		val->value.v = malloc(sizeof(invocation_t));
		val->value.v->name = strdup(PyString_AsString(
					PyTuple_GetItem(obj, 0)));
		val2 = malloc(sizeof(*val2));
		if (untranslate(PyTuple_GetItem(obj, 1), val2) == 0) {
			free(val2);
			free(val->value.v->name);
			free(val->value.v);
			return 0;
		}
		val->value.v->params = val2->value.h;
		free(val2);
	} else if (PyList_Check(obj)) {
		val->type = LISTTYPE;
		val->value.l = create_list();
		int i;
		for (i=0; i < PyList_Size(obj); i++) {
			value_t *val2 = malloc(sizeof(*val2));
			if (untranslate(PyList_GetItem(obj, i), val2) == 0) {
				free(val2);

				// delete rest of incomplete list
				list_t *pos, *n;
				list_for_each_safe(pos, n, val->value.l) {
					free_value(pos->item);
					free(pos);
				}
				free(val->value.l);
				return 0;
			}
			list_append(val->value.l, val2);
		}
	} else if (PyString_Check(obj)) {
		val->type = STRINGTYPE;
		val->value.s = strdup(PyString_AsString(obj));
	} else if (PyLong_Check(obj)) {
		val->type = LONGTYPE;
		val->value.g = PyLong_AsLongLong(obj);
	} else if (PyBool_Check(obj)) {
		val->type = BOOLTYPE;
		if (obj == Py_True) {
			val->value.i = -1;
		} else {
			val->value.i = 0;
		}
	} else if (PyInt_Check(obj)) {
		val->type = INTTYPE;
		val->value.i = PyInt_AsLong(obj);
	} else if (PyFloat_Check(obj)) {
		val->type = DOUBLETYPE;
		val->value.d = PyFloat_AsDouble(obj);
	} else {
		printf("NOOOOOOOOOOO\n");
		PyErr_SetString(PyExc_TypeError, "invalid type");
		return 0;
	}
	return 1;
}


static PyObject*
translate_list(list_t *list, PyObject *topcontext)
{
	PyObject *result = PyList_New(0);

	list_t *cur;
	list_for_each(cur, list) {
		value_t *val = cur->item;
		PyList_Append(result, translate_value(val, topcontext));
	}
	return result;
}

static PyObject*
translate_invocation(invocation_t *invoc, PyObject *topcontext)
{
	PyObject *result = PyTuple_Pack(2,
		PyString_FromString(invoc->name),
		translate_dictionary(invoc->params, topcontext));
	return result;
}


static PyObject*
translate_dictionary(hashtable_t *config, PyObject *topcontext)
{
	PyObject *result = PyDict_New();

	if (topcontext == NULL) {
		topcontext = result;
	}

	if (hashtable_count(config) == 0)
		return result;


	hashtable_itr_t *itr = hashtable_iterator(config);
	do {
		value_t *val = hashtable_iterator_value(itr);
		char *key = hashtable_iterator_key(itr);
		PyObject *py_val = translate_value(val, topcontext);

		PyDict_SetItemString(result, key, py_val);
	} while (hashtable_iterator_advance(itr));
	free(itr);

	return result;
}

static int
do_check(hashtable_t *config, hashtable_t *spec)
{
	struct vexcept *ex;
	ex = verify_config_dict(config, spec, NULL);
	if (ex) {
		PyObject *l = PyList_New(0);
		while (ex != NULL) {
			PyObject *m = PyString_FromString(ex->message);
			PyList_Append(l, m);
			ex = ex->next;
		}
		PyObject *e = PyErr_NewException(
			"configfile_mod.ConfigVerifyException",
			PyExc_Exception,
			NULL);
		PyErr_SetObject(e, l);
		return 0;
	}
	return 1;
}

static PyObject *
configfile_parse_config(PyObject *self, PyObject *args)
{
	char *filename;
	char *specfilename = NULL;
	PyObject *retval = NULL;
	hashtable_t *config = NULL;
	hashtable_t *spec = NULL;


	if (!PyArg_ParseTuple(args, "ss", &filename, &specfilename)) {
		PyErr_Clear();
		if (!PyArg_ParseTuple(args, "s", &filename)) {
			return NULL;
		}
	}

	config = parse_config(filename);


	if (!config) {
		PyErr_SetString(PyExc_Exception, filename);
		goto errout;
	}


	if (specfilename != NULL) {
		spec = parse_spec(specfilename);
		if (!spec) {
			PyErr_SetString(PyExc_Exception, specfilename);
			goto errout;
		}

		if (!do_check(config, spec)) {
			goto errout;
		}
	}

	retval = translate_dictionary(config, NULL);

errout:
	if (config) free_config(config);
	if (spec) free_config(spec);
	return retval;

}

static PyObject *
configfile_check_spec_dict(PyObject *self, PyObject *args)
{
	value_t cv;
	char *specspecfilename;
	hashtable_t *spec;
	if (!PyArg_ParseTuple(args, "O&s", untranslate, &cv,
				&specspecfilename)) {
		return NULL;
	}

	if (PyErr_Occurred()) {
		return NULL;
	}

	if (cv.type != DICTTYPE) {
		PyErr_SetString(PyExc_TypeError, "parameters must be dictionaries");
		return NULL;
	}

	spec = cv.value.h;

	hashtable_t *specspec = parse_config(specspecfilename);
	if (!specspec) {
		PyErr_SetString(PyExc_Exception, specspecfilename);
		return NULL;
	}


	if (!do_check(spec, specspec)) {
		free_config(specspec);
		free_config(spec);
		return NULL;
	}

	PyObject *retval = translate_dictionary(spec, NULL);
	free_config(spec);
	free_config(specspec);
	return retval;
}




static PyObject *
configfile_check_dict(PyObject *self, PyObject *args)
{
	value_t cv, sv;
	if (!PyArg_ParseTuple(args, "O&O&", untranslate, &cv, untranslate, &sv)) {
		return NULL;
	}

	if (PyErr_Occurred()) {
		return NULL;
	}

	if (cv.type != DICTTYPE || sv.type != DICTTYPE) {
		PyErr_SetString(PyExc_TypeError, "parameters must be dictionaries");
		return NULL;
	}

	do_check(cv.value.h, sv.value.h);
	free_config(sv.value.h);
	if (PyErr_Occurred()) {
		free_config(cv.value.h);
		return NULL;
	}

	PyObject *retval = translate_dictionary(cv.value.h, NULL);
	free_config(cv.value.h);
	return retval;
}

static PyObject *
configfile_config_to_string(PyObject *self, PyObject *args)
{
	char *cstr;
	hashtable_t *cfg;
	value_t cv;
	size_t sz;
	PyObject *retval;

	if (!PyArg_ParseTuple(args, "O&", untranslate, &cv)) {
		return NULL;
	}

	cfg = cv.value.h;

	config_to_string(cfg, &sz, &cstr);

	free_config(cfg);

	retval = PyString_FromString(cstr);
	return retval;
}

static PyObject *
configfile_parse_string(PyObject *self, PyObject *args)
{

	char *cstr;
	hashtable_t *cfg;
	PyObject *retval = NULL;

	if (!PyArg_ParseTuple(args, "s", &cstr)) {
		return NULL;
	}

	cfg = parse_config_string(cstr);


	if (!cfg) {
		PyErr_SetString(PyExc_Exception, "string");
		return NULL;
	}


	retval = translate_dictionary(cfg, NULL);

	free_config(cfg);

	return retval;

}


static PyMethodDef ConfigfileMethods[] = {
	{"parse_config", configfile_parse_config, METH_VARARGS,
		"Parse a configuration file."},
	{"check_dict", configfile_check_dict, METH_VARARGS,
		"Verify a config dict."},
	{"check_spec_dict", configfile_check_spec_dict, METH_VARARGS,
		"Verify correctness of specification"},
	{"parse_string", configfile_parse_string, METH_VARARGS,
		"Parse a string representation"},
	{"config_to_string", configfile_config_to_string, METH_VARARGS,
		"configfile dictionary to string representation"},
	{NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initconfigfile_mod(void)
{
	(void) Py_InitModule("configfile_mod", ConfigfileMethods);
}
