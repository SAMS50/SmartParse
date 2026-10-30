#include <stdlib.h>
int f(void) { int *p=malloc(sizeof *p); if (!p) return 0; *p=1; free(p); return *p; }
