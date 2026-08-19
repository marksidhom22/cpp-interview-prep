# C++ `static`, `explicit`, and `friend`

These three keywords solve different design problems:

- `static` controls duration, linkage, or class-wide membership depending on context.
- `explicit` prevents unintended implicit conversions.
- `friend` grants selected code access to a class's non-public representation.

They are grouped here because interviews often test whether you can distinguish their context-dependent meanings and design tradeoffs.

---

## Part I - Five-Minute Interview Review

## `static` in five minutes

```cpp
void count_calls() {
    static int count{}; // one object, persists between calls
    ++count;
}
```

```cpp
class Device {
public:
    inline static std::size_t count{}; // one class-wide variable

    static std::size_t active_count(); // no this pointer
};
```

```cpp
static void helper(); // namespace-scope internal linkage
```

- A local static has block scope but static storage duration. See [Local static variables](#2-local-static-variables).
- A static data member belongs to the class rather than each object. See [Static data members](#3-static-data-members).
- A static member function has no `this` pointer and directly accesses only static members. See [Static member functions](#4-static-member-functions).
- Namespace-scope `static` gives internal linkage; unnamed namespaces are generally preferred in C++ source files. See [Namespace-scope static](#5-namespace-scope-static-and-internal-linkage).
- Function-local static initialization is thread-safe since C++11, but later access to the object is not automatically synchronized. See [Initialization and concurrency](#6-static-initialization-concurrency-and-order).

## `explicit` in five minutes

```cpp
class Milliseconds {
public:
    explicit Milliseconds(int value);
};

Milliseconds a{1000};      // valid
// Milliseconds b = 1000;   // rejected
```

- Use explicit on converting constructors unless implicit conversion is intentionally part of the type's design. See [Converting constructors](#9-converting-constructors).
- Explicit conversion operators prevent broad unintended conversions while permitting direct or contextual use. See [Explicit conversion operators](#11-explicit-conversion-operators).
- C++20 supports conditional `explicit(condition)`. See [Conditional explicit](#12-conditional-explicit).

## `friend` in five minutes

```cpp
class Box {
    friend bool operator==(const Box&, const Box&);

private:
    int value_{};
};
```

- A friend is not a member; it is granted access to private/protected state. See [Friend functions](#14-friend-functions).
- Friendship is explicit, not inherited, not transitive, and not reciprocal. See [Friendship rules](#17-friendship-rules).
- Hidden friends support symmetric operators and ADL without polluting ordinary lookup. See [Hidden friends and operators](#18-hidden-friends-and-operators).
- Prefer a narrow public interface when it can express the operation cleanly; use friendship when the operation is genuinely part of the abstraction. See [Friend tradeoffs](#19-friend-tradeoffs-and-design).

### Five interview checks

1. **Does a static member function have a `this` pointer?** No.
2. **Is local-static initialization thread-safe?** Initialization is; arbitrary later reads/writes are not.
3. **What does explicit stop?** Implicit conversion through that constructor/operator in contexts that require implicit conversion.
4. **Is a friend function a class member?** No.
5. **Does a friend of a base automatically access a derived class?** No; friendship is not inherited.

---

## Part II - Detailed Reference

# `static`

## 1. One keyword, several meanings

The meaning of `static` depends on where it appears.

| Context | Main effect |
|---|---|
| Local variable | Static storage duration, block scope |
| Class data member | One shared member associated with the class |
| Class member function | No implicit object/`this` |
| Namespace-scope name | Internal linkage |
| Function declaration at namespace scope | Function visible only within translation unit |

These meanings are related historically but should be reasoned about separately.

### Storage duration, scope, and linkage

- **Storage duration** answers when storage exists.
- **Scope** answers where a name can be used.
- **Linkage** answers whether declarations in different scopes/translation units name the same entity.

A local static demonstrates why these are distinct: its name has block scope, but the object exists for the program's duration.

### Interview question

**Question:** Does `static` always mean "shared by all objects"?

**Answer:** No. That describes a static class data member. At block scope it controls storage duration; at namespace scope it controls linkage; on a member function it removes the implicit object parameter.

---

## 2. Local static variables

```cpp
int next_id() {
    static int id{};
    return ++id;
}
```

`id`:

- Is initialized once, when control first reaches the declaration.
- Retains its value across calls.
- Has block scope.
- Has static storage duration.
- Is destroyed during program termination if it has non-trivial destruction.

### Initialization timing

```cpp
Configuration& configuration() {
    static Configuration config = load_configuration();
    return config;
}
```

Initialization happens on first call, not necessarily at program startup. This is the construct-on-first-use idiom.

Since C++11, if multiple threads race to initialize the same function-local static, initialization occurs exactly once. Other threads wait.

### Later access still needs synchronization

```cpp
void increment() {
    static int count{};
    ++count; // data race if called concurrently without synchronization
}
```

Only initialization is protected. The object does not become atomic or thread-safe.

### Recursive initialization

If initialization recursively re-enters the same declaration before completion, behavior is problematic/undefined under the relevant rules. Avoid initialization dependencies that call back into themselves.

### Costs

Implementations may use a guard check on each entry. It is often tiny and optimized, but real-time code should measure and review it.

### Interview question

**Question:** What is thread-safe about a local static in C++11 and later?

**Answer:** Its one-time initialization. Concurrent later mutation requires its own synchronization.

---

## 3. Static data members

```cpp
class Device {
public:
    static std::size_t count;

    Device() {
        ++count;
    }

    ~Device() {
        --count;
    }
};

std::size_t Device::count = 0;
```

There is one `count` associated with the class, not one per `Device`.

Access it as:

```cpp
Device::count
```

Access through an object is permitted but less clear:

```cpp
device.count
```

### Definition requirements

Traditional static data members need one out-of-class definition in a source file:

```cpp
std::size_t Device::count = 0;
```

C++17 inline variables allow definition in the class/header:

```cpp
class Device {
public:
    inline static std::size_t count{};
};
```

`inline` here permits identical definitions across translation units while referring to one entity.

### `constexpr` static members

```cpp
class Protocol {
public:
    inline static constexpr std::uint32_t magic = 0xCAFEu;
};
```

Modern inline constexpr members are convenient compile-time class constants.

### Object-count caveats

A manual counter must consider:

- Copies and moves.
- Construction exceptions.
- Destruction order.
- Concurrency.
- Whether derived objects count.
- Static objects during startup/shutdown.

Use `std::atomic<std::size_t>` if concurrent increments must be safe.

### Interview question

**Question:** How many copies of a static data member exist?

**Answer:** One per program entity for that class member, rather than one inside each class object, subject to linkage and program-definition rules.

---

## 4. Static member functions

```cpp
class Device {
public:
    static std::size_t active_count() {
        return count_;
    }

private:
    inline static std::size_t count_{};
};
```

A static member function:

- Has no implicit object parameter.
- Has no `this` pointer.
- Can be called as `Device::active_count()`.
- Directly accesses static class members.
- Can access ordinary members only through an explicit object.

```cpp
static int read_id(const Device& device) {
    return device.id_;
}
```

Because it is a class member, it still has access to private members when given an object.

### Cannot be const or virtual

Trailing const qualifies `this`, but a static member has no `this`:

```cpp
// static int count() const; // invalid
```

Virtual dispatch also requires an object, so static members cannot be virtual.

### Use cases

- Factory functions.
- Class-wide queries.
- Utilities tightly associated with the class's private representation.
- Callbacks requiring plain function-pointer compatibility, if the signature and ABI match.

Do not use a static member merely as a namespace substitute when no class-private access or semantic association exists.

### Interview question

**Question:** Why can a static member function not be const?

**Answer:** Member-function const qualifies the implicit object, and a static member function has no implicit object.

---

## 5. Namespace-scope static and internal linkage

```cpp
// device.cpp
static void reset_hardware() {
}
```

At namespace scope, `static` gives `reset_hardware` internal linkage. Other translation units cannot refer to that entity by an external declaration.

Modern C++ often prefers an unnamed namespace:

```cpp
namespace {
    void reset_hardware() {
    }

    class Helper {};
}
```

An unnamed namespace works naturally for functions, variables, and types.

### Do not confuse with static storage duration

A namespace-scope object already has static storage duration even without `static`:

```cpp
int global_counter;        // static storage duration, external linkage
static int local_counter;  // static storage duration, internal linkage
```

Here `static` changes linkage, not lifetime.

### Header caution

A namespace-scope internal-linkage variable in a header may create one copy per translation unit. Use `inline` variables or other appropriate patterns when one program-wide entity is required.

### Interview question

**Question:** At namespace scope, what does `static` add to a variable that already lives for the program duration?

**Answer:** Internal linkage: the name refers to an entity local to that translation unit.

---

## 6. Static initialization, concurrency, and order

Objects with static storage duration undergo:

1. Static initialization, including zero initialization and constant initialization where possible.
2. Dynamic initialization when required.

### Cross-translation-unit order problem

```cpp
// a.cpp
Logger logger{configuration()};

// b.cpp
Configuration global_configuration{load()};
```

The dynamic initialization order of non-local objects across translation units can be unspecified or only partially ordered. `logger` may access configuration before it is dynamically initialized.

### Construct on first use

```cpp
Configuration& configuration() {
    static Configuration value = load();
    return value;
}
```

This delays construction until first use and gives a clear dependency at the call site.

### Destruction order

Function-local statics are destroyed in reverse order of completed initialization within the relevant rules. Dependencies during program shutdown can still fail if one static uses another that has already been destroyed.

Some process-lifetime services are intentionally never destroyed, but leaking by design needs documentation and may be unacceptable for test isolation or analysis tools.

### Embedded implications

Static initialization can:

- Increase startup time before `main`.
- Access hardware before clocks/peripherals are ready.
- Consume RAM for the program's entire execution.
- Introduce hidden guards or locking.
- Create initialization-order dependencies.

Explicit platform startup sequencing is often clearer in firmware.

### Interview question

**Question:** What is the static initialization order fiasco?

**Answer:** A non-local static object in one translation unit depends on another whose dynamic initialization order is not guaranteed, so it may be used before construction or after destruction.

---

## 7. `static` versus `thread_local`

```cpp
thread_local int last_error{};
```

A thread-local object has one instance per thread rather than one program-wide instance.

A local declaration can combine the ideas:

```cpp
int& thread_counter() {
    static thread_local int value{};
    return value;
}
```

The name has block scope; each thread has a separate persistent `value`.

### Tradeoffs

Thread-local storage can avoid synchronization for per-thread state but:

- Consumes storage per thread.
- Complicates aggregation.
- May have platform/runtime costs.
- May be unavailable or constrained on some embedded runtimes.

### Interview question

**Question:** How does `thread_local` differ from a normal static local?

**Answer:** A normal static local has one shared instance; a thread-local object has one instance per thread.

---

## 8. Static design guidelines

Use static state deliberately:

- Prefer dependency injection over hidden mutable global state.
- Make immutable static data `constexpr` when possible.
- Synchronize shared mutable state.
- Keep startup dependencies explicit.
- Prefer function-local statics when lazy initialization solves ordering.
- Use inline static data members for header-defined class-wide state in C++17+.
- Use namespaces for stateless utilities rather than empty "utility classes."
- Review memory residence and initialization cost on embedded targets.

### Interview question

**Question:** What is the main design risk of mutable static state?

**Answer:** Hidden global coupling: lifetime, test isolation, initialization order, and concurrent access become harder to reason about.

---

# `explicit`

## 9. Converting constructors

A constructor that can be called with one argument may define a conversion:

```cpp
class Temperature {
public:
    Temperature(double celsius)
        : celsius_{celsius} {}

private:
    double celsius_;
};

void log(Temperature temperature);

log(25.0); // implicit conversion
```

This conversion may be natural, but it also lets unrelated overloads accept values unexpectedly.

Mark it explicit:

```cpp
explicit Temperature(double celsius);
```

Now:

```cpp
log(Temperature{25.0});
// log(25.0); // rejected
```

### More than one declared parameter

This can still be a converting constructor:

```cpp
explicit Range(int low, int high = 100);
```

Only one argument is required at the call site.

### Multi-argument list conversion

Modern C++ also permits list-based conversions involving constructors with multiple arguments in some contexts:

```cpp
void draw(Point point);
// draw({1, 2}); // allowed if Point(int, int) is not explicit
```

### Interview question

**Question:** Is every converting constructor syntactically a one-parameter constructor?

**Answer:** No. It is a constructor callable with a single argument expression or relevant initializer form; additional parameters may have defaults.

---

## 10. Direct versus copy initialization with explicit

```cpp
class DeviceId {
public:
    explicit DeviceId(int value);
};
```

Allowed:

```cpp
DeviceId a(42);
DeviceId b{42};
auto c = DeviceId{42};
```

Rejected:

```cpp
// DeviceId d = 42;
```

Copy-initialization considers conversion differently and cannot use an explicit constructor as an implicit conversion.

### Function calls

```cpp
void connect(DeviceId id);

// connect(42);             // rejected
connect(DeviceId{42});      // valid
```

### Return statements

```cpp
DeviceId make_id() {
    return DeviceId{42};
}
```

A bare `return 42;` would require an implicit conversion and is rejected when the constructor is explicit.

### Interview question

**Question:** Why does `T value{arg}` accept an explicit constructor while `T value = arg` does not?

**Answer:** The first is direct initialization that names the target type; the second is copy-initialization requiring an allowed implicit conversion.

---

## 11. Explicit conversion operators

```cpp
class FileHandle {
public:
    explicit operator bool() const noexcept {
        return handle_ != invalid_handle;
    }

private:
    Handle handle_{invalid_handle};
};
```

Allowed contextual Boolean use:

```cpp
if (file) {
}

while (file) {
}

bool valid = static_cast<bool>(file);
```

Broad implicit arithmetic conversion is prevented.

Without explicit, an object convertible to `bool` may participate unexpectedly in integer overloads or arithmetic.

### Other explicit conversions

```cpp
explicit operator int() const;
```

Callers use:

```cpp
int value = static_cast<int>(object);
```

This documents potentially lossy or semantically significant conversion.

### Interview question

**Question:** Why does `explicit operator bool` still work in an `if` condition?

**Answer:** Boolean control expressions use contextual conversion to bool, which is specifically allowed to consider an explicit bool conversion.

---

## 12. Conditional explicit

C++20 supports:

```cpp
template<class T>
class Wrapper {
public:
    explicit(!std::is_convertible_v<T, int>)
    Wrapper(T value);
};
```

The constructor is explicit when the compile-time condition is true and implicit otherwise.

A common generic-wrapper goal is to mirror whether construction of the underlying type is implicit.

### Tradeoff

Conditional explicit improves generic fidelity but makes an interface harder to inspect casually. Use it in well-motivated generic libraries, not as everyday cleverness.

### Interview question

**Question:** What does `explicit(condition)` do?

**Answer:** It makes a constructor or conversion function explicit only when the constant-expression condition is true.

---

## 13. Explicit design guidelines

- Mark single-logical-argument constructors explicit by default.
- Permit implicit conversion only when it is safe, cheap, unsurprising, and preserves meaning.
- Keep unit and identifier types explicit to prevent accidental mixing.
- Use explicit bool conversions for state testing.
- Remember that explicit does not restrict direct construction.
- Review overload sets: implicit conversions can create ambiguity or silently select expensive operations.

A good implicit conversion resembles widening from a clearly compatible representation. A conversion that validates, allocates, loses information, or changes units should normally be explicit or a named factory.

### Interview question

**Question:** When is an implicit converting constructor reasonable?

**Answer:** When the source-to-target relationship is universally natural, safe, cheap, and unsurprising, and implicit participation improves rather than obscures overload behavior.

---

# `friend`

## 14. Friend functions

```cpp
class Box {
public:
    explicit Box(int value) : value_{value} {}

    friend bool same_value(const Box& left, const Box& right);

private:
    int value_;
};

bool same_value(const Box& left, const Box& right) {
    return left.value_ == right.value_;
}
```

`same_value` is not a member:

```cpp
same_value(a, b);
// a.same_value(b); // not implied
```

It receives access permission to `Box`'s private and protected members.

### Declaration and definition

A friend can be declared inside and defined outside, or defined inline inside the class:

```cpp
class Box {
    friend bool operator==(const Box& a, const Box& b) {
        return a.value_ == b.value_;
    }

    int value_{};
};
```

The inline definition is a non-member function.

### Interview question

**Question:** Does declaring a function inside a class with `friend` make it a member?

**Answer:** No. It remains a non-member function with access to the class's non-public state.

---

## 15. Friend classes and members

### Entire friend class

```cpp
class Diagnostics;

class Device {
    friend class Diagnostics;

private:
    int error_code_{};
};
```

Every member of `Diagnostics` can access the selected `Device` internals.

### One member function

It is possible to grant access to one member of another class, but declaration ordering becomes important:

```cpp
class Device;

class Diagnostics {
public:
    void inspect(const Device&);
};

class Device {
    friend void Diagnostics::inspect(const Device&);
private:
    int error_code_{};
};
```

Prefer the narrowest practical friendship.

### Templates

A class can befriend a function template, class template, or specialization. Template friendship syntax can be subtle; use it only when the generic abstraction genuinely requires private access.

### Interview question

**Question:** Which grants narrower access: `friend class Diagnostics` or befriending one member function?

**Answer:** Befriending one member function, though it requires suitable prior declarations and may add coupling complexity.

---

## 16. Friend and encapsulation

Friendship is often described as "breaking encapsulation," but a more precise view is:

> The class itself declares which external operations are part of its trusted implementation boundary.

A well-designed friend can preserve a small public interface. For example, a comparison operator may need two objects symmetrically without exposing raw member getters only for comparison.

Bad friendship gives a broad unrelated manager class unrestricted access because public APIs were inconvenient.

### Alternatives

Before using friend, consider:

- A public operation expressing the behavior.
- A private member called by a narrow friend.
- A nested helper type.
- Composition.
- Moving the operation into the class as a member.
- A test through public behavior rather than internal inspection.

### Interview question

**Question:** Does every use of friend destroy encapsulation?

**Answer:** No. Friendship expands the explicitly trusted implementation boundary, but excessive or unrelated friendship creates tight coupling and weakens representation control.

---

## 17. Friendship rules

Friendship is:

- **Not reciprocal:** if `A` befriends `B`, `A` does not automatically access `B`.
- **Not transitive:** a friend of a friend gains nothing.
- **Not inherited:** friends of a base are not automatically friends of derived-private state, and friends of a derived class do not automatically access base-private state beyond normal rules.
- **Explicit:** the granting class controls access.

```cpp
class A {
    friend class B;
};

// B can access A.
// A cannot access B merely because of this.
// Friends of B cannot access A.
```

Access control and inheritance interactions can be subtle, but these four rules answer the common interview question.

### Interview question

**Question:** If `A` befriends `B` and `B` befriends `C`, can `C` access `A`?

**Answer:** No. Friendship is not transitive.

---

## 18. Hidden friends and operators

A function declared and defined as a friend inside a class may be found primarily through ADL:

```cpp
namespace units {
class Distance {
public:
    explicit Distance(int meters) : meters_{meters} {}

    friend bool operator==(const Distance& left,
                           const Distance& right) {
        return left.meters_ == right.meters_;
    }

private:
    int meters_;
};
}
```

Usage:

```cpp
units::Distance a{10};
units::Distance b{10};

bool equal = (a == b);
```

ADL associates the operands with namespace `units` and finds the hidden friend.

### Benefits

- The function is closely documented with the type.
- It gets symmetric access to both operands.
- It does not broadly participate in unrelated unqualified lookup.
- It can avoid public getters added only for operator implementation.

### Tradeoff

Hidden-friend lookup surprises developers unfamiliar with ADL. Keep the pattern conventional and document important operations.

### Interview question

**Question:** How can an inline friend operator be found if it is not a member?

**Answer:** Argument-dependent lookup finds it through the namespace/class associated with its operands.

---

## 19. Friend tradeoffs and design

Use friendship when:

- A symmetric non-member operator needs representation access.
- Two tightly coupled abstractions form one implementation unit.
- A factory must call a private constructor.
- A serialization adapter genuinely belongs to the type's representation layer.

Avoid it when:

- It merely saves writing a stable public operation.
- A large manager class gains access to many unrelated types.
- Tests inspect implementation details rather than behavior.
- It allows invariants to be bypassed widely.

### Private-constructor factory

```cpp
class Device {
public:
    static std::optional<Device> create(Configuration config);

private:
    explicit Device(ValidatedConfiguration config);
};
```

A static member factory already has private access, so friend is unnecessary. An external factory may be made a narrow friend if separation is required.

### Interview question

**Question:** What is the key tradeoff of friend?

**Answer:** It enables precise implementation cooperation without public exposure, but increases coupling to private representation.

---

## 20. How the three keywords interact

```cpp
class DeviceId {
public:
    explicit DeviceId(int value)
        : value_{value} {}

    static DeviceId invalid() {
        return DeviceId{-1};
    }

    friend bool operator==(const DeviceId& left,
                           const DeviceId& right) {
        return left.value_ == right.value_;
    }

private:
    int value_;
};
```

- `explicit` prevents accidental integer-to-ID conversion.
- `static` provides a class-associated factory without an object.
- `friend` implements symmetric equality without exposing raw representation.

Each keyword expresses a separate design decision.

### Interview question

**Question:** Why might `invalid()` be static?

**Answer:** Creating the sentinel does not require an existing `DeviceId`; the function is associated with the type itself.

---

## 21. Embedded and systems considerations

### Static

- Verify startup and shutdown sequencing.
- Know whether storage resides in `.bss`, `.data`, flash, TLS, or another linker section.
- Avoid unsynchronized mutable shared state.
- Measure first-use guard overhead on hard real-time paths.
- Avoid hardware access before platform initialization.

### Explicit

Strong wrappers can prevent unit and register mistakes at zero runtime cost:

```cpp
struct RegisterAddress {
    explicit RegisterAddress(std::uintptr_t value);
};
```

### Friend

Hardware abstractions sometimes use friendship between a register block and a narrowly scoped driver. Keep access narrow so invariants and volatile access rules remain auditable.

### Interview question

**Question:** Which of these keywords directly introduces runtime overhead?

**Answer:** None inherently. Their designs may lead to initialization guards, synchronization, or function behavior with costs, but the keywords themselves are primarily compile-time/interface mechanisms.

---

## 22. Common mistakes

- Assuming all `static` uses mean the same thing.
- Believing a local static is fully thread-safe after initialization.
- Defining mutable class-wide state without synchronization.
- Forgetting an out-of-class static-member definition in pre-inline-variable patterns.
- Creating cross-translation-unit initialization dependencies.
- Omitting `explicit` from unit, handle, or ID constructors.
- Believing explicit prevents direct construction.
- Treating a friend function as a member.
- Assuming friendship is reciprocal, transitive, or inherited.
- Using a broad friend class where one operation would suffice.
- Exposing getters only to avoid a justified symmetric friend operator.

---

## Final interview checklist

You should be able to explain:

- Static storage duration, scope, and linkage.
- Local static initialization and thread-safety boundaries.
- Static data members and inline variables.
- Static member functions and lack of `this`.
- Namespace-scope internal linkage.
- Static initialization order problems.
- `thread_local` comparison.
- Converting constructors and direct/copy initialization.
- Explicit conversion operators and contextual bool.
- Conditional explicit.
- Friend functions versus members.
- Friend classes and member functions.
- Non-reciprocal, non-transitive, non-inherited friendship.
- Hidden friends and ADL.
- Encapsulation tradeoffs.
- Embedded implications of each keyword.
