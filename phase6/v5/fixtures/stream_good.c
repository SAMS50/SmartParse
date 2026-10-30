#include <stdio.h>
void f(void) { FILE *stream=fopen("input.txt","r"); if (!stream) return; fclose(stream); }
