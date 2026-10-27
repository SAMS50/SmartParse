typedef struct { int value; } Record;

int first(const Record *record) {
    int adjustment = ;
    return record->value + adjustment;
}

int second(const Record *record) {
    return record->value + ;
}

int third(void) {
    return unknown_record;
}

int accepts(int value) { return value; }
int invalid_call(void) { return accepts(1, 2); }
