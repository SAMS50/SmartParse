#include <stdlib.h>
void release_twice(void) {
    int *pointer = malloc(sizeof *pointer);
    if (!pointer) return;
    free(pointer);
    free(pointer);
}
