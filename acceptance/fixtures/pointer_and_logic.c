#include <stdlib.h>

int read_null(void) {
    int *pointer = NULL;
    return *pointer;
}

void lose_buffer(void) {
    int *buffer = malloc(sizeof *buffer);
    if (buffer == NULL) return;
    *buffer = 7;
}

int stale_read(void) {
    int *buffer = malloc(sizeof *buffer);
    if (buffer == NULL) return 0;
    *buffer = 7;
    free(buffer);
    return *buffer;
}

void repeated_release(void) {
    int *buffer = malloc(sizeof *buffer);
    if (buffer == NULL) return;
    free(buffer);
    free(buffer);
}

/* Contract: sum ALL length elements. The last element is mistakenly omitted. */
int incomplete_sum(const int *items, int length) {
    int total = 0;
    for (int i = 0; i < length - 1; ++i) total += items[i];
    return total;
}

/* This assignment is deliberate here; its warning does not prove a bug. */
int intentional_assignment(int value) {
    if (value = 1) return value;
    return 0;
}
