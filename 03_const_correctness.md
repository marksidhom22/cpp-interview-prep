# C++ Const Correctness: API Design and Practical Use

This chapter builds on the syntax in [`02_cpp_const_brief_interview_notes.md`](./02_cpp_const_brief_interview_notes.md). The focus here is not how to spell const declarations, but how to design an entire class or API so mutation permissions remain consistent and useful.

---

## Part I - Five-Minute Interview Review

### What const correctness means

Const correctness is the consistent use of `const` to express and enforce:

- Which objects may be modified.
- Which functions promise read-only access.
- Which callers may use an operation.
- Whether returned access is mutable or read-only.
- How mutation permissions propagate through an API.

```cpp
void inspect(const Frame& frame); // required, borrowed, read-only
void normalize(Frame& frame);     // required, borrowed, mutable
```

See [Const correctness is an API property](#1-const-correctness-is-an-api-property).

### Mandatory class pattern

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

- A mutable object selects the mutable overload.
- A const object can select only the const overload.
- The object's constness selects the overload, not whether the result is later read or written.
- Return types alone cannot distinguish overloads.

See [Const and non-const overloads](#5-const-and-non-const-overloads).

### High-frequency design rules

- Mark every logically read-only member function `const`. See [Designing const member functions](#3-designing-const-member-functions).
- Return `const T&` from a const accessor and `T&` from a non-const accessor when exposing direct access is appropriate. See [Accessor design](#6-accessor-design).
- Const is normally shallow: a const object containing a pointer may still mutate the pointed-to object. See [Shallow const and pointer members](#7-shallow-const-and-pointer-members).
- A const container provides const access to its elements; a const smart pointer usually makes the pointer handle const, not necessarily the pointee. See [Containers, iterators, and smart pointers](#10-containers-iterators-and-smart-pointers).
- Use `mutable` only for logically invisible implementation state, such as a cache or mutex. See [Logical constness](#8-logical-constness).
- Const correctness must propagate: a const member function can normally call only other const member functions. See [Const propagation](#9-const-propagation).
- Const correctness is not thread safety or deep immutability. See [Concurrency](#13-const-correctness-and-concurrency).

### Five interview checks

1. **Why is `value() const` useful?** It can be called on both const and mutable objects and promises not to mutate ordinary direct state.
2. **Why provide two `operator[]` overloads?** Mutable objects need `T&`; const objects must receive `const T&`.
3. **Can overloads differ only by return type?** No.
4. **Does a const method prevent mutation through a pointer member?** Not automatically; const is shallow.
5. **Does const mean thread-safe?** No; synchronization is a separate contract.

---

## Part II - Detailed Reference

## 1. Const correctness is an API property

A single const declaration is syntax. Const correctness is a design property across declarations, definitions, call chains, and returned access.

```cpp
class ImageProcessor {
public:
    ImageProcessor(const Calibration& calibration)
        : calibration_{calibration} {}

    Result process(const Frame& frame) const;

private:
    const Calibration& calibration_;
};
```

This interface communicates:

- The processor borrows calibration rather than owning it.
- Calibration is required because it is a reference.
- Calibration is read-only through the processor.
- Processing accepts a required read-only frame.
- `process` does not logically mutate the processor.
- The result is returned as a new value owned by the caller.

If one helper is missing a const qualifier, the whole call chain may become unusable from a const object:

```cpp
class ImageProcessor {
public:
    Result process(const Frame& frame) const {
        return validate(frame); // validate must also be const
    }

private:
    Result validate(const Frame& frame) const;
};
```

### Tradeoff

A very restrictive interface can be awkward if mutation is genuinely required. The goal is not to add const everywhere mechanically; it is to grant exactly the mutation each operation needs.

### Interview question

**Question:** What is const correctness?

**Answer:** It is the consistent design of types and APIs so read-only and mutable access are accurately expressed and enforced throughout the call graph.

---

## 2. Designing parameter contracts

Parameter types should answer four questions:

1. Is an argument required?
2. May the function modify it?
3. Does the function own it?
4. Is copying intended?

### Common contracts

```cpp
void set_retry_count(int count);             // small value
void inspect(const Packet& packet);          // required, read-only borrow
void repair(Packet& packet);                 // required, mutable borrow
void inspect_if_present(const Packet* packet); // optional, read-only borrow
void take(std::unique_ptr<Packet> packet);    // ownership transfer
```

`const Packet&` says that an object is required in ordinary use because references do not represent an empty state. It makes no copy and denies mutation through that reference.

### Output parameters

A mutable reference can express an output:

```cpp
bool decode(const Bytes& input, Packet& output);
```

However, a returned object often composes better:

```cpp
std::optional<Packet> decode(const Bytes& input);
```

Use an output reference when it fits performance, ABI, embedded allocation, or multi-output constraints. Use a return value when it produces a clearer ownership and error model.

### Small types

This is normally preferable:

```cpp
void set_channel(int channel);
```

to:

```cpp
void set_channel(const int& channel);
```

The reference adds indirection and lifetime coupling without avoiding meaningful work.

### Interview question

**Question:** When would you use `const T*` instead of `const T&`?

**Answer:** When absence is a valid state that the interface represents with `nullptr`, or when pointer semantics are otherwise natural.

---

## 3. Designing const member functions

A member function that does not logically modify the object should normally be const:

```cpp
class Sensor {
public:
    int value() const {
        return value_;
    }

    bool healthy() const {
        return error_count_ == 0;
    }

    void reset() {
        value_ = 0;
        error_count_ = 0;
    }

private:
    int value_{};
    unsigned error_count_{};
};
```

Usage:

```cpp
const Sensor sensor;
int value = sensor.value(); // valid
// sensor.reset();          // error
```

The trailing const applies to the implicit object parameter. Conceptually:

```cpp
int value(const Sensor& self);
void reset(Sensor& self);
```

### Why getters should be const

A getter without trailing const cannot be called through:

- A const object.
- A const reference.
- A pointer-to-const.
- A const container element.

Missing one qualifier can make a large read-only API unusable.

### What a const member may do

It may:

- Read ordinary members.
- Call other const member functions.
- Modify local variables.
- Modify `mutable` members.
- Read or even mutate external objects through pointer/reference members if their types permit it.
- Perform I/O.

So trailing const is a type-system restriction, not a guarantee of purity.

### Interview question

**Question:** What exactly does the trailing const on a member function change?

**Answer:** It treats the implicit object parameter as const, preventing ordinary direct member mutation and allowing the function to be called on const objects.

---

## 4. The implicit object and overload resolution

For an ordinary member function:

```cpp
class Counter {
public:
    int value() const;
    void increment();
};
```

a useful conceptual model is:

```cpp
int value(const Counter& self);
void increment(Counter& self);
```

This model explains why:

```cpp
const Counter counter;
// counter.increment(); // cannot bind const Counter to mutable Counter&
counter.value();        // can bind to const Counter&
```

It also explains overload resolution:

```cpp
void inspect();
void inspect() const;
```

A mutable object can call either in principle, but the non-const version is a better match because it does not add const qualification. A const object can call only the const version.

### Ref-qualified member functions

Advanced APIs may also distinguish lvalue and rvalue objects:

```cpp
class Payload {
public:
    const std::string& data() const & {
        return data_;
    }

    std::string data() && {
        return std::move(data_);
    }

private:
    std::string data_;
};
```

The first safely borrows from an lvalue. The second moves data out of a temporary/rvalue object.

### Interview question

**Question:** Why is a non-const member overload preferred for a non-const object?

**Answer:** Its implicit object parameter is a better qualification match; converting mutable access to const access is valid but not the best available match.

---

## 5. Const and non-const overloads

The standard pattern is:

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

### Mutable object

```cpp
Buffer writable;
writable[3] = 42;
int x = writable[3];
```

Both expressions select:

```cpp
int& operator[](std::size_t index);
```

The compiler chooses the overload before considering what later happens to the returned reference. Reading the result does not cause selection of the const overload.

### Const object

```cpp
const Buffer read_only;
int x = read_only[3];
// read_only[3] = 42; // error
```

This selects:

```cpp
const int& operator[](std::size_t index) const;
```

### Why the return types match the object

Returning `int&` from the mutable overload allows callers to mutate the actual element. Returning `const int&` from the const overload prevents a const object from leaking mutable access to its internals.

This would violate const correctness:

```cpp
int& operator[](std::size_t index) const; // normally ill-formed
```

Inside the const function, `data_[index]` behaves as a const lvalue, so it cannot bind to `int&`.

### Return types do not create overloads

These conflict:

```cpp
int& operator[](std::size_t index);
const int& operator[](std::size_t index);
```

Overload resolution cannot use the desired return type because many expressions ignore a return value or provide no unique expected type.

### Bounds tradeoff

`operator[]` conventionally provides unchecked access, as with standard containers. A checked operation can be separate:

```cpp
int& at(std::size_t index) {
    if (index >= 10) {
        throw std::out_of_range{"Buffer index"};
    }
    return data_[index];
}
```

In exception-free embedded code, the checked API might return a pointer, `std::optional<std::reference_wrapper<int>>`, an error code, or use a precondition/assertion.

### Interview question

**Question:** Which overload handles `int x = writable[3]`, and why?

**Answer:** The non-const overload, because `writable` is non-const. The result is an `int&`, whose value is then copied into `x`.

---

## 6. Accessor design

A paired accessor can preserve constness:

```cpp
class Device {
public:
    Configuration& configuration() {
        return configuration_;
    }

    const Configuration& configuration() const {
        return configuration_;
    }

private:
    Configuration configuration_;
};
```

### Benefits

- No copy of a potentially large object.
- Mutable callers can modify it.
- Const callers receive only read-only access.
- The compiler propagates constness.

### Costs

Returning a reference exposes internal representation and couples callers to the member's lifetime. It can also make invariants difficult to protect:

```cpp
device.configuration().set_invalid_combination();
```

A narrower interface may be better:

```cpp
class Device {
public:
    int sample_rate() const;
    bool set_sample_rate(int rate);
};
```

### Return by value

For a small or identity-independent value, return by value:

```cpp
int id() const {
    return id_;
}
```

Returning `const int&` would add lifetime coupling for no meaningful performance benefit.

### Interview question

**Question:** When should an accessor return by value instead of `const T&`?

**Answer:** For small cheap values, computed results, or whenever exposing a reference would unnecessarily reveal representation or couple lifetimes.

---

## 7. Shallow const and pointer members

C++ const is normally shallow.

```cpp
class Controller {
public:
    explicit Controller(Device* device)
        : device_{device} {}

    void emergency_stop() const {
        device_->stop(); // may mutate the Device
    }

private:
    Device* device_;
};
```

The const member function cannot reseat `device_` because the pointer member itself is part of the const `Controller`. But it may mutate the separate `Device` object because the pointer type is `Device*`.

To provide read-only pointed-to access:

```cpp
const Device* device_;
```

Now `device_` points to const `Device`.

### Reference members

A reference member behaves similarly:

```cpp
class Monitor {
public:
    explicit Monitor(Device& device) : device_{device} {}

    void poll() const {
        device_.refresh(); // possible if refresh is non-const
    }

private:
    Device& device_;
};
```

The reference cannot be reseated anyway; constness of `Monitor` does not automatically add const to the referenced `Device`.

### Deep const

Some designs need constness to propagate through an owning handle. Standard pointers do not provide deep const automatically. You may expose different view types or design operations so mutation remains controlled.

### Interview question

**Question:** Can a const object mutate something through a `T*` member?

**Answer:** Yes. The pointer member cannot be reseated through the const object, but the separate pointed-to `T` remains mutable unless its type is `const T*`.

---

## 8. Logical constness

Logical constness means an operation does not change the abstract value users observe, even if implementation details change.

### Cache example

```cpp
class Frame {
public:
    std::uint32_t checksum() const {
        if (!checksum_valid_) {
            checksum_ = calculate_checksum();
            checksum_valid_ = true;
        }
        return checksum_;
    }

private:
    std::uint32_t calculate_checksum() const;

    mutable bool checksum_valid_{false};
    mutable std::uint32_t checksum_{};
};
```

Caching does not change the frame's logical content.

### Mutex example

```cpp
class Registry {
public:
    std::optional<Device> find(int id) const {
        std::lock_guard lock{mutex_};
        // search devices_
    }

private:
    mutable std::mutex mutex_;
    std::vector<Device> devices_;
};
```

Locking changes mutex state but is necessary to implement a logically read-only query.

### Misuse

This is misleading:

```cpp
class Account {
public:
    void withdraw(int amount) const {
        balance_ -= amount;
    }

private:
    mutable int balance_{};
};
```

Balance is meaningful state. The operation should be non-const.

### Interview question

**Question:** What test should you apply before using `mutable`?

**Answer:** Ask whether changing the member alters the object's externally meaningful value. If it does, the operation should generally be non-const.

---

## 9. Const propagation

Const correctness is contagious in a useful way.

```cpp
class Pipeline {
public:
    Report inspect() const {
        return build_report();
    }

private:
    Report build_report() const {
        return collect_metrics();
    }

    Metrics collect_metrics() const;
};
```

Every operation in the read-only call chain must support const access.

If a helper lacks const:

```cpp
Metrics collect_metrics(); // missing const
```

then a const caller cannot use it, even if the implementation happens not to mutate anything.

### Propagating through parameters

```cpp
void render(const Scene& scene) {
    for (const Object& object : scene.objects()) {
        object.draw();
    }
}
```

For this to work cleanly:

- `Scene::objects()` needs a const overload.
- A const container must yield const elements.
- `Object::draw()` should be const if drawing does not change logical object state.

### Design benefit

The compiler reveals accidental mutation paths. Fixing the first missing const often uncovers other interfaces that did not accurately express read-only behavior.

### Interview question

**Question:** Why is const correctness sometimes described as contagious?

**Answer:** A const operation can call only interfaces that preserve its read-only contract, so const support must propagate through helpers, accessors, and nested types.

---

## 10. Containers, iterators, and smart pointers

### Const containers

```cpp
const std::vector<int> values{1, 2, 3};

int x = values[0];
// values[0] = 10; // error
```

A const vector provides const access to its elements and cannot change its size or capacity.

Iterator types reflect this:

```cpp
std::vector<int>::iterator mutable_it;
std::vector<int>::const_iterator read_only_it;
```

`cbegin()` and `cend()` explicitly request const iteration:

```cpp
for (auto it = values.cbegin(); it != values.cend(); ++it) {
    // *it is const int&
}
```

`std::as_const` can request a const view of a mutable object:

```cpp
for (const auto& value : std::as_const(values)) {
    // read-only access
}
```

### Const smart pointer versus pointer to const

```cpp
const std::unique_ptr<Device> owner = std::make_unique<Device>();
owner->reset(); // allowed if Device::reset is non-const
```

The `unique_ptr` handle cannot be moved or reset, but its pointee is still mutable.

To make the pointee read-only through the handle:

```cpp
std::unique_ptr<const Device> owner;
```

The same distinction exists with `shared_ptr`.

### `std::span`

```cpp
std::span<int> writable;
std::span<const int> read_only;
```

A `const std::span<int>` prevents changing the span descriptor but still yields mutable `int` elements. `std::span<const int>` provides read-only element access.

### Interview question

**Question:** Does `const std::unique_ptr<T>` mean the `T` is const?

**Answer:** No. It makes the smart-pointer object const. Use `std::unique_ptr<const T>` for read-only pointee access.

---

## 11. Views and borrowed data

Non-owning views make const and lifetime reasoning important:

```cpp
void parse(std::string_view text);
void transmit(std::span<const std::byte> bytes);
```

These types:

- Do not own their data.
- Provide read-only element access in these declarations.
- Usually copy cheaply.
- Can dangle if the underlying storage dies or reallocates.

### Const does not fix lifetime

```cpp
std::string_view bad() {
    std::string local = "message";
    return local; // dangling view
}
```

The view is read-only, but its data no longer exists.

### Tradeoff

Views avoid copies and express ranges better than pointer-plus-size pairs. They require disciplined lifetime management and may not be appropriate when the callee needs to retain the data.

### Interview question

**Question:** What guarantee does `std::span<const T>` provide that `const T*` alone does not?

**Answer:** It carries the element count along with read-only borrowed access, though neither type owns or extends the data's lifetime.

---

## 12. Const-correct interfaces and ownership

Constness and ownership are independent:

```cpp
void inspect(const Device& device);               // borrowed, required
void inspect(const Device* device);               // borrowed, optional
void take(std::unique_ptr<Device> device);         // exclusive ownership transfer
void share(std::shared_ptr<const Device> device);  // shared ownership, read-only access
```

A reference or raw pointer generally does not express lifetime ownership in modern C++.

### Returning internal state

```cpp
const Device& primary() const;
```

This borrows from the containing object. The reference becomes invalid when the container dies or replaces that element.

Returning a `shared_ptr<const Device>` extends shared lifetime but adds reference-counting cost and changes ownership semantics. Do not use shared ownership merely to avoid thinking about lifetime.

### Interview question

**Question:** Does `const T&` mean the function owns or extends the lifetime of `T`?

**Answer:** No. It is a borrowed access path. The caller must ensure the object remains alive for the use.

---

## 13. Const correctness and concurrency

Consider:

```cpp
class Queue {
public:
    std::size_t size() const {
        return values_.size();
    }

    void push(int value) {
        values_.push_back(value);
    }

private:
    std::vector<int> values_;
};
```

`size()` being const does not make this safe:

```text
Thread A: queue.size()
Thread B: queue.push(42)
```

Concurrent unsynchronized access can still be a data race.

A thread-safe interface must use mutexes, atomics, immutability, confinement, or another synchronization strategy.

### Stronger design idea

A truly immutable object can often be shared safely for reading after publication, provided its construction and publication are synchronized correctly. Ordinary const access to an otherwise mutable object is not the same guarantee.

### Interview question

**Question:** Can two threads safely call const member functions simultaneously?

**Answer:** Only if those operations and all shared state they access are designed for concurrent use. The const qualifier alone is insufficient.

---

## 14. Const correctness in embedded systems

Const can improve intent and placement:

```cpp
constexpr std::array<std::uint16_t, 4> thresholds{
    100, 200, 300, 400
};
```

Read-only tables may be eligible for placement in read-only memory, depending on the implementation and linker configuration.

Memory-mapped I/O requires separate `volatile` reasoning:

```cpp
volatile const std::uint32_t* status_register;
volatile std::uint32_t* control_register;
```

- Status is software-read-only but hardware may change it.
- Control is software-writable and accesses must occur.
- Neither declaration creates atomic multi-thread synchronization.

### Callback and HAL APIs

```cpp
class RegisterBank {
public:
    std::uint32_t status() const;
    void write_control(std::uint32_t value);
};
```

A const-qualified HAL query accurately communicates object-level intent even if the underlying volatile hardware changes independently.

### Interview question

**Question:** Why might a register pointer be both `volatile` and `const`?

**Answer:** `volatile` preserves actual reads because hardware may update the register; `const` prevents software writes through that pointer.

---

## 15. Common design failures

### Missing const on read-only members

```cpp
int id(); // blocks use through const objects
```

### Leaking mutable access from const object

Using casts or mutable pointers to return writable internal state undermines the contract.

### Overusing `const T&`

Small scalar inputs are clearer by value.

### Returning references without lifetime documentation

Read-only access can still dangle.

### Treating const as synchronization

Const and thread safety solve different problems.

### Overusing `mutable`

If callers would observe the state change as a semantic mutation, the operation should not be const.

### Making every data member const

This can make the type non-assignable without improving the public invariant. Prefer encapsulation unless per-member constness is specifically required.

---

## 16. Design workflow

When reviewing an API, ask:

1. Does this operation logically change the object?
2. Can this member function be const?
3. Should the input be a value, reference, pointer, or ownership type?
4. Is absence meaningful?
5. Does returned access expose mutation?
6. Could returned access outlive its source?
7. Is constness shallow through a pointer-like member?
8. Does this code need synchronization separately?
9. Is `mutable` preserving logical constness or hiding mutation?
10. Do embedded `volatile` requirements apply independently?

### Interview question

**Question:** How would you make an existing class const-correct?

**Answer:** Mark logically read-only operations const, add const-preserving accessors and overloads, correct parameter and return types, then follow compiler errors through the call graph while reviewing lifetime and ownership contracts.

---

## Final interview checklist

You should be able to explain:

- Const correctness as an API-wide property.
- Required versus optional read-only parameters.
- The implicit object parameter.
- Why mutable and const overloads are distinct.
- Why overload selection depends on the object, not result usage.
- Why return type alone cannot overload.
- Shallow const through pointers, references, and smart pointers.
- Const containers, iterators, spans, and views.
- Logical constness and responsible `mutable`.
- Const propagation through helper calls.
- Lifetime and ownership independent of constness.
- Why const does not guarantee thread safety.
