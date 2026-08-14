# Copy Constructor and Copy Assignment

## Copy constructor

Creates a **new object** from an existing object.

```cpp
class Foo {
public:
    Foo(const Foo& other) {
        // copy from other
    }
};
```

Used in cases like:

```cpp
Foo a;
Foo b = a;
Foo c(a);
```

Both `b` and `c` are newly constructed objects.

## Copy assignment

Copies into an object that **already exists**.

```cpp
class Foo {
public:
    Foo& operator=(const Foo& other) {
        if (this != &other) {
            // copy state
        }
        return *this;
    }
};
```

Example:

```cpp
Foo a;
Foo b;

b = a;
```

`b` already exists, so copy assignment runs.

## Key distinction

```text
Foo b = a;   -> copy constructor
b = a;       -> copy assignment
```

## Why this matters

For classes that manually own resources, shallow copying may cause:
- double deletion
- shared raw pointers unintentionally
- use-after-free

Modern C++ usually prefers the **Rule of Zero**: use standard library types that already manage resources safely.

## Interview takeaway

Copy constructor = initialize a new object from another.

Copy assignment = replace the state of an existing object with another object's state.
