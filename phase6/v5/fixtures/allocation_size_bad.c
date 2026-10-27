#include <stdlib.h>
void f(void) { int *p=malloc(1); if (!p) return; *p=1; free(p); }
