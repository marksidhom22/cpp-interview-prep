# C++ Copy Construction, Copy Assignment, and Copy Design

Copying is not just syntax. It is a design decision about whether two objects should have independent state, share a resource, duplicate an external resource, or not be copyable at all.

Related construction and lifetime rules are covered in [`04_constructors_destructors_initialization.md`](./04_constructors_destructors_initialization.md).

---

## Part I - Five-Minute Interview Review

### Mandatory distinction

```cpp
Foo a;       // default construction
Foo b = a;   // copy construction: b is new
Foo c(a);    // copy construction: c is new
b = a;       // copy assignment: b already exists
```

- `Foo b = a;` is initialization despite the equals sign. See [Copy construction](#2-copy-construction).
- `b = a;` assigns into an existing object. See [Copy assignment](#3-copy-assignment).
- If you do not declare copy operations, the compiler often generates memberwise copy operations. See [Compiler-generated copying](#4-compiler-generated-copying).
- Memberwise copying is correct when every base and member already has the desired copy behavior. This is the Rule of Zero. See [Rule of Zero](#11-rule-of-zero).
- An owning raw pointer is copied only as an address by compiler-generated copying, which can cause double deletion and leaks. See [Shallow copy failure](#6-shallow-copy-failure-with-owning-pointers).
- A deep copy allocates a distinct resource and copies its contents. See [Deep-copy Buffer](#7-deep-copy-buffer-rule-of-three).
- If copying has no sensible meaning, delete it explicitly. See [Non-copyable types](#10-non-copyable-types).
- Copy assignment must consider self-assignment and exception safety. See [Copy-assignment design](#8-copy-assignment-design).
- The Rule of Three applies to manual copy-era resource management; the Rule of Five adds moves; the Rule of Zero is preferred. See [Rule of Three, Five, and Zero](#12-rule-of-three-five-and-zero).
- Copy elision can remove or avoid copies in return-value scenarios, but it does not turn an lvalue copy such as `Foo b = a` into assignment. See [Copy elision](#16-copy-elision-and-performance).

### Standard signatures

```cpp
class Foo {
public:
    Foo(const Foo& other);            // copy constructor
    Foo& operator=(const Foo& other); // copy assignment

    Foo(Foo&& other) noexcept;            // move constructor
    Foo& operator=(Foo&& other) noexcept; // move assignment
};
```

### Decision table

| Resource semantics | Copy design |
|---|---|
| Value-like members (`string`, `vector`) | Let compiler copy |
| Unique resource that cannot be duplicated | Delete copy; support move |
| Heap buffer with value semantics | Deep copy, preferably through `vector` |
| OS handle with duplication API | Custom copy that duplicates handle |
| Intentionally shared object | Explicit shared ownership, often `shared_ptr` |
| Polymorphic object | Consider virtual `clone()`; avoid slicing |

### Five interview checks

1. **Copy constructor or assignment?** A declaration creates a new object; a later `=` expression assigns.
2. **What does the generated copy do?** It copies each direct base and non-static data member.
3. **Why is raw-pointer copying dangerous?** It copies an address, not the allocation it may own.
4. **Why return `*this` from assignment?** To match built-in assignment behavior and allow chaining.
5. **What is the preferred modern rule?** Rule of Zero: compose types whose own special members are already correct.

---

## Part II - Detailed Reference

## 1. Copying is a semantic contract

Before implementing a copy constructor, ask what a copy should mean.

For a mathematical point:

```cpp
struct Point {
    int x{};
    int y{};
};
```

A copy should clearly produce an independent equal value.

For a file descriptor, mutex, thread, interrupt registration, or unique hardware channel, "copy" may have no natural meaning. Possible policies include:

- Disallow copying.
- Transfer ownership with move semantics.
- Duplicate the underlying OS resource.
- Share access using explicit shared state.
- Copy only configuration, not runtime identity.

The code must reflect the domain decision.

### Value semantics versus identity semantics

A value-semantic type is interchangeable with another equal value:

```cpp
std::string a = "imu";
std::string b = a;
```

Changing `b` does not change `a`.

An identity-bearing object may represent one real device or session:

```cpp
CameraConnection connection;
```

Creating a "copy" may incorrectly suggest there are two independent connections.

### Interview question

**Question:** What should you decide before writing a copy constructor?

**Answer:** Whether copying should create an independent value, share state, duplicate an external resource, or be prohibited.

---

## 2. Copy construction

A copy constructor initializes a new object from an existing object of the same type:

```cpp
class Foo {
public:
    Foo(const Foo& other);
};
```

Examples:

```cpp
Foo a;
Foo b = a; // copy-initialization
Foo c(a);  // direct-initialization
Foo d{a};  // direct-list-initialization
```

All three target objects are new.

### Why the parameter is usually `const Foo&`

- Passing by value would itself require copying, creating recursion.
- Passing by reference avoids another copy.
- Const allows copying from const objects and ordinary lvalues.
- A copy operation should not normally change the source.

A rare legacy type may have `Foo(Foo&)`, but that cannot copy from const sources and behaves poorly with modern containers.

### Explicit copy constructor

A copy constructor may be marked explicit:

```cpp
explicit Foo(const Foo&);
```

Then direct initialization can use it:

```cpp
Foo c(a);
```

but copy-initialization cannot:

```cpp
// Foo b = a;
```

This is unusual; copy constructors normally model natural copying and are not explicit.

### Other contexts that may copy

Depending on optimization and overloads:

- Passing an object by value.
- Returning an object by value.
- Throwing/catching by value.
- Inserting an lvalue into a container.
- Capturing an object by value in a lambda.

### Interview question

**Question:** Why is `Foo b = a;` not copy assignment?

**Answer:** The statement declares `b`; no prior `b` exists. The equals sign is initialization syntax selecting a constructor.

---

## 3. Copy assignment

Copy assignment replaces the state of an existing object:

```cpp
class Foo {
public:
    Foo& operator=(const Foo& other);
};
```

Usage:

```cpp
Foo a;
Foo b;

b = a;
```

Both objects already exist.

### Why it returns `Foo&`

Built-in assignment returns the assigned object as an lvalue, allowing:

```cpp
a = b = c;
```

A conventional implementation returns:

```cpp
return *this;
```

### Existing resources matter

Unlike copy construction, assignment must replace state that may already own resources:

```text
Copy construction:
    empty new object -> acquire copied state

Copy assignment:
    existing state -> safely replace with copied state
```

This makes exception safety and cleanup central.

### Interview question

**Question:** What is the main implementation difference between copy construction and copy assignment?

**Answer:** Copy assignment must safely dispose of or replace an already-existing state, while copy construction starts a new object's state.

---

## 4. Compiler-generated copying

If you do not declare copy operations, the compiler often implicitly declares them. When used and valid, they copy:

- Direct base-class subobjects.
- Non-static data members.
- Array elements member by member.

Example:

```cpp
class Report {
public:
    std::string title;
    std::vector<int> values;
};
```

Compiler-generated copying is correct:

```cpp
Report first;
Report second = first;
```

`std::string` and `std::vector` implement value semantics, so the copied object receives independent logical contents.

### Explicitly defaulting

You can state the intent:

```cpp
class Report {
public:
    Report(const Report&) = default;
    Report& operator=(const Report&) = default;
};
```

Do this when it improves interface clarity. Avoid declaring special members without a reason, because declarations can affect move generation and triviality.

### When generated copy is deleted

Copy operations may be implicitly deleted when a base or member cannot be copied:

```cpp
class Owner {
private:
    std::unique_ptr<int> value_;
};

Owner a;
// Owner b = a; // error
```

A `unique_ptr` is intentionally non-copyable, so the containing type's implicit copy constructor is deleted.

User-declared move operations also affect implicit copy generation. Exact implicit-generation rules are worth knowing conceptually, but the design rule is simpler: explicitly default or delete special members when ownership semantics are not obvious.

### Interview question

**Question:** Does "I did not write a copy constructor" mean the class cannot be copied?

**Answer:** No. The compiler may generate one. Copying fails only if the operation is deleted, inaccessible, ambiguous, or otherwise unavailable.

---

## 5. Memberwise copy: when it is correct

Memberwise copy is desirable when members express the intended semantics:

```cpp
class TelemetryPacket {
public:
    std::uint64_t timestamp{};
    std::string source;
    std::vector<std::byte> payload;
};
```

The generated copy:

- Copies the timestamp.
- Copies the string contents.
- Copies the vector elements.

This provides independent value semantics.

### Pointers that are non-owning

A raw pointer can be correct under memberwise copying if it is explicitly non-owning:

```cpp
class SensorView {
public:
    explicit SensorView(const Sensor* sensor)
        : sensor_{sensor} {}

private:
    const Sensor* sensor_; // borrowed, optional
};
```

Copying the view should normally copy the pointer so both views refer to the same external sensor. The lifetime contract must ensure the sensor outlives both views.

### References

A reference member is copied by binding the new object's reference to the same referred-to object:

```cpp
class SensorRef {
    Sensor& sensor_;
};
```

Reference members also make ordinary copy assignment problematic because a reference cannot be reseated. The compiler-generated copy assignment is typically deleted.

### Interview question

**Question:** Is copying a raw pointer always wrong?

**Answer:** No. It is often correct for a non-owning view. It is dangerous when the pointer represents unique ownership and memberwise copy duplicates only the address.

---

## 6. Shallow-copy failure with owning pointers

Consider:

```cpp
class Buffer {
public:
    explicit Buffer(std::size_t size)
        : size_{size},
          data_{new int[size]{}} {}

    ~Buffer() {
        delete[] data_;
    }

private:
    std::size_t size_;
    int* data_; // owning pointer
};
```

The class compiles and works for a single object. The problem appears when copying:

```cpp
Buffer first{10};
Buffer second = first;
```

The generated copy constructor performs a shallow copy:

```text
first.data_  ----+
                 +---- one allocated array
second.data_ ----+
```

Both destructors later execute `delete[]` on the same address: undefined behavior.

### Generated copy assignment is worse

```cpp
Buffer first{10};
Buffer second{20};

second = first;
```

Memberwise assignment overwrites `second.data_`:

- The original 20-element allocation becomes unreachable: memory leak.
- Both objects point to the same 10-element allocation: later double deletion.

### Terminology

- **Shallow copy:** copy handles/addresses without duplicating owned resource contents.
- **Deep copy:** create a distinct resource and copy the contents.
- Shallow copy is not inherently bad; it is wrong when it contradicts ownership semantics.

### Interview question

**Question:** Why is the destructor alone a warning sign in this `Buffer`?

**Answer:** The class manually releases a resource, so compiler-generated copying may duplicate the resource handle without duplicating ownership safely.

---

## 7. Deep-copy Buffer: Rule of Three

A complete C++11-era example:

```cpp
#include <algorithm>
#include <cstddef>
#include <utility>

class Buffer {
public:
    explicit Buffer(std::size_t size)
        : size_{size},
          data_{new int[size]{}} {}

    ~Buffer() {
        delete[] data_;
    }

    Buffer(const Buffer& other)
        : size_{other.size_},
          data_{new int[other.size_]} {
        std::copy_n(other.data_, size_, data_);
    }

    Buffer& operator=(const Buffer& other) {
        if (this == &other) {
            return *this;
        }

        int* replacement = new int[other.size_];
        std::copy_n(other.data_, other.size_, replacement);

        delete[] data_;
        data_ = replacement;
        size_ = other.size_;

        return *this;
    }

    int& operator[](std::size_t index) {
        return data_[index];
    }

    const int& operator[](std::size_t index) const {
        return data_[index];
    }

private:
    std::size_t size_{};
    int* data_{};
};
```

The copy constructor allocates independent storage:

```cpp
Buffer first{10};
first[0] = 42;

Buffer second = first;
second[0] = 100;
```

Now:

```text
first.data_  -> [42, ...]
second.data_ -> [100, ...]
```

### Why allocate before deleting in assignment?

```cpp
int* replacement = new int[other.size_];
```

If allocation fails, the original object remains unchanged. Only after the replacement is successfully prepared does the implementation release old state.

For `int`, copying cannot throw. For general element types, stronger exception-safety techniques are needed.

### Rule of Three

If a class manually manages a resource and needs any of:

- Destructor.
- Copy constructor.
- Copy assignment.

it often needs to consider all three.

### Interview question

**Question:** What makes this a deep copy?

**Answer:** The destination allocates its own array and copies every element, so each object owns a distinct allocation.

---

## 8. Copy-assignment design

Copy assignment must handle several cases.

### Self-assignment

```cpp
buffer = buffer;
```

A naive implementation might delete the resource and then attempt to copy from the same deleted resource.

An identity check handles it:

```cpp
if (this == &other) {
    return *this;
}
```

A well-designed algorithm such as copy-and-swap can be naturally self-assignment safe without a separate check.

### Exception safety

Common guarantees are:

- **No-throw guarantee:** operation never throws.
- **Strong guarantee:** if it fails, the target remains unchanged.
- **Basic guarantee:** invariants remain valid, but state may change.
- **No guarantee:** even invariants may be lost.

Preparing a full replacement before modifying `*this` is a common strong-guarantee strategy.

### Copy-and-swap

```cpp
class Buffer {
public:
    Buffer& operator=(Buffer other) {
        swap(other);
        return *this;
    }

    void swap(Buffer& other) noexcept {
        using std::swap;
        swap(size_, other.size_);
        swap(data_, other.data_);
    }

    // constructors and destructor omitted
};
```

The parameter `other` is a copy for lvalue arguments or a move for rvalues when move construction exists. Swapping cannot fail, and `other` destroys the old state when the function returns.

#### Tradeoffs

- Clear strong exception safety.
- Naturally handles self-assignment.
- May do an allocation even when existing capacity could be reused.
- A carefully optimized assignment may perform less work.

### Interview question

**Question:** Why should copy assignment not delete old memory before successfully acquiring replacement memory?

**Answer:** If allocation or copying then fails, the object loses its original valid state. Preparing first can provide the strong exception guarantee.

---

## 9. Copying external resources

Not every resource can be deep-copied like memory.

### File descriptor

A copy might call an OS duplication function:

```cpp
FileHandle::FileHandle(const FileHandle& other)
    : fd_{duplicate_fd(other.fd_)} {}
```

The two handles may refer to the same underlying open-file description, so offsets and flags can still interact depending on OS semantics. "Duplicate" must be defined precisely.

### Hardware device

A UART or CAN controller object may represent unique hardware ownership. Copying should likely be deleted.

### Registration or callback token

Copying a registration could accidentally unregister twice or duplicate callbacks. A move-only token is often better.

### Shared resource

Shared ownership may be intentional:

```cpp
class SharedConfiguration {
    std::shared_ptr<const Data> data_;
};
```

Memberwise copy then increments the reference count and shares immutable data. This differs from deep copying and has atomic/reference-count overhead.

### Interview question

**Question:** Does deep copy always mean duplicating bytes?

**Answer:** No. For external resources it means implementing the domain-specific independent-copy semantics, if such semantics exist. Sometimes copying should instead be deleted.

---

## 10. Non-copyable types

Delete copy operations when an object represents exclusive ownership or identity:

```cpp
class DeviceSession {
public:
    DeviceSession(const DeviceSession&) = delete;
    DeviceSession& operator=(const DeviceSession&) = delete;

    DeviceSession(DeviceSession&&) noexcept = default;
    DeviceSession& operator=(DeviceSession&&) noexcept = default;
};
```

Common non-copyable types include:

- `std::unique_ptr`.
- `std::mutex`.
- `std::thread` and `std::jthread` in relevant respects.
- Unique OS handles.
- Exclusive hardware registrations.
- Objects whose address is part of an external invariant.

### Why not hide copy operations privately?

Old code used private undeclared functions. `= delete` is clearer, provides better diagnostics, and makes the intent visible to type traits and templates.

### Interview question

**Question:** When should a class be move-only?

**Answer:** When ownership can be transferred safely but duplicating the represented resource or identity has no valid meaning.

---

## 11. Rule of Zero

Prefer composing resource-managing members:

```cpp
class Buffer {
public:
    explicit Buffer(std::size_t size)
        : data_(size) {}

    int& operator[](std::size_t index) {
        return data_[index];
    }

    const int& operator[](std::size_t index) const {
        return data_[index];
    }

private:
    std::vector<int> data_;
};
```

No destructor, copy constructor, copy assignment, move constructor, or move assignment is needed.

`std::vector` already supplies:

- Destruction.
- Deep copying.
- Efficient moving.
- Exception-safe assignment.
- Size tracking.

### Rule of Zero benefit

Fewer handwritten special members mean:

- Fewer ownership bugs.
- Better exception safety.
- Easier maintenance.
- Correct behavior when new members are added.
- Better compatibility with standard containers.

### Pimpl nuance

A class owning an incomplete implementation through `std::unique_ptr<Impl>` may need an out-of-line destructor where `Impl` is complete:

```cpp
class Widget {
public:
    Widget();
    ~Widget();

private:
    class Impl;
    std::unique_ptr<Impl> impl_;
};
```

This is still RAII design, even though a destructor declaration is needed for completeness/ABI structure.

### Interview question

**Question:** State the Rule of Zero.

**Answer:** Design classes from members that already manage their resources correctly so the class needs no custom special member functions.

---

## 12. Rule of Three, Five, and Zero

### Rule of Three

Manual resource management in pre-move C++ often requires:

```cpp
~T();
T(const T&);
T& operator=(const T&);
```

### Rule of Five

Modern C++ adds:

```cpp
T(T&&) noexcept;
T& operator=(T&&) noexcept;
```

A manual resource owner should consider all five operations.

### Rule of Zero

Prefer needing none by composing standard RAII types.

### These are design heuristics, not compiler laws

Defining one function does not mechanically mean every other one must be handwritten. It means the ownership design requires deliberate review of the full set.

For example, a polymorphic base may need only:

```cpp
virtual ~Base() = default;
```

and explicitly defaulted copy/move behavior may or may not fit its intended semantics.

### Interview question

**Question:** Why is Rule of Zero preferred over Rule of Five?

**Answer:** Correct resource semantics are delegated to tested member types, avoiding repetitive manual ownership and exception-safety code.

---

## 13. Move interaction

A move operation transfers state from an object that is about to be discarded or explicitly treated as movable:

```cpp
Buffer destination = std::move(source);
```

`std::move` is a cast that allows move overloads to be selected; it does not itself transfer anything.

A user-declared destructor prevents implicit move generation in common cases. The same object may then fall back to copying if a copy operation is available, sometimes unexpectedly.

### Default moves with owning raw pointers

Blindly defaulting move operations for a raw owning pointer is unsafe:

```cpp
Buffer(Buffer&&) = default; // copies pointer bits; source still owns it
```

Both objects would still delete the address. A manual move must empty the source, or better, ownership should use `std::unique_ptr`/`std::vector`.

### `noexcept`

Standard containers prefer moving during reallocation when a move constructor is `noexcept`; otherwise they may copy to preserve exception guarantees.

### Interview question

**Question:** Why should a well-behaved move constructor often be `noexcept`?

**Answer:** It enables containers to move elements during reallocation while maintaining their exception guarantees.

---

## 14. Inheritance, slicing, and cloning

Copying by base value slices derived state:

```cpp
Derived derived;
Base base = derived;
```

Only the `Base` subobject is copied into `base`.

Polymorphic objects are normally handled through references or pointers:

```cpp
void process(const Base& object);
```

If an independent polymorphic copy is required, use a virtual clone pattern:

```cpp
class Base {
public:
    virtual ~Base() = default;
    virtual std::unique_ptr<Base> clone() const = 0;
};

class Derived : public Base {
public:
    std::unique_ptr<Base> clone() const override {
        return std::make_unique<Derived>(*this);
    }
};
```

### Tradeoff

Cloning supports value-like polymorphism but requires each derived type to implement correct copying. Sometimes a non-polymorphic value type or type-erasure wrapper is cleaner.

### Interview question

**Question:** What is object slicing?

**Answer:** Copying a derived object into a base object by value copies only the base subobject and discards the derived-specific portion.

---

## 15. Containers and copying cost

```cpp
std::vector<LargeObject> destination = source;
```

This generally copies every element and allocates destination storage. Complexity is linear in the number of elements plus each element's copy cost.

Prefer references when only observing:

```cpp
void inspect(const std::vector<LargeObject>& objects);
```

Copy deliberately when the function needs independent state.

### Accidental copies

```cpp
for (auto object : objects) { // copies each element
}
```

Use:

```cpp
for (const auto& object : objects) {
}
```

when read-only borrowing is intended.

Lambda capture can also copy:

```cpp
auto task = [configuration] {
    // captured by value
};
```

This may be desirable for lifetime independence or expensive accidentally.

### Interview question

**Question:** What common range-for syntax accidentally copies every element?

**Answer:** `for (auto element : container)`. Use `const auto&` for read-only borrowing or `auto&` for mutation.

---

## 16. Copy elision and performance

Modern C++ can avoid constructing intermediate copies.

### Guaranteed elision since C++17

```cpp
Widget make_widget() {
    return Widget{};
}

Widget widget = make_widget();
```

The result can be constructed directly in `widget`'s storage under guaranteed prvalue rules.

### Named return value optimization

```cpp
Widget make_widget() {
    Widget result;
    return result;
}
```

NRVO is permitted but not guaranteed in all cases. Adding `std::move(result)` can prevent NRVO and is usually a mistake.

### Lvalue copy remains conceptually a copy

```cpp
Widget a;
Widget b = a;
```

`a` is an lvalue. This selects copy construction; it is not one of the normal guaranteed-elision cases.

### Measure before optimizing

A correct value-semantic interface with compiler optimization is often clearer and faster than a complicated out-parameter design.

### Interview question

**Question:** Should you write `return std::move(local);`?

**Answer:** Usually no. Returning a named local already enables NRVO and fallback move rules; explicit `std::move` can inhibit NRVO.

---

## 17. Embedded and real-time tradeoffs

Copying can affect:

- Worst-case execution time.
- Stack usage.
- Heap allocation.
- Bus or memory bandwidth.
- Interrupt latency.
- Determinism.

A `std::vector` deep copy may allocate, which can be unacceptable on a real-time path. Alternatives include:

- Fixed-capacity value types.
- `std::array`.
- Preallocated object pools.
- Non-owning `std::span` for synchronous borrowing.
- Move-only ownership transfer.
- Reference-counted immutable buffers, if atomic overhead is acceptable.
- Explicit caller-provided output storage.

### Beware hidden copies

Pass-by-value, range loops, lambda captures, `std::function`, container insertion, and message queues can copy unexpectedly.

Compile-time deletion can enforce a policy:

```cpp
Frame(const Frame&) = delete;
Frame& operator=(const Frame&) = delete;
```

### Interview question

**Question:** Why might a valid deep copy still be unacceptable in real-time code?

**Answer:** It may allocate or have data-size-dependent latency, harming determinism and worst-case timing.

---

## 18. Common mistakes

### Thinking missing user code means no copy

The compiler may generate copy operations.

### Defining a destructor but ignoring copy

Manual ownership plus memberwise copy often creates double deletion.

### Copying an owning pointer address

This is shallow ownership duplication, not a deep copy.

### Deleting old state before acquiring new state

Failure can corrupt the target's invariant.

### Forgetting self-assignment

A naive resource replacement may read freed data.

### Returning the wrong type from assignment

Use `T&` and return `*this`.

### Defaulting raw-pointer moves

The source may remain an owner of the same address.

### Copying polymorphic objects by base value

This slices derived state.

### Adding `std::move` to a returned local

It may disable NRVO.

---

## 19. Design workflow

For every class, ask:

1. Does it represent a value or an identity?
2. Does it own any resource?
3. Do member types already express ownership correctly?
4. What should copy construction mean?
5. What should copy assignment do to existing state?
6. Should copying be deleted?
7. Is moving safe and useful?
8. What exception guarantee is required?
9. Can copying allocate or block?
10. Are polymorphism and slicing relevant?
11. Is shared ownership genuinely required?
12. Can Rule of Zero replace manual code?

### Interview question

**Question:** How do you review a class for safe copy behavior?

**Answer:** Identify every owned and borrowed resource, define value/identity semantics, inspect generated memberwise behavior, and then choose default, deep copy, sharing, moving, or deletion explicitly.

---

## Final interview checklist

You should be able to explain:

- Copy construction versus copy assignment.
- Why `Foo b = a` is construction.
- Why copy constructors take `const T&`.
- Compiler-generated memberwise copying.
- When pointer copying is correct or dangerous.
- Shallow versus deep copying.
- Full Rule-of-Three resource management.
- Self-assignment and exception guarantees.
- Copy-and-swap tradeoffs.
- Non-copyable and move-only types.
- Rule of Three, Five, and Zero.
- Raw-pointer move hazards.
- Object slicing and virtual cloning.
- Container, lambda, and range-loop copies.
- Guaranteed copy elision and NRVO.
- Real-time costs of copying.
