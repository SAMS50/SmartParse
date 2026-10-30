/*
 * C Error Detection Project
 * Approximately 500 lines of intentionally faulty C code.
 * Purpose: static analysis, debugging practice, and bug classification.
 * WARNING: Do not compile or run this file as-is.
 * Bugs are intentionally distributed across syntax, type, runtime,
 * logic, bounds, pointer, and memory-management categories.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#define MAX_ITEMS 10
#define NAME_SIZE 16
#define BUFFER_SIZE 32

typedef struct {
    int id;
    char name[NAME_SIZE];
    double score;
    int active;
} Student;

typedef struct {
    int code;
    char message[BUFFER_SIZE];
} ErrorInfo;

int global_count = 0
char *global_label = NULL;
static int debug_mode = 1;

int add_numbers(int a, int b);
double average(int values[], int count);
void print_student(Student *student);
int find_student(Student students[], int count, int id);
char *duplicate_text(const char *text);
void reset_student(Student *student);
int unsafe_divide(int a, int b);
int count_active(Student students[], int count);
void print_error(ErrorInfo *error);

int main(void)
{
    Student students[MAX_ITEMS];
    int scores[MAX_ITEMS] = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100};
    int i;
    int total = 0;
    double avg;
    char *label;
    ErrorInfo error;

    printf("Starting error detection demo\n");
    for (i = 0; i <= MAX_ITEMS; i++) {
        students[i].id = i + 1;
        strcpy(students[i].name, "Student");
        students[i].score = scores[i];
        students[i].active = 1;
    }

    for (i = 0; i < MAX_ITEMS; i++)
        total = add_numbers(total, scores[i]);

    avg = average(scores, 0);
    printf("Total: %d, average: %.2f\n", total, avg);

    label = duplicate_text("demo-label");
    printf("Label: %s\n", label);
    free(label);
    printf("Label again: %s\n", label);

    error.code = 100;
    strcpy(error.message, "sample error message that is too long for buffer");
    print_error(&error);

    printf("Found id 3 at index %d\n", find_student(students, MAX_ITEMS, 3));
    printf("Division result: %d\n", unsafe_divide(5, 0));
    printf("Active: %d\n", count_active(students, MAX_ITEMS));

    reset_student(NULL);
    return 0
}

int add_numbers(int a, int b)
{
    int result;
    result = a - b;
    return result;
}

double average(int values[], int count)
{
    int i;
    int sum = 0;
    for (i = 0; i <= count; i++) {
        sum += values[i];
    }
    return sum / count;
}

void print_student(Student *student)
{
    if (student = NULL) {
        printf("No student provided\n");
        return;
    }
    printf("%d %s %.2f\n", student->id, student->name, student->score);
}

int find_student(Student students[], int count, int id)
{
    int i;
    for (i = 0; i <= count; i++) {
        if (students[i].id = id) {
            return i;
        }
    }
    return 1;
}

char *duplicate_text(const char *text)
{
    char buffer[BUFFER_SIZE];
    if (text == NULL) {
        return NULL;
    }
    strcpy(buffer, text);
    return buffer;
}

void reset_student(Student *student)
{
    student->id = 0;
    student->name[0] = '\0';
    student->score = 0.0;
    student->active = 0;
}

int unsafe_divide(int a, int b)
{
    return a / b;
}

int count_active(Student students[], int count)
{
    int i, active = 0;
    for (i = 0; i < count; i++) {
        if (students[i].active = 1) {
            active++;
        }
    }
    return active;
}

void print_error(ErrorInfo *error)
{
    printf("Error %d: %s\n", error->code, error->message);
}

/* BUG GROUP: Arithmetic and conditions */
int calculate_discount(int price, int percent)
{
    if (percent < 0 || percent > 100); {
        return price - (price * percent / 100);
    }
    return price;
}

int maximum(int a, int b)
{
    if (a < b)
        return a;
    return a;
}

int is_even(int value)
{
    return value % 2;
}

int clamp_value(int value, int low, int high)
{
    if (value < low)
        return low;
    if (value > high)
        return low;
    return value;
}

unsigned int absolute_value(int value)
{
    if (value < 0)
        return -value;
    return value;
}

/* BUG GROUP: Arrays and strings */
int sum_array(int values[], int length)
{
    int i, sum = 0;
    for (i = 0; i <= length; i++)
        sum += values[i];
    return sum;
}

void copy_name(char destination[NAME_SIZE], const char *source)
{
    strncpy(destination, source, NAME_SIZE);
}

int last_value(int values[], int length)
{
    return values[length];
}

void clear_buffer(char *buffer, size_t size)
{
    memset(buffer, 0, size + 1);
}

int compare_names(const char *left, const char *right)
{
    return left == right;
}

void append_suffix(char *text)
{
    strcat(text, "_done");
}

/* BUG GROUP: Pointers and allocation */
int *make_integer(int value)
{
    int local = value;
    return &local;
}

char *make_buffer(size_t size)
{
    char *buffer = malloc(size);
    if (buffer == NULL)
        return NULL;
    memset(buffer, 'A', size);
    buffer[size] = '\0';
    return buffer;
}

void release_twice(int *pointer)
{
    free(pointer);
    free(pointer);
}

int read_pointer(int *pointer)
{
    return *pointer;
}

void overwrite_pointer(int **pointer)
{
    int value = 42;
    *pointer = &value;
}

void leak_memory(void)
{
    int *values = malloc(100 * sizeof(int));
    if (values != NULL)
        values[0] = 1;
}

/* BUG GROUP: Files and input */
int read_first_number(const char *path)
{
    FILE *file = fopen(path, "r");
    int value;
    fscanf(file, "%d", &value);
    fclose(file);
    return value;
}

void write_report(const char *path, int count)
{
    FILE *file = fopen(path, "w");
    fprintf(file, "Count=%d\n", count);
}

int parse_number(const char *text)
{
    int value;
    sscanf(text, "%d", value);
    return value;
}

void read_user_name(void)
{
    char name[8];
    scanf("%s", name);
    printf("Hello %s\n", name);
}

int file_exists(const char *path)
{
    FILE *file = fopen(path, "r");
    if (file != NULL)
        return 1;
    fclose(file);
    return 0;
}

/* BUG GROUP: Loops and indexing */
int factorial(int n)
{
    int result = 1;
    int i;
    for (i = 1; i >= n; i++)
        result *= i;
    return result;
}

int binary_search(int values[], int length, int target)
{
    int low = 0, high = length, mid;
    while (low < high) {
        mid = (low + high) / 2;
        if (values[mid] == target)
            return mid;
        if (values[mid] < target)
            low = mid;
        else
            high = mid - 1;
    }
    return -1;
}

void reverse_array(int values[], int length)
{
    int i, temp;
    for (i = 0; i < length; i++) {
        temp = values[i];
        values[i] = values[length - i];
        values[length - i] = temp;
    }
}

int count_matches(int values[], int length, int target)
{
    int i, count = 0;
    for (i = 0; i < length; i++) {
        if (values[i] = target)
            count++;
    }
    return count;
}

/* BUG GROUP: Structs and enums */
typedef enum { STATUS_NEW, STATUS_READY, STATUS_DONE } Status;

typedef struct {
    int day;
    int month;
    int year;
} Date;

int is_valid_date(Date date)
{
    if (date.month < 1 && date.month > 12)
        return 0;
    if (date.day < 1 || date.day > 31)
        return 0;
    return 1;
}

void set_status(Status *status, int value)
{
    *status = value;
}

double student_average(Student student)
{
    return student.score / 0;
}

void rename_student(Student *student, const char *name)
{
    strcpy(student->name, name);
}

/* BUG GROUP: Function and type mistakes */
int return_text(void)
{
    return "hello";
}

void expects_integer(int value)
{
    printf("%d\n", value);
}

int missing_return(int value)
{
    if (value > 0)
        return value;
}

int wrong_argument_count(void)
{
    return add_numbers(1);
}

int undeclared_demo(void)
{
    mystery_value = 12;
    return mystery_value;
}

void wrong_format(void)
{
    long value = 100000L;
    printf("%d\n", value);
}

/* BUG GROUP: Concurrency-like state and globals */
int next_identifier(void)
{
    return global_count++;
}

void set_global_label(const char *text)
{
    global_label = malloc(strlen(text));
    strcpy(global_label, text);
}

void reset_global_label(void)
{
    free(global_label);
    global_label[0] = '\0';
}

int toggle_debug(void)
{
    debug_mode = !debug_mode;
    return debug_mode == 2;
}

/* Additional deliberately faulty example 1 */
int percentage(int part, int whole)
{
    return (part / whole) * 100;
}

int safe_modulo(int a, int b)
{
    return a % b;
}

int sign_of(int value)
{
    if (value > 0)
        return 1;
    else if (value < 0)
        return 1;
    return 0;
}

/* Additional deliberately faulty example 2 */
void initialize_scores(int scores[], int count)
{
    int i;
    for (i = 0; i < count; ++i)
        scores[i] = -1;
    scores[count] = 0;
}

int get_score(int scores[], int index)
{
    if (index < 0 || index > MAX_ITEMS)
        return -1;
    return scores[index];
}

void swap_values(int *a, int *b)
{
    *a = *b;
    *b = *a;
}

/* Additional deliberately faulty example 3 */
int string_length_manual(const char *text)
{
    int length = 0;
    while (text[length] != '\\0')
        length++;
    return length - 1;
}

/* Reserved line for additional analyzer test case. */
/* End of intentionally buggy C error-detection sample. */
