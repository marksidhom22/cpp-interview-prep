# C++ Storage, Scope, Lifetime, Ownership, and Temporaries

Many serious C++ bugs come from combining concepts that must be reasoned about separately. "It is on the stack" is not enough. Ask where storage comes from, when the object is alive, where its name is visible, who owns its resources, and which borrowed handles remain valid.

---

## Part I - Five-Minute Interview Review

### The four concepts you must separate

| Concept | Question |
|---|---|
| Scope | Where is a name visible in source code? |
| Storage duration | How long does the object's storage exist? |
| Lifetime | During what interval does a valid object exist in that storage? |
| Ownership | Which object/code is responsible for ending or releasing a resource? |

See [Separate the concepts](#1-separate-scope-storage-duration-lifetime-and-ownership).

### Storage durations

```cpp
void f() {
    int automatic{};        // automatic storage duration
    static int persistent{}; // static storage duration
    thread_local int per_thread{}; // thread storage duration
    auto dynamic = std::make_unique<int>(0); // pointed-to int has dynamic storage
}
```

See [The four storage durations](#2-the-four-storage-durations).

### Mandatory lifetime rules

- An automatic object is destroyed when its scope exits, including early return and exception unwinding. See [Automatic objects](#3-automatic-objects-and-the-stack).
- Dynamic storage does not manage itself; represent ownership with RAII, normally `std::unique_ptr` or a container. See [Dynamic storage](#4-dynamic-storage-the-free-store-and-the-heap).
- A pointer, reference, iterator, span, or view does not extend the source object's lifetime. See [Borrowing and dangling](#9-borrowed-handles-and-dangling).
- Most temporaries live until the end of the full expression. Direct binding to a local const lvalue reference can extend a temporary's lifetime. See [Temporary objects](#11-temporary-objects) and [Temporary lifetime extension](#12-temporary-lifetime-extension).
- Returning a reference to a local object is always wrong. See [Returning pointers and references](#10-returning-pointers-references-and-views).
- Container reallocation or erasure may invalidate pointers, references, and iterators. See [Container invalidation](#14-container-invalidation).
- A lambda captured by reference can outlive the captured local, especially in asynchronous code. See [Lambda and callback lifetimes](#15-lambda-callback-and-thread-lifetimes).
- Construction and allocation are separate; destruction and deallocation are separate. See [Object lifetime boundaries](#7-object-lifetime-boundaries).
- `new`/`delete` and `malloc`/`free` must not be mixed. See [`new` versus `malloc`](#5-new-delete-malloc-and-free).
- "Stack" and "heap" are implementation-oriented shorthand; standard C++ specifies storage duration and lifetime. See [Stack and heap terminology](#6-stack-and-heap-terminology).

### Five interview checks

1. **Does a raw pointer keep an object alive?** No.
2. **Does leaving scope always mean storage disappears?** A local static name leaves scope, but its object persists.
3. **Does a const reference always extend a temporary?** Only in specific direct-binding contexts; passing through or returning a reference does not re-extend it.
4. **Where does a `unique_ptr` live?** The smart-pointer object can be automatic while its pointee has dynamic storage.
5. **What matters more than "stack versus heap"?** Ownership, lifetime, validity, allocation behavior, and required duration.

---

## Part II - Detailed Reference

## 1. Separate scope, storage duration, lifetime, and ownership

Consider:

```cpp
std::unique_ptr<Device> make_device() {
    auto device = std::make_unique<Device>();
    return device;
}
```

There are two objects:

1. The local `unique_ptr` object, whose name `device` has block scope and whose storage is automatic.
2. The `Device` object, whose storage is dynamic and whose ownership is transferred to the returned `unique_ptr`.

Returning transfers ownership; it does not move the local stack bytes into the caller.

### Another separation example

```cpp
Device* observer = nullptr;

{
    Device device;
    observer = &device;
}
```

After the block:

- The name `device` is out of scope.
- The automatic storage for its object is no longer active.
- The `Device` lifetime has ended.
- `observer` still exists.
- `observer` is dangling and must not be dereferenced.

The pointer's lifetime and the pointee's lifetime are independent.

### Interview question

**Question:** Can a name be out of scope while its object is still alive?

**Answer:** Yes. A local static object persists after execution leaves the block, and a dynamically allocated object may outlive the local pointer name that originally referred to it.

---

## 2. The four storage durations

C++ defines four storage-duration categories.

### Automatic storage duration

Most local variables and parameters:

```cpp
void process(int parameter) {
    Frame frame;
}
```

Their storage normally lasts until the enclosing block/function exits.

### Static storage duration

Namespace-scope variables and objects declared static:

```cpp
DeviceRegistry registry;

void f() {
    static int calls{};
}
```

Their storage lasts for the program's execution.

### Thread storage duration

```cpp
thread_local Error last_error;
```

One object exists per thread for that thread's lifetime.

### Dynamic storage duration

Storage obtained through allocation facilities:

```cpp
auto device = std::make_unique<Device>();
```

The pointee's storage lasts until the owning mechanism deallocates it.

### Subobjects

A data member or base subobject normally has the storage duration of its complete containing object.

### Interview question

**Question:** What storage duration does a member of a dynamically allocated object have?

**Answer:** As a subobject, its storage duration follows the complete dynamically allocated object.

---

## 3. Automatic objects and the stack

```cpp
void sample() {
    Sensor sensor;
    std::array<int, 32> readings{};
}
```

These objects have automatic storage duration. Implementations usually place them in a stack frame, but the standard describes semantics rather than requiring a physical stack.

### Benefits

- Deterministic scope-based destruction.
- No explicit deallocation.
- Typically constant-time storage management.
- Good locality.
- Natural RAII and exception cleanup.

### Constraints

- Lifetime is tied to scope unless state is moved/copied elsewhere.
- Large objects may exceed stack budgets.
- Recursion multiplies frame usage.
- Returning a pointer/reference to a local is invalid.

### Early exits

Destructors still run:

```cpp
void process() {
    LockGuard lock{mutex};

    if (!ready()) {
        return;
    }
} // lock always releases
```

### Embedded considerations

Thread stacks are often fixed and small. Review:

- Large local arrays.
- Deep recursion.
- Worst-case call depth.
- Interrupt stack usage.
- Compiler-created temporaries.
- Alignment and guard regions.

### Interview question

**Question:** Does automatic storage guarantee a physical hardware stack?

**Answer:** No. It specifies lifetime semantics. A stack is the usual implementation, subject to optimization and platform conventions.

---

## 4. Dynamic storage, the free store, and the heap

Manual syntax:

```cpp
Device* device = new Device{42};
delete device;
```

The object continues to exist beyond the allocating scope if not deleted:

```cpp
Device* make_device() {
    return new Device{42};
}
```

This transfers an undocumented cleanup obligation to the caller and is easy to misuse.

Prefer explicit RAII ownership:

```cpp
std::unique_ptr<Device> make_device() {
    return std::make_unique<Device>(42);
}
```

### When dynamic storage is justified

- Runtime-selected lifetime independent of lexical scope.
- Polymorphic objects with dynamic type.
- Runtime-sized data.
- Large objects that should not consume a constrained stack.
- Stable addresses across movement of owning handles.
- Shared lifetime, if genuinely required.

### Costs and risks

- Allocation/deallocation latency.
- Fragmentation.
- Allocation failure.
- Pointer indirection and reduced locality.
- Ownership complexity.
- Nondeterministic timing in general-purpose allocators.

Dynamic allocation is not automatically wrong. Unclear ownership is the deeper problem.

### Interview question

**Question:** When should you dynamically allocate an object?

**Answer:** When required lifetime, size, polymorphism, address stability, or ownership cannot be expressed appropriately with direct scoped/container storage, after considering cost and determinism.

---

## 5. `new`, `delete`, `malloc`, and `free`

### `new`

```cpp
Widget* widget = new Widget{arguments};
```

Conceptually:

1. Obtain suitably sized/aligned storage.
2. Construct `Widget`.
3. Return a typed pointer.

### `delete`

```cpp
delete widget;
```

Conceptually:

1. Run the destructor.
2. Deallocate storage.

Arrays must use matching syntax:

```cpp
Widget* widgets = new Widget[count];
delete[] widgets;
```

Mismatching `delete` and `delete[]` is undefined behavior.

### `malloc` and `free`

```cpp
void* storage = std::malloc(sizeof(Widget));
std::free(storage);
```

`malloc` obtains raw storage but does not ordinarily construct a C++ class object. `free` does not run a destructor.

Do not mix families:

```cpp
// free(new Widget);        // wrong
// delete malloc_storage;   // wrong
```

### Prefer higher-level RAII

```cpp
auto widget = std::make_unique<Widget>();
std::vector<Widget> widgets(count);
```

Direct manual allocation is mainly needed when implementing containers, allocators, pools, low-level runtimes, or placement/lifetime facilities.

### Interview question

**Question:** What does `new T` do that `malloc(sizeof(T))` does not?

**Answer:** It obtains appropriate storage and constructs a `T`, returning a typed pointer. `malloc` only obtains raw bytes.

---

## 6. Stack and heap terminology

"Stack object" commonly means automatic local object:

```cpp
Widget widget;
```

"Heap object" commonly means dynamically allocated object:

```cpp
auto widget = std::make_unique<Widget>();
```

Useful corrections:

- The C++ standard's core language uses storage-duration terms.
- A `unique_ptr` object may be on the stack while owning a dynamic object.
- A class such as `std::vector` may be automatic while its element storage is dynamic.
- A static object may be stored in `.data` or `.bss`, neither stack nor heap.
- Optimizers may place values in registers or eliminate storage.
- "Free store" is the C++ allocation abstraction; "heap" is a common implementation term. They often refer to the same underlying allocator but are not definitions of ownership.

### Interview question

**Question:** Is a local `std::vector<int>` entirely on the stack?

**Answer:** The vector control object usually has automatic storage, while its element buffer normally has dynamic storage.

---

## 7. Object lifetime boundaries

An object's lifetime is the interval during which the program may treat storage as containing that object, subject to language rules.

For a class object, construction establishes its valid state; destruction ends its lifetime.

```cpp
{
    Device device{42}; // lifetime begins through initialization
    device.start();    // valid use
}                     // destructor; lifetime ends
```

Storage and lifetime are not identical in manual-lifetime code:

```cpp
alignas(Device) std::byte storage[sizeof(Device)];
```

The bytes exist, but no `Device` necessarily exists there yet.

Low-level code can explicitly construct and destroy:

```cpp
Device* device = std::construct_at(
    reinterpret_cast<Device*>(storage), 42);

std::destroy_at(device);
```

Manual lifetime management has strict alignment, aliasing, reuse, and exception rules. Prefer standard containers/allocators unless implementing infrastructure.

### Lifetime of trivial objects

Even when no constructor or destructor call appears in machine code, the abstract lifetime rules still control legal access and aliasing.

### Interview question

**Question:** Can storage exist without a live object of the intended type in it?

**Answer:** Yes. Raw allocated or aligned storage may exist before construction and after destruction.

---

## 8. Scope and name hiding

Scope controls name visibility, not necessarily lifetime.

```cpp
int value = 1;

void f() {
    int value = 2; // hides outer value
    {
        int value = 3; // hides function-local value
    }
}
```

Common scopes:

- Block scope.
- Function parameter scope.
- Class scope.
- Namespace scope.
- Template parameter scope.
- Enumeration scope for scoped enums.

### Name out of scope, object still alive

```cpp
Device& device() {
    static Device instance;
    return instance;
}
```

The local name `instance` is visible only inside the function, while the object persists.

### Object dead while pointer name remains visible

```cpp
Device* pointer;

{
    Device local;
    pointer = &local;
}

// pointer is visible but dangles
```

### Interview question

**Question:** Does scope determine lifetime in every case?

**Answer:** No. They often align for ordinary locals, but static and dynamic objects demonstrate that visibility and lifetime are separate.

---

## 9. Borrowed handles and dangling

Non-owning handles include:

- Raw pointers.
- References.
- Iterators.
- `std::span`.
- `std::string_view`.
- Reference wrappers.
- Many library-specific views.

They do not keep the source alive.

### Dangling pointer

```cpp
int* pointer;
{
    int value = 10;
    pointer = &value;
}
// *pointer is invalid
```

### Dangling reference

```cpp
const int& bad_reference() {
    int value = 10;
    return value;
}
```

### Dangling view

```cpp
std::string_view view = std::string{"temporary"};
// temporary string is already destroyed after the statement
```

The view may still hold an address and length, but the characters no longer exist.

### Use-after-free

```cpp
int* pointer = new int{10};
delete pointer;
// *pointer is invalid
```

Setting one pointer to null does not repair other aliases:

```cpp
int* alias = pointer;
pointer = nullptr;
// alias still dangles
```

### Interview question

**Question:** Does a reference guarantee lifetime safety because it cannot be null?

**Answer:** No. It can refer to an object whose lifetime has ended, producing a dangling reference.

---

## 10. Returning pointers, references, and views

### Invalid local return

```cpp
const std::string& name() {
    std::string local = "sensor";
    return local; // dangling
}
```

The local dies when the function returns.

### Valid member return with contract

```cpp
class Device {
public:
    const std::string& name() const {
        return name_;
    }

private:
    std::string name_;
};
```

The reference remains valid only while:

- The `Device` remains alive.
- The member is not replaced or invalidated in a way that ends that referenced state.
- Concurrent mutation does not introduce a race.

### Return by value

```cpp
std::string name() const {
    return name_;
}
```

This gives the caller independent ownership and often uses efficient copy/move/elision. Prefer it when lifetime independence and encapsulation outweigh copy cost.

### Static return

A reference to a static object can remain valid until program termination, but global shared state and destruction-order concerns remain.

### Interview question

**Question:** When is returning `const T&` from a member safe?

**Answer:** When the caller respects that it borrows from the containing object and does not use the reference after the owner or relevant state becomes invalid.

---

## 11. Temporary objects

A temporary is often created as an intermediate result:

```cpp
std::string text = make_prefix() + make_suffix();
```

The addition may produce a temporary string used to initialize `text`.

Most temporaries are destroyed at the end of the **full expression**, usually the statement:

```cpp
consume(Widget{}); // temporary survives through consume, then is destroyed
```

### Parameter binding

```cpp
void print(const std::string& text);

print("hello");
```

A temporary `std::string` can be constructed and bound to the const reference. It survives until the full expression containing the call ends.

The callee must not store a reference for later:

```cpp
const std::string* saved{};

void save(const std::string& text) {
    saved = &text;
}

save(std::string{"temporary"});
// saved now dangles
```

### Materialization and optimization

Modern C++ prvalue rules can construct results directly in their final destination. Even when no temporary object is materialized at runtime, source-level lifetime semantics remain important.

### Interview question

**Question:** How long does a temporary bound to a const-reference function parameter live?

**Answer:** Through the full expression containing the function call, not for as long as any reference the function might store.

---

## 12. Temporary lifetime extension

Directly binding a local reference can extend a temporary's lifetime:

```cpp
const std::string& text = std::string{"hello"};
```

The temporary string lives as long as `text`.

Rvalue references can also extend lifetime in direct local binding:

```cpp
std::string&& text = std::string{"hello"};
```

### No re-extension through another reference

```cpp
const std::string& identity(const std::string& value) {
    return value;
}

const std::string& ref = identity(std::string{"hello"});
```

The temporary is bound to the function parameter only for the call's full expression. Returning the reference does not extend the temporary again. `ref` dangles after the initialization statement.

### Returning a temporary by reference

```cpp
const std::string& bad() {
    return std::string{"hello"};
}
```

The temporary does not survive as a valid returned object. Return by value instead.

### Prefer ownership over memorizing edge cases

When a reference or view may escape a full expression, use an owning value unless lifetime is unambiguous.

### Interview question

**Question:** Does passing a temporary through a function that returns its const reference extend the lifetime for the caller?

**Answer:** No. Lifetime extension is not transitive; the temporary dies at the end of the original full expression.

---

## 13. Value categories and lifetime intuition

A simplified model:

- **lvalue:** identifies an object with persistent identity.
- **prvalue:** computes/initializes a value, often associated with a temporary.
- **xvalue:** identifies an object whose resources may be reused.
- **rvalue:** prvalue or xvalue.

References interact with value categories:

```cpp
T&        // normally binds mutable lvalues
const T&  // binds lvalues and rvalues read-only
T&&       // binds rvalues in non-deduced ordinary use
```

`std::move(object)` does not move or end lifetime. It casts the expression to an xvalue so a move overload may be selected:

```cpp
std::string target = std::move(source);
```

`source` remains alive but is in a valid, possibly changed state defined by the type's move contract.

### Interview question

**Question:** Does `std::move(x)` destroy `x` or shorten its lifetime?

**Answer:** No. It is a cast enabling move selection. `x` remains alive until its normal lifetime ends.

---

## 14. Container invalidation

A live container does not guarantee that every pointer/reference/iterator into it remains valid.

### Vector reallocation

```cpp
std::vector<int> values;
values.reserve(1);
values.push_back(10);

int& first = values[0];
values.push_back(20); // may reallocate

// first may now dangle
```

Reallocation moves/copies elements to new storage and invalidates pointers, references, and iterators to old elements.

### Erasure

Erasing from a vector invalidates iterators/references at or after the erased position. Other containers have different rules.

### `reserve` versus `resize`

- `reserve(n)` changes capacity without changing element count.
- `resize(n)` changes size and constructs/destroys elements.

Reserving sufficient capacity can prevent reallocation until capacity is exceeded, but it is not a universal lifetime guarantee.

### Unordered containers

Rehashing invalidates iterators, while references/pointers to elements have different standard guarantees. Always check the specific operation/container rules rather than generalizing.

### Interview question

**Question:** Why can a reference to `vector[0]` dangle while the vector itself remains alive?

**Answer:** Reallocation can end the old element object's lifetime and construct elements in a new storage block.

---

## 15. Lambda, callback, and thread lifetimes

### Reference capture

```cpp
std::function<void()> make_callback() {
    int count = 0;

    return [&count] {
        ++count;
    }; // returned lambda holds dangling reference
}
```

Capture by value when the callback must own independent state:

```cpp
return [count]() mutable {
    ++count;
};
```

### Capturing `this`

```cpp
class Device {
public:
    auto callback() {
        return [this] {
            poll();
        };
    }
};
```

The lambda does not keep the object alive. Calling it after `Device` destruction is invalid.

Shared lifetime can be explicit:

```cpp
auto self = shared_from_this();
return [self] {
    self->poll();
};
```

This requires an appropriate shared-ownership design and can create cycles if callbacks are stored by the same object. A `weak_ptr` may be better.

### Detached/asynchronous work

A thread or asynchronous operation can easily outlive locals:

```cpp
std::thread worker([&local] {
    use(local);
});
```

Joining before local destruction may make it safe. `std::jthread` helps tie joining to scope, but captured object lifetimes still require review.

### Interview question

**Question:** Does capturing `this` by value copy the entire object?

**Answer:** No. Traditional `[this]` captures the pointer value. The pointed-to object must remain alive.

---

## 16. Ownership models

### Direct value ownership

```cpp
Device device;
```

The containing scope/object owns the value directly.

### Exclusive dynamic ownership

```cpp
std::unique_ptr<Device> device;
```

One owner; movable, not copyable.

### Shared ownership

```cpp
std::shared_ptr<Device> device;
```

Reference-counted ownership. The object dies when the last owning shared pointer dies.

Costs include allocation/control block, reference-count updates, and cycle risk.

### Weak observation

```cpp
std::weak_ptr<Device> observer;
```

Does not extend lifetime. Call `lock()` to obtain temporary shared ownership if the object still exists.

### Borrowing

```cpp
Device& required;
Device* optional;
std::span<const std::byte> bytes;
```

No ownership. The source must outlive every use.

### Interview question

**Question:** When should `shared_ptr` be used?

**Answer:** When the design genuinely has multiple owners whose lifetimes cannot be nested or centralized, not merely because ownership is unclear.

---

## 17. Static and thread-local lifetimes

Namespace-scope and static local objects live until program termination, but dynamic initialization order across translation units can cause dependencies to fail.

```cpp
Registry& registry() {
    static Registry instance;
    return instance;
}
```

This delays initialization until first use.

Destruction order can still matter if one static object's destructor accesses another already-destroyed static.

Thread-local objects are initialized per thread and destroyed when that thread exits, subject to implementation/platform details. References escaping the originating thread's lifetime can dangle.

### Interview question

**Question:** Why can process-lifetime objects still have lifetime bugs?

**Answer:** Their initialization and destruction order relative to other static objects may be unsafe, especially across translation units.

---

## 18. Placement construction and storage reuse

Low-level systems code may separate allocation from object construction:

```cpp
void* storage = ::operator new(sizeof(Device));

Device* device = new (storage) Device{42}; // placement new

device->~Device();
::operator delete(storage);
```

Placement new does not allocate; it constructs at the supplied address.

Modern library code can use:

```cpp
std::construct_at(pointer, arguments...);
std::destroy_at(pointer);
```

### Responsibilities

You must ensure:

- Correct size and alignment.
- Storage is available.
- Construction happens exactly as required.
- Destruction occurs for non-trivial objects.
- No invalid old pointers are used after type-changing reuse.
- Exception cleanup is correct.
- Array and union lifetime rules are respected.

`std::launder` is needed in certain advanced storage-reuse scenarios, but it is not a general fix for aliasing or lifetime violations.

### Use cases

- Containers.
- Object pools.
- Arenas.
- Shared-memory layouts.
- Embedded fixed storage.
- Variant-like implementations.

### Interview question

**Question:** Does placement new allocate memory?

**Answer:** No. It constructs an object in storage supplied by the caller.

---

## 19. Lifetime and polymorphism

Deleting through a base pointer requires a suitable virtual destructor:

```cpp
class Device {
public:
    virtual ~Device() = default;
};

Device* device = new Camera;
delete device; // complete destruction
```

Without a virtual base destructor, deletion through `Device*` is undefined behavior.

During construction and destruction, the active dynamic-dispatch level changes. Derived state is not active before derived construction or after derived destruction.

### Slicing

```cpp
Camera camera;
Device device = camera;
```

This creates an independent `Device` containing only the copied base subobject. It does not preserve the derived dynamic identity.

### Interview question

**Question:** What lifetime problem does a virtual destructor solve?

**Answer:** It ensures deletion through a base pointer runs the complete derived-to-base destruction chain.

---

## 20. Common lifetime bugs

### Returning a local reference

Always dangling.

### Storing a function-parameter reference to a temporary

The temporary normally dies at the end of the caller's full expression.

### Using a vector element after reallocation

The container may live while the old element address no longer does.

### Capturing locals by reference in escaping callbacks

Callback lifetime exceeds captured state.

### Raw owning pointers

Cleanup responsibility is unclear and may be duplicated or forgotten.

### Shared-pointer cycles

```text
A owns B
B owns A
```

Neither count reaches zero. Break non-owning back edges with `weak_ptr` when shared ownership is truly intended.

### Use after move

A moved-from standard object remains valid but has type-specific/unspecified state. Only perform operations permitted by its contract before assigning a new value.

### Double destruction/manual lifetime errors

Placement-managed objects require exact construction/destruction tracking.

### Interview question

**Question:** What single question detects many lifetime bugs?

**Answer:** "Can this pointer, reference, iterator, view, callback, or thread outlive the object it accesses?"

---

## 21. Embedded and real-time lifetime design

Prefer lifetimes that are statically obvious:

- Automatic RAII for bounded operations.
- Direct composition for device ownership.
- Static allocation for process-lifetime hardware abstractions when startup order is controlled.
- Fixed-capacity containers and pools where dynamic allocation is prohibited.
- Explicit shutdown for threads, DMA, interrupts, and callbacks before referenced state is destroyed.

### Interrupt and DMA hazards

A stack buffer passed to asynchronous DMA may die before transfer completion:

```cpp
void transmit() {
    std::array<std::byte, 128> buffer{};
    start_dma(buffer.data(), buffer.size());
} // unsafe if DMA continues using buffer
```

The buffer must remain alive until completion, perhaps through a persistent owner, static pool, or synchronous wait.

An ISR callback registered with a pointer to an object must be unregistered or disabled before object destruction.

### Determinism

Heap avoidance does not automatically solve lifetime. A pointer into a fixed pool can still dangle after slot reuse. Generation counters, ownership state, and clear protocols may be necessary.

### Interview question

**Question:** Why is passing a local buffer to asynchronous DMA dangerous?

**Answer:** The function may return and end the buffer's lifetime while hardware still reads or writes its address.

---

## 22. Diagnosing lifetime failures

Useful tools and techniques include:

- Compiler warnings such as return-local-address and reorder warnings.
- AddressSanitizer for use-after-free, stack-use-after-scope, and buffer errors.
- UndefinedBehaviorSanitizer for relevant undefined behavior.
- MemorySanitizer for uninitialized reads where supported.
- Static analyzers and lifetime profiles.
- Debug iterator modes.
- Ownership annotations and code review.
- Hardware watchpoints and MPU/MMU guards in embedded work.
- Stress testing asynchronous shutdown and cancellation.

Tools cannot replace a correct ownership model. They find exercised violations, not every possible lifetime bug.

### Interview question

**Question:** Which sanitizer is most directly useful for heap use-after-free?

**Answer:** AddressSanitizer.

---

## 23. Lifetime design workflow

For every object or handle, ask:

1. What storage duration does the object have?
2. When exactly does its lifetime begin and end?
3. Who owns it?
4. Which names or handles borrow it?
5. Can a borrow escape its owner's scope?
6. Can a container operation invalidate it?
7. Can asynchronous work outlive it?
8. Does moving the owner affect addresses or invariants?
9. Is cleanup deterministic on every exit path?
10. Are static initialization/destruction dependencies safe?
11. Does hardware continue accessing the storage?
12. Is dynamic allocation acceptable for worst-case timing?

### Interview question

**Question:** How should you explain a lifetime design in an interview?

**Answer:** Name the owner, storage duration, destruction trigger, all borrowers, invalidation events, and synchronization/shutdown mechanism.

---

## 24. Final comparison table

| Pattern | Storage/lifetime | Ownership | Main risk |
|---|---|---|---|
| `T object;` local | Automatic; to scope exit | Direct local owner | Stack size, escaping borrow |
| `static T object;` | Static; program/thread rules | Process/static subsystem | Init/destruction order, shared state |
| `new T` raw pointer | Dynamic; until correct delete | Unclear unless documented | Leak, double delete |
| `unique_ptr<T>` | Pointee dynamic | One explicit owner | Dangling external borrowers |
| `shared_ptr<T>` | Dynamic; until last owner | Shared | Cycles, overhead, unclear graph |
| `T&` / `T*` | Does not control source | Borrowed | Dangling |
| `span<T>` / `string_view` | Does not control source | Borrowed range/view | Dangling, invalidation |
| Container element reference | Follows element lifetime | Container owns element | Reallocation/erase invalidation |
| Lambda `[&x]` | Follows closure, not `x` | Borrowed capture | Escaping callback |
| Placement object | Manually controlled | Custom | Alignment/lifetime mistakes |

---

## Final interview checklist

You should be able to explain:

- Scope versus storage duration versus lifetime versus ownership.
- Automatic, static, thread, and dynamic storage durations.
- Why stack/heap language is incomplete.
- `new`/`delete` versus `malloc`/`free`.
- Construction/destruction versus allocation/deallocation.
- RAII ownership models.
- Borrowed pointers, references, spans, and views.
- Returning values versus borrowed references.
- Full-expression temporary lifetime.
- Direct lifetime extension and its non-transitivity.
- Value categories and what `std::move` does not do.
- Container invalidation.
- Lambda, callback, thread, DMA, and ISR lifetime hazards.
- Static initialization/destruction order.
- Placement construction and manual lifetime management.
- Virtual destruction and slicing.
- Sanitizers and systematic lifetime review.
