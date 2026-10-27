#include <stdlib.h>
void lose_allocation(void) {
    int *pointer = malloc(sizeof *pointer);
    if (!pointer) return;
    *pointer = 42;
    /* Allocation goes out of scope without being released. */
}
