# Namespaces and Overloading

## Namespaces

Namespaces prevent name collisions.

```cpp
namespace motor {
    void start();
}
```

Usage:

```cpp
motor::start();
```

Two namespaces can contain the same name:

```cpp
namespace camera {
    void start();
}

namespace motor {
    void start();
}
```

Avoid large-scale:

```cpp
using namespace std;
```

especially in headers.

---

## Function overloading

C++ allows multiple functions with the same name when their parameter lists differ.

```cpp
void print(int x);
void print(double x);
void print(const std::string& x);
```

The compiler chooses the best match.

Return type alone cannot distinguish overloads:

```cpp
int f();
double f();   // invalid
```

---

## Operator overloading

Operators can be defined for user-defined types.

```cpp
class Point {
public:
    Point operator+(const Point& other) const {
        return {x + other.x, y + other.y};
    }

    int x{};
    int y{};
};
```

Usage:

```cpp
Point c = a + b;
```

Good operator overloads should behave naturally and predictably.

## Interview takeaway

Namespaces organize names. Function overloading provides multiple behaviors under one function name. Operator overloading lets user-defined types behave naturally with operators.
