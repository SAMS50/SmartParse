#include <stddef.h>
#include <string.h>

typedef struct {
    const char *name;
    unsigned count;
} Stock;

size_t find_stock(const Stock *items, size_t length, const char *name) {
    for (size_t i = 0; i < length; ++i) {
        if (strcmp(items[i].name, name) == 0) return i;
    }
    return length;
}

int main(void) {
    Stock items[] = {{"bolts", 12}, {"washers", 30}};
    size_t i = find_stock(items, sizeof items / sizeof items[0], "washers");
    return i == 1 ? 0 : 1;
}
