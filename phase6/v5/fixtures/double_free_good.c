#include <stdlib.h>
void f(void) { int *p=malloc(sizeof *p); if (!p) return; free(p); }
