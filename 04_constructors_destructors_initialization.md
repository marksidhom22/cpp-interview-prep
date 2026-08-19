# C++ Constructors, Destructors, and Initialization

Construction establishes a valid object in storage. Destruction ends that object's lifetime and releases the resources it owns. This chapter connects syntax to the object-lifetime model used in systems and embedded interviews.

---

## Part I - Five-Minute Interview Review

### Mandatory mental model

```text
Obtain storage
    -> initialize base-class subobjects
    -> initialize data members
    -> execute constructor body
    -> use the complete object
    -> execute destructor body
    -> destroy data members in reverse order
    -> destroy base classes in reverse order
    -> release storage when applicable
```

- Allocation obtains bytes; construction creates a live class object in storage. They are related but distinct. See [Storage, initialization, and construction](#1-storage-initialization-and-construction).
- Members are initialized before the constructor body. Assignment inside the body changes objects that already exist. See [Member initializer lists](#4-member-initializer-lists).
- Base classes are constructed before derived-class members and the derived constructor body. See [Base-class construction](#5-base-class-construction).
- Actual initialization order is base classes first, then members in declaration order, regardless of initializer-list order. See [Initialization order](#6-initialization-order).
- In-class default member initializers provide defaults that a constructor may override. See [Default member initializers](#7-default-member-initializers).
- Use `explicit` for constructors that should not define implicit conversions. See [Converting constructors](#10-converting-constructors-and-explicit).
- A destructor performs cleanup automatically at lifetime end; RAII ties resource release to that event. See [Destructors and RAII](#12-destructors-and-raii).
- A polymorphic base intended for deletion through a base pointer normally needs a virtual destructor. See [Virtual destructors](#14-virtual-destructors).
- If construction throws, already-constructed bases and members are destroyed automatically; the incomplete object's destructor is not called. See [Exceptions during construction](#15-exceptions-during-construction).
- Avoid calling virtual functions from constructors or destructors when expecting derived dispatch. See [Virtual dispatch during construction and destruction](#16-virtual-dispatch-during-construction-and-destruction).

### Core syntax

```cpp
class Device {
public:
    Device() = default;

    explicit Device(int id, std::string name)
        : id_{id},
          name_{std::move(name)} {}

    ~Device() = default;

private:
    int id_{};
    std::string name_;
};
```

### High-frequency initialization forms

| Code | Meaning |
|---|---|
| `Widget w;` | Default-initialization |
| `Widget w{};` | Value/list-initialization; often safest default spelling |
| `Widget w(args);` | Direct-initialization |
| `Widget w{args};` | Direct-list-initialization |
| `Widget w = other;` | Copy-initialization; not assignment |
| `w = other;` | Assignment to an existing object |

See [Initialization forms](#2-initialization-forms).

### Five interview checks

1. **Does a constructor allocate memory?** Not necessarily. Storage exists before the constructor initializes an object in it.
2. **Why prefer an initializer list?** It directly initializes members and is required for references, const members, bases, and members without suitable default constructors.
3. **What determines member initialization order?** Declaration order in the class, not textual order in the initializer list.
4. **When does a destructor run?** At the end of the object's lifetime: scope exit, owning deletion, container destruction, exception unwinding, and similar events.
5. **Can a constructor be virtual?** No. Destructors can be virtual.

---

## Part II - Detailed Reference

## 1. Storage, initialization, and construction

These terms describe different parts of an object's life.

| Term | Meaning |
|---|---|
| Storage | Bytes with sufficient size and alignment |
| Allocation | Obtaining storage |
| Initialization | Giving an object or subobject its initial state |
| Construction | Establishing a live class object, including base/member initialization and constructor execution |
| Assignment | Replacing state of an object that already exists |
| Destruction | Ending a class object's lifetime and running cleanup |
| Deallocation | Returning storage |

Consider:

```cpp
Device device{42};
```

For an automatic object, the implementation reserves storage, initializes the object's bases and members, and executes the constructor. It later runs the destructor at scope exit. The compiler may optimize the machine instructions, but these language-level effects must be preserved.

Dynamic construction combines allocation and construction:

```cpp
Device* device = new Device{42};
```

The `new` expression conceptually:

1. Calls an allocation function to obtain storage.
2. Constructs `Device` in that storage.
3. Produces a pointer to the object.

`delete device` conceptually destroys the object and then deallocates its storage.

Modern code usually represents exclusive dynamic ownership with:

```cpp
auto device = std::make_unique<Device>(42);
```

### Construction does not always emit a function call

For trivial types, construction may amount to simple stores or no instructions. "Construct" is an object-model term; it does not promise a literal runtime call.

### Interview question

**Question:** What is the difference between allocation and construction?

**Answer:** Allocation obtains raw storage. Construction establishes a live object in that storage by initializing its subobjects and executing its constructor when required.

---

## 2. Initialization forms

C++ has several initialization syntaxes whose differences matter.

### Default-initialization

```cpp
Widget widget;
```

For a class, this invokes a default constructor. For a local built-in scalar with no initializer:

```cpp
int value; // indeterminate
```

Reading the indeterminate value is invalid.

### Value-initialization

```cpp
Widget widget{};
int value{}; // zero
```

Braces are a reliable way to request initialization. For scalar types, `{}` produces zero initialization.

### Direct-initialization

```cpp
Widget widget(argument);
Widget widget2{argument};
```

The constructor is selected directly. Braces additionally reject narrowing conversions in list-initialization:

```cpp
int x{3.5}; // error: narrowing
```

### Copy-initialization

```cpp
Widget copy = original;
```

Despite the `=`, this initializes a new object. It is not assignment.

```cpp
Widget copy;
copy = original; // assignment
```

Copy-initialization does not use explicit converting constructors, whereas direct-initialization can.

### Aggregate initialization

An aggregate can initialize public members directly:

```cpp
struct Point {
    int x;
    int y;
};

Point point{10, 20};
```

Adding private members, certain constructors, base conditions, or virtual functions can change aggregate status; exact rules depend on the C++ standard version.

### `auto` and initializer lists

```cpp
auto a = 1;   // int
auto b{1};    // int
auto c = {1}; // std::initializer_list<int>
```

Brace deduction has special cases. Do not assume all visually similar forms have the same type.

### Interview question

**Question:** What is the difference between `Foo b = a;` and `b = a;`?

**Answer:** The first declares and copy-initializes a new `Foo`; the second copy-assigns an already-existing object.

---

## 3. Constructor fundamentals

A constructor:

- Has the class name.
- Has no return type.
- Establishes the class invariant.
- Runs automatically during class-object initialization.
- May be overloaded.
- Cannot be `virtual`, `static`, `const`, or a coroutine.
- May be defaulted or deleted.

```cpp
class Connection {
public:
    Connection();
    explicit Connection(int port);
    Connection(std::string host, int port);
};
```

### Default constructor

A default constructor can be called with no arguments:

```cpp
Connection connection;
```

It may be compiler-generated if the class declares no constructor and its members/bases permit it.

Once you declare another constructor, the compiler does not automatically add a no-argument constructor:

```cpp
class Device {
public:
    explicit Device(int id);
};

// Device device; // error: no default constructor
```

Add it intentionally if it makes sense:

```cpp
Device() = default;
```

### Establish invariants

A constructor should leave the object ready for every public operation:

```cpp
class Range {
public:
    Range(int low, int high)
        : low_{low},
          high_{high} {
        if (low_ > high_) {
            throw std::invalid_argument{"invalid range"};
        }
    }

private:
    int low_;
    int high_;
};
```

In exception-free embedded code, invalid construction may instead be prevented with factories, error-return types, assertions, or validated inputs.

### Interview question

**Question:** When does the compiler generate a default constructor?

**Answer:** Generally when no user-declared constructor prevents implicit declaration and all bases and members can be default-constructed. A declared non-default constructor means you must request a default constructor explicitly if desired.

---

## 4. Member initializer lists

```cpp
class Device {
public:
    Device(int id, std::string name)
        : id_{id},
          name_{std::move(name)} {}

private:
    int id_;
    std::string name_;
};
```

The initializer list appears after the constructor parameter list and before the body.

### Direct initialization versus assignment

Initializer list:

```cpp
Device(const std::string& name)
    : name_{name} {}
```

`name_` is copy-constructed directly.

Constructor-body assignment:

```cpp
Device(const std::string& name) {
    name_ = name;
}
```

Before the body, `name_` has already been default-constructed as an empty string. The body then copy-assigns it.

For an `int` without a default member initializer, omission leaves it indeterminate before a later body assignment. For class members, omission invokes their default construction if possible.

### Required uses

Initializer lists are required to select construction for:

```cpp
const int id_;
Driver& driver_;
NoDefaultConstructor component_;
```

They are also where base-class constructors and delegating constructors are selected.

### Braces or parentheses

Both may initialize members:

```cpp
: id_(id), name_(name)
: id_{id}, name_{name}
```

Braces are popular because they reject narrowing, but `std::initializer_list` constructor preference can make brace behavior surprising for some types such as `std::vector`.

### Interview question

**Question:** Why is assignment in the constructor body not equivalent to member initialization?

**Answer:** Members already exist before the body. Body assignment changes an already-initialized member; an initializer list chooses how that member is constructed initially.

---

## 5. Base-class construction

```cpp
class Device {
public:
    explicit Device(int id)
        : id_{id} {}

private:
    int id_;
};

class Sensor : public Device {
public:
    Sensor(int id, int channel)
        : Device{id},
          channel_{channel} {}

private:
    int channel_;
};
```

Constructing:

```cpp
Sensor sensor{42, 3};
```

conceptually performs:

1. Obtain storage for the entire `Sensor`.
2. Construct the `Device` subobject in its portion of that storage using `Device{42}`.
3. Initialize `channel_` with `3`.
4. Execute the `Sensor` constructor body.

`Device{id}` does not normally allocate a separate `Device`. It initializes the base subobject embedded within the `Sensor`.

If `Device` has no default constructor and the derived initializer omits it, compilation fails because the compiler attempts `Device()`.

### Virtual bases

Virtual base classes are initialized by the most-derived constructor, not by intermediate base constructors. This matters in diamond inheritance, but virtual inheritance should be used deliberately because it complicates layout and construction.

### Interview question

**Question:** Why can you not initialize a base class in the derived constructor body?

**Answer:** The base subobject must already be constructed before the derived body begins. An expression such as `Device{id};` in the body creates a separate temporary.

---

## 6. Initialization order

Initialization order is fixed by the language:

1. Virtual base classes, when applicable.
2. Direct base classes in base-specifier order.
3. Non-static data members in declaration order.
4. Constructor body.

The order written in the initializer list does not change it.

```cpp
class Example {
public:
    Example()
        : second_{first_},
          first_{42} {}

private:
    int first_;
    int second_;
};
```

Although the list writes `second_` first, `first_` is declared first and therefore initialized first. This particular code is safe because `first_` is ready before `second_`.

Reverse the declarations and the code becomes dangerous:

```cpp
private:
    int second_;
    int first_;
```

Now `second_` initializes first using an indeterminate `first_`.

### Best practice

Write initializer lists in the same order as declarations. Enable compiler warnings for reordered initializers.

### Destruction order

Destruction reverses successful construction:

1. Destructor body for the most-derived object.
2. Members in reverse declaration order.
3. Direct bases in reverse order.
4. Virtual bases last.

### Interview question

**Question:** Does initializer-list order control initialization order?

**Answer:** No. Base and member declaration order controls it. The list should match that order for clarity and warning-free builds.

---

## 7. Default member initializers

```cpp
class Buffer {
private:
    std::size_t size_{};
    int data_[10]{};
};
```

These are in-class default member initializers. They apply when a constructor does not explicitly initialize that member.

```cpp
class Device {
public:
    Device() = default;

    explicit Device(int id)
        : id_{id} {} // overrides the default of 0

private:
    int id_{};
    bool enabled_{false};
};
```

For `Device{42}`:

- `id_` uses the constructor initializer `42`.
- `enabled_` uses its in-class default `false`.

### Benefits

- Every constructor begins from consistent defaults.
- Adding a constructor does not accidentally leave scalars uninitialized.
- Boilerplate is reduced.
- The member declaration documents the default locally.

### Tradeoff

A default member initializer may hide unnecessary work if every constructor immediately overrides a costly default. Review expensive class-member construction.

### Interview question

**Question:** Is `int data_[10]{};` a constructor initializer list?

**Answer:** No. It is an in-class default member initializer that zero-initializes the array unless a constructor supplies another initializer.

---

## 8. Delegating constructors

One constructor can delegate to another constructor in the same class:

```cpp
class Socket {
public:
    Socket()
        : Socket{"127.0.0.1", 8080} {}

    Socket(std::string host, int port)
        : host_{std::move(host)},
          port_{port} {}

private:
    std::string host_;
    int port_;
};
```

This centralizes invariant establishment.

A delegating constructor's initializer list cannot initialize other members in addition to selecting the target constructor:

```cpp
// Socket() : Socket{"127.0.0.1", 8080}, port_{9000} {} // invalid
```

The target constructor initializes the complete object; the delegating constructor then runs its body.

### Tradeoff

Delegation reduces duplication, but a complicated chain can obscure which constructor establishes which invariant. Keep a clear primary constructor.

### Interview question

**Question:** What is a delegating constructor?

**Answer:** A constructor that invokes another constructor of the same class so initialization logic is centralized.

---

## 9. Defaulted and deleted constructors

### Defaulted

```cpp
class Device {
public:
    Device() = default;
    ~Device() = default;
};
```

`= default` explicitly requests compiler-generated behavior. It can improve clarity and affect triviality depending on where and how it is declared.

### Deleted

```cpp
class Device {
public:
    Device() = delete;
    explicit Device(int id);
};
```

This prevents construction without an ID.

A class can prevent heap allocation or particular conversions through deleted functions, but such techniques should be motivated by a real invariant.

### Non-copyable resource example

```cpp
class MutexOwner {
public:
    MutexOwner() = default;
    MutexOwner(const MutexOwner&) = delete;
    MutexOwner& operator=(const MutexOwner&) = delete;
};
```

Copy control is covered in detail in [`05_copy_constructor_and_copy_assignment.md`](./05_copy_constructor_and_copy_assignment.md).

### Interview question

**Question:** Why use `= delete` instead of declaring a private undefined constructor?

**Answer:** It states the prohibition directly, participates clearly in diagnostics, and prevents all access contexts from using the function.

---

## 10. Converting constructors and `explicit`

A constructor callable with one argument can define an implicit conversion:

```cpp
class Milliseconds {
public:
    Milliseconds(int value) : value_{value} {}

private:
    int value_;
};

void wait(Milliseconds duration);
wait(1000); // implicit conversion
```

This may be convenient for a natural value type, but it may also hide mistakes.

```cpp
class Milliseconds {
public:
    explicit Milliseconds(int value) : value_{value} {}
};

wait(Milliseconds{1000}); // intention is explicit
```

Copy-initialization rejects explicit constructors:

```cpp
// Milliseconds duration = 1000; // error
Milliseconds duration{1000};    // valid
```

Constructors with multiple parameters can also be converting constructors if remaining parameters have defaults:

```cpp
explicit Range(int low, int high = 100);
```

Since C++11, conversion operators can also be explicit:

```cpp
explicit operator bool() const;
```

### Interview question

**Question:** Why mark single-argument constructors explicit by default?

**Answer:** To prevent unintended implicit conversions unless the type relationship is intentionally designed as a conversion.

---

## 11. `std::initializer_list` constructors

Brace initialization gives `std::initializer_list` constructors strong preference:

```cpp
std::vector<int> a(10, 20); // ten elements, each 20
std::vector<int> b{10, 20}; // two elements: 10 and 20
```

A class may use:

```cpp
class RegisterSet {
public:
    RegisterSet(std::initializer_list<std::uint32_t> values);
};
```

This supports:

```cpp
RegisterSet registers{1, 2, 3};
```

### Tradeoffs

- Excellent for homogeneous element lists.
- Elements in an initializer list are const, which can inhibit moving move-only values.
- Overload resolution can surprise callers because initializer-list constructors are preferred.
- Empty braces may select a default constructor in some cases rather than an initializer-list constructor.

### Interview question

**Question:** Why can replacing parentheses with braces change a `std::vector`'s contents?

**Answer:** Braces prefer the initializer-list constructor, while parentheses may select the size/value constructor.

---

## 12. Destructors and RAII

A destructor has this form:

```cpp
class File {
public:
    ~File() {
        if (handle_) {
            close_file(handle_);
        }
    }

private:
    Handle handle_{};
};
```

It:

- Has no return type.
- Takes no ordinary parameters.
- Is called automatically when the object's lifetime ends.
- Should release resources owned by the object.
- Is normally expected not to throw.

RAII means resource ownership is represented by an object's lifetime:

```cpp
void process() {
    File file{"input.bin"};
    // use file
} // file destructor closes the handle
```

Cleanup also happens on early return and exception unwinding.

### Prefer member-owned RAII types

Instead of writing manual cleanup:

```cpp
class Buffer {
    int* data_;
};
```

prefer:

```cpp
class Buffer {
    std::vector<int> data_;
};
```

Then the compiler-generated destructor correctly destroys the vector.

### Interview question

**Question:** What is the connection between destructors and RAII?

**Answer:** RAII places a resource in an object whose destructor releases it, making cleanup follow scope and lifetime automatically.

---

## 13. Destruction timing and order

### Automatic objects

```cpp
{
    Device device;
} // destructor runs
```

### Dynamic objects

```cpp
auto device = std::make_unique<Device>();
device.reset(); // destroys now
```

Or destruction occurs when the last owning smart pointer dies.

### Containers

```cpp
std::vector<Device> devices;
```

Destroying the vector destroys its elements.

### Static objects

Function-local static and namespace-scope objects are destroyed during program termination, subject to ordering rules. Dependencies among globals across translation units can create the static initialization/destruction order problem.

### Temporary objects

Most temporaries are destroyed at the end of the full expression unless a lifetime-extension rule applies.

### Interview question

**Question:** In what order are members destroyed?

**Answer:** In reverse declaration order, after the containing destructor body runs.

---

## 14. Virtual destructors

If objects may be deleted through a base pointer, the base destructor should normally be virtual:

```cpp
class Device {
public:
    virtual ~Device() = default;
    virtual void start() = 0;
};

class Camera : public Device {
public:
    ~Camera() override {
        // release camera resources
    }
};

std::unique_ptr<Device> device = std::make_unique<Camera>();
```

When the smart pointer deletes through `Device*`, virtual dispatch ensures the `Camera` destructor runs before `Device` destruction.

Deleting a derived object through a base pointer without an appropriate virtual destructor is undefined behavior:

```cpp
class Device {
public:
    ~Device() = default; // non-virtual
};
```

### When a non-virtual protected destructor is appropriate

A base not intended for polymorphic deletion can make that contract explicit:

```cpp
class InterfaceMixin {
protected:
    ~InterfaceMixin() = default;
};
```

A common guideline is: a polymorphic base destructor should be public virtual or protected non-virtual, depending on the intended ownership model.

### Pure virtual destructor

A destructor may be pure virtual, but it still needs a definition because base destruction must execute:

```cpp
class Interface {
public:
    virtual ~Interface() = 0;
};

Interface::~Interface() = default;
```

### Interview question

**Question:** Why does a polymorphic base class need a virtual destructor?

**Answer:** So deletion through a base pointer invokes the complete derived-to-base destruction chain.

---

## 15. Exceptions during construction

```cpp
class System {
public:
    System()
        : log_{},
          connection_{},
          worker_{} {}
};
```

If `connection_` constructs successfully but `worker_` throws:

- `connection_` is destroyed.
- `log_` is destroyed.
- The `System` destructor is not called because the complete `System` was never constructed.
- Storage cleanup proceeds according to how construction was initiated.

This is why RAII members are essential. Raw resources acquired in a constructor body can leak if a later operation throws unless immediately wrapped.

### Function-try-blocks

A constructor function-try-block can observe exceptions from base/member initialization:

```cpp
System::System()
try
    : connection_{make_connection()} {
} catch (...) {
    // log and rethrow or translate
    throw;
}
```

The already-constructed subobjects have already been handled by the language. Access to not-fully-constructed state is restricted and must be treated cautiously.

### Destructor exceptions

Destructors should generally be `noexcept` and must not let exceptions escape during stack unwinding, because a second active exception leads to `std::terminate`.

### Interview question

**Question:** Is the containing object's destructor called if its constructor throws?

**Answer:** No, because that object never completed construction. Successfully constructed bases and members are destroyed automatically.

---

## 16. Virtual dispatch during construction and destruction

Calling a virtual function from a constructor does not dispatch to a more-derived override:

```cpp
class Base {
public:
    Base() {
        initialize(); // calls Base::initialize
    }

    virtual void initialize();
};
```

While the base constructor runs, the derived portion is not yet constructed. During destruction, the derived portion may already be destroyed. Dispatch is therefore limited to the currently active construction/destruction level.

Calling a pure virtual function in such a context can lead to undefined behavior or a runtime failure, depending on the call and implementation.

### Better pattern

Perform derived-specific initialization after complete construction, possibly through:

- A factory function.
- A non-virtual initialization step called by the factory.
- Constructor parameters that supply required strategies or dependencies.

### Interview question

**Question:** Why does a virtual call in a base constructor not reach the derived override?

**Answer:** The derived subobject is not yet constructed, so treating it as active would expose uninitialized derived state.

---

## 17. Construction and destruction in inheritance

For:

```cpp
class BaseA {};
class BaseB {};
class MemberA {};
class MemberB {};

class Derived : public BaseA, public BaseB {
    MemberA first_;
    MemberB second_;
};
```

Construction order is:

```text
BaseA -> BaseB -> first_ -> second_ -> Derived body
```

Destruction order is:

```text
Derived destructor body -> second_ -> first_ -> BaseB -> BaseA
```

This structure ensures each constructor can rely on its bases and earlier members, and each destructor body can still access its members before they are destroyed.

### Interview question

**Question:** Why are bases constructed before the derived constructor body?

**Answer:** The derived part may rely on base invariants and behavior, so the base subobjects must already be valid.

---

## 18. Embedded and real-time considerations

Constructors and destructors improve deterministic cleanup, but their contents require review in constrained systems.

Ask:

- Does construction allocate dynamically?
- Can it throw?
- Does it block?
- Is it safe before the scheduler starts?
- Does static initialization access hardware too early?
- Is destruction actually reached in a non-terminating firmware process?
- Is cleanup permitted in an ISR?
- Is initialization order across translation units deterministic enough?

### Static initialization

A function-local static is initialized on first use and, since C++11, initialization is thread-safe:

```cpp
Driver& driver() {
    static Driver instance;
    return instance;
}
```

The guard may have runtime cost. Some embedded systems use explicit startup sequencing instead.

### Two-phase initialization tradeoff

A constructor that cannot report failure without exceptions may be paired with a factory:

```cpp
static expected<Device, Error> create(Configuration config);
```

A default constructor followed by `init()` can leave temporarily invalid objects and requires every caller to remember the second step. Prefer factories or valid-state types when feasible.

### Interview question

**Question:** Is RAII compatible with embedded systems that prohibit heap allocation?

**Answer:** Yes. RAII is about lifetime-bound resources, not heap use. Stack objects, static objects, locks, interrupt guards, and hardware handles can all use RAII.

---

## 19. Common mistakes

### Assigning instead of initializing

```cpp
Device(int id) {
    id_ = id;
}
```

Use `: id_{id}`.

### Depending on initializer-list order

Declaration order wins.

### Leaving scalar members indeterminate

Use meaningful constructor initialization or in-class defaults.

### Forgetting explicit

Accidental implicit conversions can select surprising overloads.

### Missing virtual destructor

Polymorphic deletion becomes invalid.

### Manual cleanup instead of RAII members

This creates exception and early-return hazards.

### Throwing from destructors

This can terminate the process during unwinding.

### Calling virtual customization too early

Derived state is unavailable in base construction.

### Confusing `Foo b = a` with assignment

A declaration initializes a new object.

---

## 20. Design guidelines

1. Establish a complete invariant before the constructor finishes.
2. Prefer direct member initialization.
3. Put stable defaults at member declarations.
4. Write initializer lists in declaration order.
5. Use `explicit` unless an implicit conversion is intentional.
6. Use RAII member types so default destruction is correct.
7. Default special functions when compiler behavior is exactly intended.
8. Delete invalid construction or copying operations explicitly.
9. Make polymorphic base destructors virtual when deletion through base is allowed.
10. Keep constructors and destructors predictable; document blocking, allocation, and failure.
11. Prefer factories over objects that require a fallible `init()` before becoming valid.
12. Review static initialization carefully in firmware and multi-translation-unit systems.

### Interview question

**Question:** What should a good constructor guarantee?

**Answer:** On successful return, the complete object satisfies its invariants and is ready for all documented public operations.

---

## Final interview checklist

You should be able to explain:

- Allocation versus initialization versus construction.
- Default-, value-, direct-, list-, and copy-initialization.
- Why `Foo b = a` is initialization.
- Member initializer lists versus body assignment.
- Required initializer-list cases.
- Base and member construction order.
- Default member initializers.
- Delegating, defaulted, and deleted constructors.
- `explicit` and initializer-list overload preference.
- RAII and destructor timing.
- Reverse destruction order.
- Virtual and pure virtual destructors.
- Exception cleanup during partial construction.
- Virtual dispatch restrictions in constructors/destructors.
- Embedded constraints on initialization and cleanup.
