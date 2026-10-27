#include <stdlib.h>
void f(void) { int *p=malloc(sizeof(char)); if (!p) return; *p=1; free(p); }
