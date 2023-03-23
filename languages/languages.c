#define PY_SSIZE_T_CLEAN
#include "Python.h"
#include <wctype.h>

static PyMethodDef module_methods[] = {
  NULL
};

static struct PyModuleDef module_definition = {
  .m_base = PyModuleDef_HEAD_INIT,
  .m_name = "binding",
  .m_doc = NULL,
  .m_size = -1,
  .m_methods = NULL,
};

PyMODINIT_FUNC PyInit_staticcodecov_languages(void) {
  PyObject *module = PyModule_Create(&module_definition);
  if (module == NULL) return NULL;
  return module;
}