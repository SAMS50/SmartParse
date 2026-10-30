#include <stdlib.h>
int f(void) { int *p=malloc(sizeof *p); if (!p) return 0; *p=1; int value=*p; free(p); return value; }
