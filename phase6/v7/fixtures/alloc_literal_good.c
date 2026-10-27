#include <stdlib.h>
void probe(void){ int *slot=malloc(sizeof *slot); if(!slot)return; *slot=42; free(slot); }
