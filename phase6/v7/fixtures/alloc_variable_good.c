#include <stdlib.h>
void probe(void){ size_t bytes=sizeof(int); int *slot=malloc(bytes); if(!slot)return; *slot=42; free(slot); }
