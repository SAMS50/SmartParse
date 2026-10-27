#include <stdlib.h>
void probe(size_t bytes){int *slot=malloc(bytes);if(!slot)return;*slot=42;free(slot);}
