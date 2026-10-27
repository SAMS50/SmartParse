#include "include/eligibility_config.h"
#ifndef INITIAL_VALUE
#define INITIAL_VALUE 4
#endif
int item_value(const EligibilityItem *item) {
    return item->values[0] + header_value();
}
int main(void) {
    EligibilityItem item = {"café", {INITIAL_VALUE, 2}};
    return item_value(&item);
}
