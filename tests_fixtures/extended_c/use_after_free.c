#include <stdlib.h>
int read_released(void) {
    int *pointer = malloc(sizeof *pointer);
    if (!pointer) return 0;
    *pointer = 42;
    free(pointer);
    return *pointer;
}
