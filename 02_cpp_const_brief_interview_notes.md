# C++ `const` — Brief Interview Notes

## Core Idea

`const` means:

> This object/value cannot be modified through this name, pointer, or reference.

```cpp
const int x = 10;
// x = 20;   // error
```

---

## 1. `const` Reference

```cpp
int x = 10;
const int& r = x;

// r = 20;   // error
x = 20;      // okay
```

`const int&` means you cannot modify the object **through `r`**.

It does **not** necessarily mean the original object is immutable.

Common use:

```cpp
void process(const std::vector<int>& data);
```

Use this for a large read-only object to avoid copying.

---

## 2. Pointer to `const`

```cpp
const int* p = &x;
// *p = 20;   // error

p = &y;       // okay
```

Meaning:

```text
pointer can change
pointed-to value cannot be changed through the pointer
```

Equivalent spelling:

```cpp
int const* p;
```

---

## 3. `const` Pointer

```cpp
int* const p = &x;

*p = 20;      // okay
// p = &y;    // error
```

Meaning:

```text
pointer cannot change
pointed-to value can change
```

---

## 4. `const` Pointer to `const`

```cpp
const int* const p = &x;
```

Neither is allowed:

```cpp
// *p = 20;
// p = &y;
```

---

## Quick Pointer Rule

Read pointer declarations from right to left:

```cpp
const int* p;        // pointer to const int
int* const p = &x;   // const pointer to int
const int* const p;  // const pointer to const int
```

---

## 5. `const` Member Functions

```cpp
class Sensor {
public:
    int value() const {
        return value_;
    }

private:
    int value_{};
};
```

The trailing `const` means the function promises not to modify the observable state of the object.

It also allows the function to be called on a `const` object:

```cpp
const Sensor s;
s.value();   // okay
```

A non-`const` member function normally cannot be called on a `const` object.

---

## 6. Const Overloads

Classes can provide mutable and read-only access:

```cpp
class Buffer {
public:
    int& operator[](std::size_t i) {
        return data_[i];
    }

    const int& operator[](std::size_t i) const {
        return data_[i];
    }

private:
    int data_[10]{};
};
```

---

## 7. `const` and Function Parameters

For small cheap types:

```cpp
void f(int x);
```

Usually prefer pass-by-value rather than:

```cpp
void f(const int& x);
```

For large read-only objects:

```cpp
void f(const LargeObject& obj);
```

For mutable required objects:

```cpp
void f(LargeObject& obj);
```

---

## 8. Important Trap

```cpp
int x = 10;
const int& r = x;

x = 20;

std::cout << r;   // 20
```

`const` protects access through `r`; it does not freeze `x`.

---

## 9. `const_cast`

C++ allows removing constness:

```cpp
const_cast<int&>(r)
```

Use it very rarely.

Modifying an object that was originally declared `const` through a cast can cause **undefined behavior**.

---

# Interview Summary

```text
const T        -> immutable through this object
const T&       -> read-only reference
const T*       -> pointer to read-only T
T* const       -> non-reseatable pointer
const T* const -> non-reseatable pointer to read-only T
method() const -> promises not to modify object state
```

## Main Principle

> `const` is mainly about expressing and enforcing what code is allowed to modify.

Good const-correctness makes APIs easier to understand and harder to misuse.
