#include <stdlib.h>
void probe(void){ size_t bytes=1; int *slot=malloc(bytes); if(!slot)return; *slot=42; free(slot); }
