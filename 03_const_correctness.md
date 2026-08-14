# C++ Const Correctness

## Core idea

Const correctness means using `const` consistently so code clearly expresses what may and may not be modified.

```cpp
void print(const Data& data);
```

This says:
- `data` is required
- no copy is made
- the function cannot modify `data` through this reference

## Const member functions

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

The trailing `const` means the function cannot normally modify the object.

```cpp
const Sensor s;
s.value();   // allowed
```

A non-const member function generally cannot be called on a const object.

## Const overloads

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

This allows mutable access for mutable objects and read-only access for const objects.

## Interview takeaway

Use `const` whenever mutation is not required. It documents intent and lets the compiler catch mistakes.
