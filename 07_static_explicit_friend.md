# `static`, `explicit`, and `friend`

## `static` class members

A static data member belongs to the class rather than each object.

```cpp
class Device {
public:
    static int count;
};
```

All `Device` objects share the same `count`.

A static member function has no `this` pointer:

```cpp
class Device {
public:
    static int getCount();
};
```

It can directly access only static members.

---

## `static` local variable

```cpp
void f() {
    static int count = 0;
    ++count;
}
```

The variable:
- is initialized once
- keeps its value between calls
- has static storage duration

---

## `explicit`

Prevents unintended implicit conversions.

```cpp
class Distance {
public:
    explicit Distance(int meters);
};
```

Without `explicit`, this might be allowed:

```cpp
Distance d = 10;
```

With `explicit`:

```cpp
Distance d(10);   // okay
```

Use `explicit` on single-argument constructors unless implicit conversion is intentionally desired.

---

## `friend`

A friend can access private members.

```cpp
class Box {
    friend void inspect(const Box&);

private:
    int value_{};
};
```

Use `friend` sparingly because it weakens encapsulation.

Common legitimate uses include certain operator overloads and tightly coupled helper functions/classes.

## Interview takeaway

- `static` = shared/class-level or long-lived local state
- `explicit` = prevents accidental implicit conversions
- `friend` = grants private access deliberately
