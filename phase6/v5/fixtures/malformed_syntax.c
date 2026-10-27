#include <stdlib.h>
void f(void) { char *p=malloc(4) if (!p) return; p[4]=1; free(p); }
