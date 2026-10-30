int takes_int(int value) { return value; }
struct Item { int value; };
int bad_return(void) { struct Item item = {1}; return item; }
int main(void) {
    int value = missing_identifier;
    takes_int(1, 2);
    if (value = 3) return value;
    return 0;
}
