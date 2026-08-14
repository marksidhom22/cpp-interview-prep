# Constructors, Destructors, and Initialization Lists

## Constructor

A constructor initializes an object.

```cpp
class Device {
public:
    Device(int id)
        : id_(id) {}

private:
    int id_;
};
```

A constructor:
- has the same name as the class
- has no return type
- runs automatically when an object is created

## Initialization lists

Prefer:

```cpp
Device(int id)
    : id_(id) {}
```

over:

```cpp
Device(int id) {
    id_ = id;
}
```

The initialization list initializes members directly instead of default-constructing and then assigning.

Initialization lists are required for things such as:

```cpp
const int id_;
Driver& driver_;
```

They are also used to call base-class constructors.

## Destructor

```cpp
class Device {
public:
    ~Device() {
        // cleanup
    }
};
```

A destructor:
- runs automatically when an object dies
- has the form `~ClassName()`
- has no arguments or return type

It is used to release owned resources.

## Important RAII connection

```cpp
{
    Device d;
}   // destructor runs here
```

C++ ties cleanup to object lifetime.

## Interview takeaway

Construction establishes a valid object state; destruction releases owned resources. Prefer initialization lists for member initialization.
