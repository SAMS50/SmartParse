#include <stdlib.h>
struct Entry { int code; };
int release_entry(void) {
 struct Entry *item=malloc(sizeof *item);
 if(!item) return 0;
 item->code=29;
 int code=item->code;
 free(item);
 return code;
}
