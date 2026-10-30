#include <stdlib.h>
void probe(void){ int *slot=malloc(1); if(!slot)return; *slot=42; free(slot); }
