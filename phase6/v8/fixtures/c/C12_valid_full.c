#include <stddef.h>
#define ROWS 3
typedef struct { int slots[ROWS]; const char *name; } Record;
int total_record(void) {
 Record r={{2,4,6},"new evaluation"};
 int total=0;
 for(size_t i=0;i<ROWS;i++) total+=r.slots[i];
 return total;
}
