#define PY_SSIZE_T_CLEAN
#include <Python.h>

typedef struct line_s {
  uint64_t offset;
  uint32_t length;
} line_t;

typedef struct cmost_s {
  FILE *fp;
  uint64_t file_size;
  line_t *lines;
  unsigned n_lines;
} cmost_t;

static cmost_t cm;

int open_doc(char *path)
{
  cm.fp = fopen(path, "r");
  if (cm.fp == NULL)
    return 1;

  fseek(cm.fp, 0, SEEK_END);
  cm.file_size = ftell(cm.fp);
  fseek(cm.fp, 0, SEEK_SET);
  return 0;
}

void read_doc(void) {
  unsigned buf_size = 1 << 16;
  char *buf = malloc(buf_size);

  unsigned alloc_lines = 1000;
  cm.lines = calloc(alloc_lines, sizeof(*cm.lines));
  cm.n_lines = 1;

  size_t chunk_offset = 0;
  size_t chunk_size;
  while ((chunk_size = fread(buf, 1, buf_size, cm.fp)) > 0) {
    char *p = buf - 1;
    char *buf_end = buf + chunk_size;
    while ((p = memchr(p + 1, '\n', buf_end - p - 1)) != NULL) {
      if (cm.n_lines == alloc_lines) {
        float est_lines = cm.file_size * cm.n_lines / cm.lines[cm.n_lines - 1].offset * 1.1;
        alloc_lines = (uint64_t) est_lines;
        cm.lines = realloc(cm.lines, alloc_lines * sizeof(*cm.lines));
      }
      uint64_t offset = chunk_offset + p - buf + 1;
      cm.lines[cm.n_lines - 1].length = offset - cm.lines[cm.n_lines - 1].offset - 1;
      cm.lines[cm.n_lines++].offset = offset;
    }
    chunk_offset += chunk_size;
  }

  /* File size may have changed since most_open_doc. This is fine since we
   * only used the old size to estimate the number of lines to allocate. */
  cm.file_size = chunk_offset;

  if (cm.lines[cm.n_lines - 1].offset == cm.file_size) {
    /* We will hit this block in two case:
     * 1. The file is zero length. In this case we want n_lines == 0.
     * 2. The file ends in a trailing newline (\n). In this case we'll have inserted an
     *    extra line pointing one byte beyond the end of the file, which we must discard. */
    --cm.n_lines;
  } else {
    /* If the file doesn't end in a trailing \n, we wont have written the final line's length */
    cm.lines[cm.n_lines - 1].length = cm.file_size - cm.lines[cm.n_lines - 1].offset;
  }

  free(buf);
}

static PyObject *read_file(PyObject *self, PyObject *args)
{
  char *file_path;
  if (!PyArg_ParseTuple(args, "s", &file_path))
    return NULL;

  if (open_doc(file_path) != 0)
    return PyErr_Format(PyExc_OSError, "Failed to open '%s'", file_path);

  read_doc();
  return PyLong_FromUnsignedLong(cm.n_lines);
}

static PyObject *read_line(PyObject *self, PyObject *args)
{
  uint64_t line_number;
  if (!PyArg_ParseTuple(args, "K", &line_number))
    return NULL;

  if (line_number >= cm.n_lines)
    return PyErr_Format(PyExc_IndexError, "Line number %lu out of range", line_number);

  line_t line = cm.lines[line_number];

  fseek(cm.fp, line.offset, SEEK_SET);
  char buf[line.length];
  size_t rc = fread(buf, 1, line.length, cm.fp);
  if (rc != line.length)
    return PyErr_Format(PyExc_IOError, "Unexpected EOF reading %d bytes at %lu",
                        line.length, line.offset);

  return Py_BuildValue("s#", buf, line.length);
}

#define METHOD(_name, _args, _desc) {#_name, _name, METH_VARARGS, #_name "(" _args ")\n--\n\n" _desc}
static PyMethodDef CmostMethods[] = {
  METHOD(read_file, "path", "Read the specified file.\nReturns the number of lines in the file"),
  METHOD(read_line, "line_i", "Read a single line.\nReturns its contents as a string, "
         "excluding the final newline if present."),
  {},
};
#undef METHOD

static struct PyModuleDef cmostmodule = {
  PyModuleDef_HEAD_INIT,
  "cmost",
  "Optimised file reader for most",
  -1,
  CmostMethods,
};

PyMODINIT_FUNC PyInit_cmost(void)
{
  return PyModule_Create(&cmostmodule);
}
