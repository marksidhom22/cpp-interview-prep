# C++ `const`: Syntax, Meaning, and Interview Reference

`const` is not merely a compiler restriction. It is a way to express an API contract: which access paths may modify an object, which objects are safe to expose, and which overloads should be available.

---

## Part I - Five-Minute Interview Review

Use this section for fast recall. Follow the links for the complete rules and examples.

### The mandatory rules

```cpp
const T object{};       // object cannot be modified after initialization
const T& ref = object;  // read-only access through ref
const T* ptr = &object; // reseatable pointer to read-only T
T* const ptr2 = &value; // fixed pointer to mutable T
const T* const ptr3 = &object; // fixed pointer to read-only T
```

- `const` restricts what can be changed **through a particular object, pointer, or reference**. It does not necessarily make the underlying object globally immutable. See [The access-path model](#1-the-access-path-model).
- A const object must be initialized because it cannot be assigned a value later. See [Const objects and initialization](#2-const-objects-and-initialization).
- Read pointer declarations from the identifier outward, or identify the const on each side of `*`. See [Pointers and two independent kinds of const](#3-pointers-and-two-independent-kinds-of-const).
- `const T&` is a non-owning, non-reseatable, read-only access path. It can bind to a mutable object or a temporary. See [Const references](#4-const-references).
- Top-level const qualifies an object itself; low-level const qualifies an object reached through a pointer or reference. This matters in copying, deduction, and overloads. See [Top-level and low-level const](#5-top-level-and-low-level-const).
- Pass small cheap values by value. Use `const T&` for a required large read-only object. Use `const T*` when the object is optional. See [Const in function parameters](#6-const-in-function-parameters).
- A trailing `const` on a member function makes `*this` const for that call and permits the function on const objects. See [Const member functions](#8-const-member-functions).
- Const and non-const member overloads commonly provide read-only and writable access. See [Const overloads](#9-const-overloads).
- `mutable` supports logical constness for implementation details such as caches and mutexes; it is not a license to hide meaningful state changes. See [Logical constness and mutable](#10-logical-constness-and-mutable).
- Removing const with `const_cast` is rarely a good design. Modifying an object that was originally declared const is undefined behavior. See [`const_cast`](#11-const_cast).
- `const` does not imply thread safety. See [Const and concurrency](#14-const-and-concurrency).

### Declaration table

| Declaration | Can change the value through this name? | Can reseat the pointer? |
|---|---:|---:|
| `const int x` | No | N/A |
| `const int& r` | No | References cannot be reseated |
| `int* p` | Yes | Yes |
| `const int* p` | No | Yes |
| `int* const p` | Yes | No |
| `const int* const p` | No | No |

### High-frequency interview answers

**What does `const` mean?**

It means an object cannot be modified through the const-qualified access path. It is a compile-time interface guarantee, not necessarily global immutability.

**Are `const int*` and `int const*` different?**

No. Both mean pointer to const `int`.

**Can a const reference refer to a mutable object?**

Yes. The original object may still change through a different non-const name.

**Why use a trailing `const` on getters?**

It documents non-mutation and allows the getter to be called on const objects.

**Can two free functions differ only by top-level const on a by-value parameter?**

No. `void f(int)` and `void f(const int)` are the same function type for overloading purposes.

---

## Part II - Detailed Reference

## 1. The access-path model

A useful definition is:

> `const` prevents mutation through a particular access path.

```cpp
int value = 10;
const int& view = value;

// view = 20; // error
value = 20;   // valid
```

`view` does not freeze `value`. It only refuses to provide a mutable operation through `view`.

This distinction matters in APIs:

```cpp
void inspect(const Sensor& sensor);
```

The function promises not to mutate `sensor` through this reference. It does not prove that another thread or another alias cannot mutate the same `Sensor`.

### Why this model is better than "const means immutable"

"Immutable" often suggests the value can never change. C++ `const` is usually shallower and more local:

- Another non-const alias may modify the object.
- A pointer member may point to mutable external data.
- `mutable` members may change inside const member functions.
- Hardware or another thread may change externally observed state.

### Interview question

**Question:** If `const int& r` refers to a non-const `int x`, can `x` change?

**Answer:** Yes. It cannot be changed through `r`, but it can be changed through `x` or another mutable alias.

---

## 2. Const objects and initialization

```cpp
const int limit = 100;
```

A const object must be given its state during initialization because ordinary assignment is unavailable afterward:

```cpp
// const int limit; // error for a local scalar: no initializer
// limit = 100;
```

For class types, construction establishes the const object's initial state:

```cpp
class Device {
public:
    explicit Device(int id) : id_{id} {}

    int id() const { return id_; }

private:
    int id_;
};

const Device device{42};
```

The constructor can initialize the members. After construction, only operations allowed by the const interface may be called.

### Const data members

```cpp
class Packet {
public:
    Packet(int sequence, int payload)
        : sequence_{sequence},
          payload_{payload} {}

private:
    const int sequence_;
    int payload_;
};
```

`sequence_` must be initialized in the member-initializer list. Assignment in the constructor body would be too late because the member already exists by then.

### Tradeoff

A const data member can communicate a strong invariant, but it can also disable or complicate assignment for the containing class. Often a private ordinary member with no mutating public operation provides adequate encapsulation while leaving the type assignable.

### Interview question

**Question:** Why must a const data member appear in the constructor initializer list?

**Answer:** Members are initialized before the constructor body begins. A const member cannot be default-initialized and then assigned.

---

## 3. Pointers and two independent kinds of const

A pointer introduces two independently qualifiable objects:

1. The pointed-to object.
2. The pointer object itself.

### Pointer to const

```cpp
int x = 10;
int y = 20;

const int* p = &x;
// *p = 11; // error
p = &y;     // valid
```

The pointer is reseatable, but it provides read-only access to the `int`.

These spellings are equivalent:

```cpp
const int* p;
int const* p;
```

### Const pointer

```cpp
int x = 10;
int y = 20;

int* const p = &x;
*p = 11;   // valid
// p = &y; // error
```

The pointer's stored address is fixed, but the pointed-to value is mutable.

### Const pointer to const

```cpp
const int x = 10;
const int* const p = &x;

// *p = 11; // error
// p = &y;  // error
```

Neither the pointer nor the pointed-to object can be changed through `p`.

### Reading difficult declarations

Start at the identifier and work outward:

```cpp
const Widget* const handle;
```

- `handle` is const.
- It is a pointer.
- It points to a const `Widget`.

Type aliases can make const placement surprising:

```cpp
using IntPtr = int*;

int value = 0;
IntPtr const p = &value; // int* const, not const int*
```

`const` qualifies the alias as one complete type.

### Conversion direction

A pointer to mutable data can convert to a pointer to const data:

```cpp
int* mutable_ptr = &x;
const int* read_only_ptr = mutable_ptr;
```

The reverse is rejected because it would discard a safety guarantee:

```cpp
const int* read_only_ptr = &x;
// int* mutable_ptr = read_only_ptr; // error
```

### Interview question

**Question:** Explain `const char* const p`.

**Answer:** `p` is a non-reseatable pointer that provides read-only access to a `char`.

---

## 4. Const references

```cpp
std::string name = "camera";
const std::string& ref = name;
```

`ref`:

- Must be initialized.
- Cannot be reseated.
- Does not own `name`.
- Cannot modify `name` through this reference.
- Can still dangle if `name` dies first.

### Binding to mutable objects

```cpp
int x = 10;
const int& r = x;

x = 20;
std::cout << r; // 20
```

The reference observes the same object. Const controls permission, not whether the value may change elsewhere.

### Binding to temporaries

A const lvalue reference can bind to a temporary:

```cpp
const std::string& text = std::string{"hello"};
```

In this direct local binding, the temporary's lifetime is extended to the lifetime of `text`.

A function parameter can also bind to a temporary:

```cpp
void print(const std::string& text);

print("hello");
```

The temporary survives through the full expression containing the call, which is enough for `print`. Storing a pointer or reference to it for later would be dangerous.

### Why `const T&` is common

For a large object, it avoids a copy while expressing required read-only borrowing:

```cpp
void process(const std::vector<int>& values);
```

For a small type such as `int`, pass by value is normally simpler:

```cpp
void set_limit(int limit);
```

### Interview question

**Question:** Why can `const T&` bind to a temporary while `T&` normally cannot?

**Answer:** A mutable lvalue reference suggests a stable object that the caller expects to be modified. Const binding safely permits read-only use and may extend the temporary's lifetime under specific rules.

---

## 5. Top-level and low-level const

Top-level const qualifies the object itself:

```cpp
const int value = 10; // value itself is const
int* const p = &x;    // p itself is const
```

Low-level const is nested inside another type:

```cpp
const int* p = &value; // pointed-to int is const
const int& r = value;  // referred-to int is const
```

### Copying drops top-level const

```cpp
const int source = 10;
int copy = source; // valid
```

`copy` is a new object. The fact that `source` could not be modified does not require the copy to be const.

Low-level const cannot be discarded implicitly:

```cpp
const int* source_ptr = &source;
// int* mutable_ptr = source_ptr; // error
```

### Function parameters

For by-value parameters, top-level const is not part of the callable interface:

```cpp
void f(int value);
// void f(const int value); // redeclaration of the same function, not an overload
```

Inside the function definition, adding const can still prevent accidental local modification:

```cpp
void f(const int value) {
    // value = 2; // error inside this function
}
```

For pointers and references, const applies to the caller's object and does affect the interface:

```cpp
void inspect(const Device& device);
void update(Device& device);
```

### Interview question

**Question:** Why can `void f(int)` not be overloaded with `void f(const int)`?

**Answer:** The argument is copied. Top-level const affects only the function's private parameter object, so it is removed from the function type used for overload resolution.

---

## 6. Const in function parameters

Parameter types should express size, ownership, optionality, and mutation.

### Small input value

```cpp
void set_priority(int priority);
```

Copying is cheap, and the function receives an independent value.

### Required large read-only input

```cpp
void analyze(const Frame& frame);
```

No copy is made. The caller must supply an object, and the function promises not to modify it through `frame`.

### Required mutable input

```cpp
void normalize(Frame& frame);
```

Mutation is part of the API contract.

### Optional read-only input

```cpp
void log(const Metadata* metadata);
```

`nullptr` can mean that metadata is absent.

### Sink parameter

When a function needs its own copy or will move the value into storage, pass by value can be appropriate:

```cpp
class Device {
public:
    explicit Device(std::string name)
        : name_{std::move(name)} {}

private:
    std::string name_;
};
```

This supports both lvalues and rvalues with one overload, at the cost of a copy for lvalue callers.

### Avoid meaningless const on value declarations in headers

```cpp
void set_limit(const int limit); // const does not help callers
```

Prefer:

```cpp
void set_limit(int limit);
```

The definition may choose `const int limit` locally if useful.

### Interview question

**Question:** Choose between `T`, `const T&`, and `const T*`.

**Answer:** Use `T` for cheap values or when taking a local value; `const T&` for a required borrowed read-only object; and `const T*` when absence is part of the contract.

---

## 7. Const in return types

Returning a value as const is usually unnecessary and can interfere with moving in older patterns:

```cpp
const Widget make_widget(); // usually avoid
Widget make_widget();       // preferred
```

The caller receives a new value and should control whether its local object is const:

```cpp
const Widget widget = make_widget();
```

Const references and pointers are useful when returning borrowed access:

```cpp
class Registry {
public:
    const Device& primary() const {
        return primary_;
    }

private:
    Device primary_;
};
```

The caller cannot mutate the returned object through that reference.

### Lifetime requirement

A returned reference must refer to an object that outlives the reference:

```cpp
const std::string& bad() {
    std::string local = "temporary";
    return local; // dangling reference
}
```

### Const by value for primitive types

```cpp
const int size(); // top-level const on returned scalar is ignored by most uses
```

Prefer:

```cpp
int size();
```

### Interview question

**Question:** Why is `const T` as a return-by-value type usually discouraged?

**Answer:** The caller owns a new value, so top-level const adds little. It can also unnecessarily restrict operations on the result.

---

## 8. Const member functions

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

The trailing const:

```cpp
int value() const
```

qualifies the implicit object parameter. A useful conceptual model is:

```cpp
int value(const Sensor& self);
```

Inside a const member function:

- Ordinary data members cannot be modified.
- Only other const member functions can normally be called.
- `this` provides access to a const `Sensor`.

A const object can call only const-qualified operations:

```cpp
const Sensor sensor;
int value = sensor.value();
```

A non-const object can call both const and non-const operations.

### What const member functions do not guarantee

They do not automatically guarantee:

- No externally visible changes.
- No mutation through pointer members.
- Thread safety.
- No I/O.
- No changes to `mutable` members.

They primarily enforce the C++ type-system rules for the object's direct state.

### Interview question

**Question:** What does the trailing const in `int value() const` qualify?

**Answer:** It qualifies the implicit object parameter, so the function treats the object as const and can be called on const instances.

---

## 9. Const overloads

A class can provide mutable and read-only access:

```cpp
class Buffer {
public:
    int& operator[](std::size_t index) {
        return data_[index];
    }

    const int& operator[](std::size_t index) const {
        return data_[index];
    }

private:
    int data_[10]{};
};
```

Usage:

```cpp
Buffer writable;
writable[3] = 42;       // non-const overload returns int&
int x = writable[3];    // still selects the non-const overload

const Buffer read_only;
int y = read_only[3];   // const overload returns const int&
// read_only[3] = 42;   // error
```

The object's constness selects the overload, not how the returned result will later be used.

### Conceptual overloads

```cpp
int& subscript(Buffer& self, std::size_t index);
const int& subscript(const Buffer& self, std::size_t index);
```

For a mutable object, binding to `Buffer&` is the better match. For a const object, only `const Buffer&` is valid.

### Return type alone cannot overload

```cpp
int& operator[](std::size_t);
const int& operator[](std::size_t); // error: differs only by return type
```

The trailing member-function const is what creates distinct overloads.

### Reducing duplication

A simple function can be duplicated safely. More complicated implementations sometimes centralize the const version and carefully delegate from the non-const version, but clarity is usually more valuable than clever casting. C++23 explicit object parameters can also reduce duplication in supported codebases.

### Interview question

**Question:** Why does `int x = writable[3]` use the non-const overload even though it only reads?

**Answer:** Overload resolution occurs from the expression and the object's type. It does not inspect the later use of the returned value.

---

## 10. Logical constness and `mutable`

Bitwise constness means direct non-mutable data members are unchanged. Logical constness asks whether the object's externally meaningful state is unchanged.

A cache can change without changing the abstract value:

```cpp
class Measurement {
public:
    double converted() const {
        if (!cache_valid_) {
            cached_value_ = calculate();
            cache_valid_ = true;
        }
        return cached_value_;
    }

private:
    double calculate() const;

    mutable bool cache_valid_{false};
    mutable double cached_value_{};
};
```

`mutable` permits those members to change in const member functions.

Another legitimate use is synchronization:

```cpp
class Counter {
public:
    int value() const {
        std::lock_guard lock{mutex_};
        return value_;
    }

private:
    mutable std::mutex mutex_;
    int value_{};
};
```

Locking the mutex changes the mutex's internal state but not the logical value of `Counter`.

### Tradeoff

`mutable` can preserve a clean const API, but overuse can make `const` misleading. Do not mark business state mutable merely to avoid designing the right mutating operation.

### Interview question

**Question:** Give a legitimate use for `mutable`.

**Answer:** A cache-valid flag or mutex used by a logically read-only member function, provided the externally observable value is not conceptually changed.

---

## 11. `const_cast`

`const_cast` can add or remove cv-qualification:

```cpp
void legacy_api(char* text);

void call_legacy(const char* text) {
    legacy_api(const_cast<char*>(text));
}
```

This is safe only if `legacy_api` truly does not modify the characters and its signature is merely outdated.

### Originally mutable object

```cpp
int value = 10;
const int& read_only = value;
int& mutable_again = const_cast<int&>(read_only);
mutable_again = 20; // defined because the original object is non-const
```

Although defined, this often indicates a poor interface.

### Originally const object

```cpp
const int value = 10;
int& dangerous = const_cast<int&>(value);
dangerous = 20; // undefined behavior
```

The cast can compile, but it cannot make an originally const object safely writable.

### Interview question

**Question:** When does modifying through a cast-away-const reference cause undefined behavior?

**Answer:** When the underlying object was originally defined as const.

---

## 12. `auto`, templates, and const deduction

Plain `auto` usually drops top-level const and references:

```cpp
const int value = 10;
const int& ref = value;

auto a = value; // int
auto b = ref;   // int
```

Use qualifiers explicitly when needed:

```cpp
const auto& c = ref; // const int&
auto& d = ref;       // const int&; referred-to const is preserved
```

`decltype(auto)` preserves the declaration form more exactly:

```cpp
decltype(auto) e = (ref); // const int&
```

Parentheses matter with `decltype`.

### Template deduction

For a by-value template parameter, top-level const is generally dropped:

```cpp
template<class T>
void by_value(T value);
```

For reference parameters, referred-to const participates in deduction:

```cpp
template<class T>
void by_reference(T& value);
```

Passing a `const int` makes `T` deduce as `const int`.

### Interview question

**Question:** What is the type of `auto x = ref` when `ref` is `const int&`?

**Answer:** `int`. Plain `auto` with by-value deduction drops the reference and top-level const.

---

## 13. `const`, `constexpr`, and `consteval`

These words are related but not interchangeable.

### `const`

```cpp
const int value = runtime_input();
```

The object cannot be modified after initialization, but its value may be determined at runtime.

### `constexpr`

```cpp
constexpr int max_devices = 16;
```

A constexpr object must be usable as a constant expression. A constexpr function can be evaluated at compile time when its arguments and context permit:

```cpp
constexpr int square(int x) {
    return x * x;
}
```

It may also execute at runtime:

```cpp
int n = runtime_input();
int result = square(n);
```

### `consteval`

```cpp
consteval int protocol_id(int major, int minor) {
    return major * 100 + minor;
}
```

Every potentially evaluated call must be evaluated at compile time.

### Practical comparison

| Keyword | Cannot mutate object? | Must be compile-time value? |
|---|---:|---:|
| `const` object | Yes | No |
| `constexpr` object | Yes | Yes |
| `constexpr` function call | N/A | Only when required and possible |
| `consteval` function call | N/A | Yes |

### Interview question

**Question:** Is every const object a compile-time constant?

**Answer:** No. It may be initialized from a runtime value. `constexpr` expresses constant-expression usability.

---

## 14. Const and concurrency

A const member function is not automatically thread-safe:

```cpp
class Statistics {
public:
    int sample_count() const {
        return samples_.size();
    }

    void add_sample(int value) {
        samples_.push_back(value);
    }

private:
    std::vector<int> samples_;
};
```

Calling `sample_count()` concurrently with `add_sample()` without synchronization can cause a data race, even though the first function is const.

Const says that a function does not mutate ordinary members through its own access path. Thread safety concerns all concurrent accesses to shared state.

`mutable std::mutex` is common because locking is an implementation detail of a logically const operation.

### Interview question

**Question:** Does a const getter make concurrent reads and writes safe?

**Answer:** No. Const correctness and synchronization are separate guarantees.

---

## 15. Const and volatile in embedded code

`volatile` and `const` express different constraints:

- `const` restricts program mutation through an access path.
- `volatile` tells the compiler that accesses are observable and the value may change outside ordinary program flow.

A read-only memory-mapped register might be represented as:

```cpp
volatile const std::uint32_t* status =
    reinterpret_cast<volatile const std::uint32_t*>(status_address);
```

The program should not write through this pointer, but every read must actually occur because hardware may change the value.

A writable register might use:

```cpp
volatile std::uint32_t* control =
    reinterpret_cast<volatile std::uint32_t*>(control_address);
```

`volatile` is not an atomicity or thread-synchronization mechanism. It does not make compound operations safe between threads.

### Interview question

**Question:** What does `volatile const` mean for a hardware register?

**Answer:** Software treats it as read-only, while reads remain observable because hardware may change the value asynchronously.

---

## 16. Common mistakes and diagnostics

### Mistake: believing const freezes every alias

```cpp
int x = 1;
const int& r = x;
x = 2; // valid
```

### Mistake: confusing pointer const positions

```cpp
const int* p; // pointer to const int
int* const p2 = &x; // const pointer to int
```

### Mistake: missing const on a getter

```cpp
int value(); // cannot be called on const object
```

Prefer when appropriate:

```cpp
int value() const;
```

### Mistake: returning const values

```cpp
const std::string name() const; // first const usually unnecessary
```

Prefer:

```cpp
std::string name() const;
```

### Mistake: assuming const means thread-safe

Protect shared mutable state with synchronization.

### Mistake: casting away a real const object

The cast may compile; mutation is still undefined behavior.

---

## 17. Design guidelines and tradeoffs

1. Start APIs read-only and add mutation only when required.
2. Use `const T&` for required borrowed read-only class objects when avoiding a copy matters.
3. Use values for small cheap types and sink parameters.
4. Use pointers for optional borrowed access, preferably with a clear null contract.
5. Add trailing const to every member operation that is logically read-only.
6. Provide paired const/non-const accessors when callers legitimately need both forms.
7. Use `mutable` only for implementation state that preserves logical constness.
8. Avoid owning raw pointers; const does not solve ownership.
9. Treat `const_cast` as an interface smell requiring justification.
10. Do not confuse const correctness with immutability, atomicity, or thread safety.

### Interview question

**Question:** What is the main benefit of const correctness?

**Answer:** It makes mutation permissions explicit, enables APIs for const objects, supports overload selection, and lets the compiler reject accidental writes.

---

## Final interview checklist

You should be able to explain without notes:

- The access-path meaning of const.
- Pointer-to-const versus const-pointer.
- Why `const T&` does not freeze a mutable object.
- Top-level versus low-level const.
- Why by-value top-level const does not create an overload.
- The trailing const on member functions.
- Const and non-const accessors.
- Logical constness and appropriate `mutable` usage.
- Why casting away original constness is dangerous.
- `const` versus `constexpr`, `consteval`, and `volatile`.
- Why const does not guarantee thread safety.
