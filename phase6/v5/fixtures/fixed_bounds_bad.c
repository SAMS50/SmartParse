#include <stdlib.h>
void f(void) { char *p=malloc(4); if (!p) return; int index=4; p[index]=1; free(p); }
