#include <stdio.h>
#include <math.h>
#include <assert.h>

extern double almide_distance(double ax, double ay, double bx, double by);
extern double almide_area_circle(double r);
extern double almide_area_rect(double w, double h);

typedef struct { double x; double y; } MidpointResult;
extern void almide_midpoint(double ax, double ay, double bx, double by, MidpointResult* out);

int main() {
    double d = almide_distance(0, 0, 3, 4);
    printf("distance = %f\n", d);
    assert(fabs(d - 5.0) < 0.001);

    double a = almide_area_circle(5.0);
    printf("area(circle(5)) = %f\n", a);
    assert(fabs(a - 78.54) < 0.1);

    double ar = almide_area_rect(3.0, 4.0);
    printf("area(rect(3,4)) = %f\n", ar);
    assert(fabs(ar - 12.0) < 0.001);

    MidpointResult mid;
    almide_midpoint(0, 0, 10, 10, &mid);
    printf("midpoint = (%f, %f)\n", mid.x, mid.y);
    assert(fabs(mid.x - 5.0) < 0.001);

    printf("\nC FFI: ALL TESTS PASSED\n");
    return 0;
}
