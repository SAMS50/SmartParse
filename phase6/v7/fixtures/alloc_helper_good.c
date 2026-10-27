#include <stdlib.h>
static void *reserve(void){return malloc(sizeof(int));}
void probe(void){int *slot=reserve();if(!slot)return;*slot=42;free(slot);}
