#include <stddef.h>
typedef struct Item { const char *name; int values[3]; } Item;
int total(const Item *item) { return item->values[0] + item->values[1]; }
int main(void) {
    Item item = {"hello", {1, 2, 3}};
    return total(&item) == 3 ? 0 : 1;
}
