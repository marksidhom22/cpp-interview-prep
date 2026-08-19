# Modern C++ Language Features and Iteration

Modern C++ is not a single version or one special syntax. It is a style of writing type-safe, ownership-aware, expressive code using features introduced across C++11, C++14, C++17, C++20, and later standards.

This chapter focuses on high-frequency language and library features used in interviews and production systems code, especially `auto`, range-based `for`, structured bindings, lambdas, safer types, compile-time evaluation, and ranges.

Related chapters:

- [`01_cpp_references_vs_pointers.md`](./01_cpp_references_vs_pointers.md) for reference deduction and lifetime.
- [`02_cpp_const_brief_interview_notes.md`](./02_cpp_const_brief_interview_notes.md) for const syntax.
- [`08_stack_heap_lifetime_scope_temporaries.md`](./08_stack_heap_lifetime_scope_temporaries.md) for borrowed views and temporary lifetime.

---

## Part I - Five-Minute Interview Review

### `auto`: mandatory rules

```cpp
const int value = 10;
const int& reference = value;

auto a = value;             // int
auto b = reference;         // int
const auto& c = reference;  // const int&
auto& d = reference;        // const int&
auto&& e = value;           // const int& because value is an lvalue
```

- Plain `auto` behaves mostly like template by-value deduction: it normally drops references and top-level const. See [`auto` type deduction](#2-auto-type-deduction).
- Add `&`, `const &`, `*`, or `&&` when those semantics are required. See [`auto` with references, pointers, and const](#3-auto-with-references-pointers-and-const).
- `auto` does not mean dynamic typing. The compiler determines one static type at compile time.
- `auto x{1}` is an `int`, while `auto x = {1}` is usually `std::initializer_list<int>`. See [Brace deduction](#4-brace-deduction-and-auto-pitfalls).
- Use `decltype` when you need the declared/expression type rules rather than ordinary `auto` deduction. See [`decltype` and `decltype(auto)`](#5-decltype-and-decltypeauto).

### Range-based `for`: mandatory rules

```cpp
for (auto value : values) {
    // value is a copy
}

for (auto& value : values) {
    // mutable reference to each element
}

for (const auto& value : values) {
    // read-only reference; no element copy
}

for (auto&& value : range) {
    // generic binding; useful for proxy/range element types
}
```

See [Range-based for fundamentals](#6-range-based-for-fundamentals) and [Choosing the loop variable](#8-choosing-the-loop-variable).

Conceptually:

```cpp
auto&& range = range_expression;
auto begin = begin(range);
auto end = end(range);

for (; begin != end; ++begin) {
    item_declaration = *begin;
    // loop body
}
```

The exact language transformation depends on the C++ version and range type. See [How range-based for works](#7-how-range-based-for-works).

### High-frequency modern features

| Feature | Main purpose |
|---|---|
| [`auto`](#2-auto-type-deduction) | Infer a static type from an initializer |
| [`decltype`](#5-decltype-and-decltypeauto) | Obtain a type from a declaration/expression |
| [Range-based `for`](#6-range-based-for-fundamentals) | Iterate over a range without manual index/iterator syntax |
| [Structured bindings](#10-structured-bindings) | Decompose tuple-like, array, or class values |
| [Lambda](#11-lambdas) | Create a local callable object with optional captures |
| [`nullptr`](#15-nullptr) | Type-safe null pointer value |
| [`enum class`](#16-enum-class) | Scoped, strongly typed enumeration |
| [`using`](#17-using-aliases) | Clear type and template aliases |
| [`constexpr`](#18-constexpr-consteval-and-constinit) | Permit/require compile-time-capable evaluation |
| [`consteval`](#18-constexpr-consteval-and-constinit) | Require compile-time calls |
| [`constinit`](#18-constexpr-consteval-and-constinit) | Require static initialization |
| [`noexcept`](#19-noexcept) | State and query non-throwing behavior |
| [`if` initializer](#20-initialization-statements-in-if-and-switch) | Limit temporary/helper variable scope |
| [CTAD](#21-class-template-argument-deduction-ctad) | Deduce class-template arguments from construction |
| [Concepts](#22-if-constexpr-and-concepts) | Constrain templates and improve interfaces |
| [`optional` / `variant`](#23-stdoptional-stdvariant-and-vocabulary-types) | Type-safe absence and alternatives |
| [`span` / `string_view`](#24-stdspan-and-stdstring_view) | Cheap non-owning views |
| [`std::ranges`](#14-c20-ranges-and-views) | Composable range algorithms and lazy views |

### Five interview checks

1. **Does `auto` preserve a reference?** Plain `auto` normally does not; use `auto&`, `const auto&`, or `auto&&`.
2. **Does `for (auto x : values)` modify the elements?** No; it normally modifies a copy.
3. **Why use `const auto&` in a loop?** It avoids element copies and prevents mutation through the loop variable.
4. **When is an index loop still appropriate?** When the index itself, a stride, multiple ranges, mutation/erasure control, or non-range traversal is required.
5. **Are ranges and views owners?** Views are often non-owning and lazy; lifetime must be checked.

---

## Part II - Detailed Reference

## 1. What “modern C++” means

Modern C++ generally means using the language's type system, RAII, value semantics, standard library, and newer expressive features instead of writing “C with classes.”

Examples of the shift:

```cpp
// Manual ownership
Widget* widget = new Widget;
delete widget;

// Explicit ownership
auto widget = std::make_unique<Widget>();
```

```cpp
// Manual indexing when the index is irrelevant
for (std::size_t i = 0; i < values.size(); ++i) {
    process(values[i]);
}

// Express the intent directly
for (const auto& value : values) {
    process(value);
}
```

Modern does not mean “always use the newest syntax.” A classic indexed loop may be best when the index matters. The goal is to express intent, ownership, lifetime, and constraints clearly.

### Version awareness

Features have standard-version requirements:

| Standard | Selected features |
|---|---|
| C++11 | `auto` expansion, range-for, lambdas, `nullptr`, `enum class`, move semantics, `constexpr`, `noexcept` |
| C++14 | Generic lambdas, relaxed constexpr, return-type deduction |
| C++17 | Structured bindings, `if` initializer, CTAD, inline variables, `if constexpr`, `string_view`, `optional`, `variant` |
| C++20 | Concepts, ranges, `consteval`, `constinit`, abbreviated templates, designated initialization, expanded constexpr |
| C++23 | Additional ranges and lifetime/utility improvements |

Know the standard configured by the target codebase, compiler, embedded toolchain, and safety standard.

### Interview question

**Question:** What makes C++ code “modern”?

**Answer:** Clear ownership through RAII, correct value/reference semantics, strong types, standard-library abstractions, and language features that express intent without hiding important cost or lifetime behavior.

---

## 2. `auto` type deduction

`auto` asks the compiler to deduce a static type from the initializer:

```cpp
auto count = 10;        // int
auto voltage = 3.3;     // double
auto name = std::string{"imu"}; // std::string
```

The variable does not change type later:

```cpp
auto value = 10; // int
value = 20;      // valid
// value = "text"; // error
```

### Why use it?

`auto` is valuable when:

- The type is obvious from the initializer.
- The exact type is verbose.
- The type is an iterator or lambda closure.
- Template types may change while the intended operation remains the same.
- Repeating the type creates opportunities for accidental conversions.

```cpp
auto iterator = devices.find(id);
auto owner = std::make_unique<Device>();
auto callback = [](int value) { return value * 2; };
```

### Avoid obscuring important semantics

This may hide too much:

```cpp
auto result = perform_operation();
```

If ownership, units, precision, or cost are not obvious, an explicit type or clearer function name may communicate more.

```cpp
std::unique_ptr<Device> device = create_device();
Milliseconds timeout = read_timeout();
```

### Avoid accidental conversion from repeated types

```cpp
std::vector<std::uint64_t> values;
auto size = values.size(); // correct container size_type
```

An explicit `int` could narrow or create signed/unsigned issues:

```cpp
int size = values.size(); // possible narrowing
```

### Interview question

**Question:** Is `auto` dynamic typing?

**Answer:** No. The compiler deduces a fixed static type at compile time; all normal type checking still applies.

---

## 3. `auto` with references, pointers, and const

Plain `auto` normally drops references and top-level const:

```cpp
const int original = 42;
const int& reference = original;

auto a = original;  // int
auto b = reference; // int
```

Both `a` and `b` are independent mutable integers.

### Preserve reference semantics

```cpp
auto& c = reference;       // const int&
const auto& d = original;  // const int&
```

`auto&` preserves reference binding, and low-level/referred-to const participates in deduction.

### Mutable reference

```cpp
std::vector<int> values{1, 2, 3};

for (auto& value : values) {
    value *= 2;
}
```

### Pointer deduction

```cpp
const int* pointer = &original;

auto p1 = pointer;  // const int*
auto* p2 = pointer; // const int*
```

`auto*` documents that a pointer is expected and rejects a non-pointer initializer.

### `auto&&`

Outside template discussions, `auto&&` uses forwarding-reference deduction:

```cpp
int value = 10;

auto&& a = value; // int&
auto&& b = 20;    // int&&
```

Reference collapsing produces:

```text
T&  + &  -> T&
T&  + && -> T&
T&& + &  -> T&
T&& + && -> T&&
```

This makes `auto&&` useful when generic code should bind whatever category an expression provides.

### Interview question

**Question:** What is the type of `auto x = ref` when `ref` is `const Widget&`?

**Answer:** `Widget`; plain by-value `auto` drops the reference and top-level const, creating a copy if initialization requires one.

---

## 4. Brace deduction and `auto` pitfalls

These forms are different:

```cpp
auto a{1};    // int
auto b = {1}; // std::initializer_list<int>
auto c = {1, 2, 3}; // std::initializer_list<int>
```

This is invalid:

```cpp
// auto d{1, 2}; // direct-list auto requires one element
```

Elements of an initializer list must have a compatible deduced type:

```cpp
// auto values = {1, 2.5}; // cannot deduce one element type
```

### Accidental copies

```cpp
const auto item = container.front(); // copy
const auto& item_ref = container.front(); // borrow
```

A copy may be correct if the element must remain valid after container mutation. A reference may be correct if avoiding the copy matters and lifetime is safe.

### Proxy types

Some APIs return proxy objects rather than real references:

```cpp
std::vector<bool> bits{true, false};

auto bit = bits[0]; // proxy type, not necessarily bool
```

`auto` accurately preserves the returned proxy type, which can surprise code expecting a value. Request the semantic value explicitly when desired:

```cpp
bool bit_value = bits[0];
```

### `auto` can hide narrowing or precision decisions

```cpp
auto duration = 1s; // good if chrono literal and type are known
auto number = calculate(); // inspect whether float/double/integer matters
```

Use strong types and meaningful names rather than relying on `auto` to solve semantic ambiguity.

### Interview question

**Question:** Why can `auto value = {1}` behave differently from `auto value{1}`?

**Answer:** Copy-list initialization with `auto` deduces an `initializer_list`, while direct-list initialization with one element deduces the element type.

---

## 5. `decltype` and `decltype(auto)`

`decltype` obtains a type without evaluating the expression.

```cpp
int value = 10;
const int& reference = value;

decltype(value) a = 20;     // int
decltype(reference) b = value; // const int&
```

### Special rule for unparenthesized names

For an unparenthesized identifier/member access, `decltype(name)` produces the declared type.

For other expressions, value category affects the result:

```cpp
decltype((value)) c = value; // int&
```

Because `(value)` is an lvalue expression, `decltype((value))` is `int&`.

A useful summary:

```text
decltype(expression)
lvalue expression  -> T&
xvalue expression  -> T&&
prvalue expression -> T
```

except for the special unparenthesized-name rule.

### `decltype(auto)`

`decltype(auto)` uses `decltype` rules for deduction:

```cpp
decltype(auto) get_reference(int& value) {
    return (value); // returns int&
}
```

Without parentheses:

```cpp
decltype(auto) get_value_member() {
    return object.member; // special declared-type rule may apply
}
```

This power can accidentally return dangling references. Use it only when exact propagation is intended and reviewed.

### `auto` return type

```cpp
auto get_value() {
    return object.member; // deduces by value
}
```

Plain `auto` return deduction generally drops references similarly to variable deduction.

### Trailing return type

```cpp
template<class A, class B>
auto add(const A& a, const B& b) -> decltype(a + b) {
    return a + b;
}
```

This was especially important before C++14 return deduction and remains useful when the return type needs explicit expression-dependent documentation.

### Interview question

**Question:** What is the difference between `decltype(x)` and `decltype((x))` for an `int x`?

**Answer:** `decltype(x)` is `int` by the unparenthesized-name rule; `decltype((x))` is `int&` because `(x)` is an lvalue expression.

---

## 6. Range-based `for` fundamentals

A range-based loop iterates through elements:

```cpp
std::vector<int> values{10, 20, 30};

for (int value : values) {
    std::cout << value << '\n';
}
```

The syntax is:

```cpp
for (item_declaration : range_expression) {
    body
}
```

Examples of ranges include:

- Built-in arrays.
- Standard containers.
- Types with suitable `begin()` and `end()`.
- Types with free `begin`/`end` found through lookup.
- C++20 range views.

### Why use it?

It expresses “for every element” without exposing irrelevant iterator/index mechanics.

```cpp
for (const auto& sensor : sensors) {
    sensor.poll();
}
```

This is clearer than:

```cpp
for (std::size_t i = 0; i < sensors.size(); ++i) {
    sensors[i].poll();
}
```

when the index is never used.

### It is not always superior

Use another loop when you need:

- The numeric index.
- A stride other than one.
- Simultaneous traversal of multiple ranges.
- Manual iterator control.
- Erasure during traversal.
- Reverse iteration without a range adaptor.
- Early manipulation of begin/end positions.

### Interview question

**Question:** When should a range-based loop replace an indexed loop?

**Answer:** When the intent is simply to process every element and neither the index nor custom traversal control is required.

---

## 7. How range-based `for` works

A simplified conceptual transformation is:

```cpp
for (const auto& item : collection) {
    process(item);
}
```

into something similar to:

```cpp
{
    auto&& hidden_range = collection;
    auto hidden_begin = begin(hidden_range);
    auto hidden_end = end(hidden_range);

    for (; hidden_begin != hidden_end; ++hidden_begin) {
        const auto& item = *hidden_begin;
        process(item);
    }
}
```

The compiler does not necessarily generate these exact variable names or instructions. This model explains the semantics.

### Range expression is evaluated once

```cpp
for (const auto& item : get_collection()) {
}
```

`get_collection()` is evaluated once, not for every iteration.

The hidden `auto&&` range binding can keep the returned range object alive for the loop under the applicable temporary-lifetime rules. Chained intermediate temporaries have had version-sensitive lifetime rules; a named owner or init-statement is clearer when in doubt.

### Begin and end

For a built-in array, the language knows the array bounds.

For a class with member operations:

```cpp
class Collection {
public:
    Iterator begin();
    Sentinel end();
};
```

the loop can use those operations.

Associated free `begin`/`end` functions can support custom range types through argument-dependent lookup.

### Iterator and sentinel can differ

Since C++17, begin and end types do not always need to be identical, enabling sentinel-based ranges.

### Loop body and invalidation

The loop obtains begin/end state. Mutating the container structurally during iteration can invalidate those iterators:

```cpp
for (const auto& value : values) {
    values.push_back(value); // dangerous if reallocation occurs
}
```

### Interview question

**Question:** Is the range expression evaluated once or once per iteration?

**Answer:** Once. The loop binds a hidden range object/reference and obtains traversal state from it.

---

## 8. Choosing the loop variable

This choice controls copying, mutation, constness, and proxy behavior.

### By value

```cpp
for (auto value : values) {
    process(value);
}
```

Each iteration initializes a local value. Use this when:

- Elements are cheap to copy.
- You intentionally need an independent copy.
- The algorithm modifies only the copy.
- A stable local value is needed despite later container changes.

### Mutable reference

```cpp
for (auto& value : values) {
    value.normalize();
}
```

Use when modifying actual elements.

### Const reference

```cpp
for (const auto& value : values) {
    inspect(value);
}
```

This is the common default for large read-only elements.

### Forwarding/generic reference

```cpp
for (auto&& value : range) {
    process(value);
}
```

This adapts to the range's element reference type and handles proxy/reference-like results. It is common in generic range code. It does not automatically mean the function should move from every element.

### Const by value

```cpp
for (const auto value : values) {
}
```

This still copies each element; const only prevents changing the local copy. It rarely provides an advantage over `auto value` or `const auto& value`.

### Explicit type danger

```cpp
std::map<std::string, int> counts;

for (const std::pair<std::string, int>& item : counts) {
}
```

The map's actual value type is:

```cpp
std::pair<const std::string, int>
```

The mismatched explicit type may cause a temporary conversion and copy each iteration. Prefer:

```cpp
for (const auto& item : counts) {
}
```

### Interview question

**Question:** Why is `const auto&` a strong default for read-only container traversal?

**Answer:** It avoids copies, preserves the actual element type, and prevents mutation through the loop variable.

---

## 9. Index loops, iterator loops, and range loops

Each form communicates different needs.

### Index loop

```cpp
for (std::size_t index = 0; index < values.size(); ++index) {
    use(index, values[index]);
}
```

Best when:

- The index is part of the operation.
- Random access is required.
- Traversing multiple indexed arrays.
- Applying a stride or neighborhood.
- Interfacing with index-based APIs.

For reverse loops, unsigned underflow is a common bug:

```cpp
// for (std::size_t i = values.size() - 1; i >= 0; --i) // wrong
```

Use reverse iterators, reverse views, or a safe pattern.

C++20 provides `std::ssize` for a signed size when signed arithmetic is appropriate.

### Iterator loop

```cpp
for (auto iterator = values.begin(); iterator != values.end();) {
    if (should_remove(*iterator)) {
        iterator = values.erase(iterator);
    } else {
        ++iterator;
    }
}
```

Best for explicit iterator operations, erasure, subranges, and non-indexable containers.

### Range loop

```cpp
for (const auto& value : values) {
    process(value);
}
```

Best for direct element traversal.

### Algorithm

```cpp
std::ranges::for_each(values, process);
```

Best when the operation composes with other algorithms or the algorithm name communicates intent.

### Interview question

**Question:** Which loop form is best when erasing selected vector elements during traversal?

**Answer:** An explicit iterator loop using the iterator returned by `erase`, or an appropriate erase/remove algorithm.

---

## 10. Structured bindings

Structured bindings decompose an object:

```cpp
std::pair<int, std::string> entry{42, "camera"};

auto [id, name] = entry;
```

This creates value-like bindings according to the declaration.

### Avoid copies with references

```cpp
auto& [id, name] = entry;
name = "imu"; // modifies entry.second
```

Read-only borrowing:

```cpp
const auto& [id, name] = entry;
```

### Maps

```cpp
for (const auto& [key, value] : counts) {
    std::cout << key << ": " << value << '\n';
}
```

For a map, `key` is effectively const because keys cannot be modified in place without breaking ordering/hash invariants.

To modify mapped values:

```cpp
for (auto& [key, value] : counts) {
    ++value;
}
```

### Arrays and tuple-like types

```cpp
int coordinates[2]{10, 20};
auto [x, y] = coordinates;
```

`std::tuple`, `std::pair`, `std::array`, and user-defined tuple-like types can participate.

### `if` with structured binding

```cpp
if (auto [iterator, inserted] = map.insert({key, value}); inserted) {
    // inserted successfully
}
```

The bindings remain scoped to the `if` statement.

### Interview question

**Question:** What is the difference between `auto [a, b] = pair` and `auto& [a, b] = pair`?

**Answer:** The first creates value bindings based on a copied object; the second binds to the original pair's components and can modify them when allowed.

---

## 11. Lambdas

A lambda creates an unnamed callable object:

```cpp
auto square = [](int value) {
    return value * value;
};

int result = square(5);
```

Conceptually, the compiler generates a unique closure type with an `operator()`.

### Capture list

```cpp
[]        // capture nothing
[=]       // implicitly capture used local variables by value
[&]       // implicitly capture used local variables by reference
[x]       // capture x by value
[&x]      // capture x by reference
[this]    // capture this pointer
[*this]   // capture a copy of the current object (C++17)
```

Prefer explicit captures for asynchronous or long-lived callbacks because lifetime and ownership are visible.

### Value capture

```cpp
int factor = 2;

auto multiply = [factor](int value) {
    return factor * value;
};
```

The closure stores its own copy of `factor`.

### Reference capture

```cpp
int total = 0;

auto add = [&total](int value) {
    total += value;
};
```

The closure borrows `total`. It must not outlive it.

### `mutable`

A lambda's call operator is const by default for value captures:

```cpp
int count = 0;

auto next = [count]() mutable {
    return ++count;
};
```

This changes the closure's private captured copy, not the original `count`.

### Init-capture

```cpp
auto task = [owner = std::make_unique<Device>()]() mutable {
    owner->run();
};
```

Init-capture can move ownership into a closure.

### Generic lambda

```cpp
auto print = [](const auto& value) {
    std::cout << value;
};
```

This behaves like a callable object with a templated call operator.

### Interview question

**Question:** What does a lambda capture by value actually store?

**Answer:** The closure object stores its own member-like copy of the captured value; `mutable` permits changing that copy.

---

## 12. Lambda lifetime and `this`

A lambda may outlive captured references:

```cpp
std::function<void()> make_callback() {
    int value = 10;

    return [&value] {
        std::cout << value;
    }; // dangling reference after return
}
```

Capture by value for independent lifetime:

```cpp
return [value] {
    std::cout << value;
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

private:
    void poll();
};
```

`[this]` stores a pointer; it does not copy or own the `Device`. The callback dangles after the object dies.

`[*this]` captures an object copy:

```cpp
return [*this] {
    poll();
};
```

This requires the object to be copyable and gives snapshot-like semantics that may still be inappropriate for resource owners.

### Shared and weak lifetime

An asynchronous callback can capture shared ownership:

```cpp
auto self = shared_from_this();

return [self] {
    self->poll();
};
```

This keeps the object alive but can create ownership cycles. A `weak_ptr` capture plus `lock()` often represents observation more accurately.

### Interview question

**Question:** Does `[this]` keep the object alive?

**Answer:** No. It copies the pointer value; the caller must ensure the object outlives every callback invocation.

---

## 13. Algorithms versus handwritten loops

The standard library often names the intent:

```cpp
auto iterator = std::find(values.begin(), values.end(), target);
std::sort(values.begin(), values.end());
auto total = std::accumulate(values.begin(), values.end(), 0);
```

C++20 ranges reduce iterator pairs:

```cpp
auto iterator = std::ranges::find(values, target);
std::ranges::sort(values);
```

### Why algorithms help

- They communicate intent.
- Iterator/range boundaries are centralized.
- They reduce indexing errors.
- Library implementations may optimize well.
- They compose with predicates and projections.

### When a loop is clearer

Use a loop when:

- Control flow is complex.
- Multiple effects occur.
- Early exits have domain meaning.
- State transitions are clearer procedurally.
- Algorithm composition becomes harder to read than the operation.

Do not replace readable loops with an opaque chain merely because ranges are newer.

### Projection example

```cpp
std::ranges::sort(devices, {}, &Device::id);
```

This sorts using each device's ID without a custom comparison lambda.

### Interview question

**Question:** Why prefer `std::ranges::find(values, target)` over a manual search loop?

**Answer:** It names the operation, reduces boundary bookkeeping, works generically, and returns the matching iterator with standard behavior.

---

## 14. C++20 ranges and views

Views provide lazy transformations:

```cpp
auto even_squares =
    values
    | std::views::filter([](int value) { return value % 2 == 0; })
    | std::views::transform([](int value) { return value * value; });

for (int value : even_squares) {
    process(value);
}
```

### Lazy evaluation

The filter and transform usually run as elements are requested. They do not necessarily allocate a new container.

### Views often borrow

A view may refer to an existing range:

```cpp
auto filtered = values | std::views::filter(predicate);
```

If `values` dies, `filtered` may dangle.

Some adaptors own/move an rvalue range depending on the adaptor and standard version, but never assume lifetime without inspecting the view type and construction.

### Mutation

A view can expose mutable elements if the underlying range and view permit it. "View" does not inherently mean const.

### Complexity

Lazy composition can avoid temporary allocations, but repeated traversal may repeat predicate/transformation work. Document single-pass versus multi-pass expectations.

### Interview question

**Question:** Does a range view normally create a container of transformed values?

**Answer:** No. It usually represents a lazy adaptor evaluated during traversal, with ownership and lifetime depending on the particular view.

---

## 15. `nullptr`

Before C++11, code used `0` or `NULL`:

```cpp
void select(int);
void select(Device*);

select(0); // selects int
```

`nullptr` has type `std::nullptr_t` and expresses pointer intent:

```cpp
select(nullptr); // selects Device*
```

It converts to pointer and pointer-to-member types, but not to arbitrary integer parameters.

### Generic code

```cpp
auto pointer = nullptr; // std::nullptr_t
```

This is not `Device*`. If the pointer type matters:

```cpp
Device* pointer = nullptr;
```

### Avoid C-style null macros in C++ APIs

Use `nullptr` consistently for:

- Initialization.
- Resetting non-owning pointers.
- Null comparisons.
- Optional pointer arguments.

Smart pointers usually compare/reset naturally:

```cpp
std::unique_ptr<Device> device;
if (!device) {
}
```

### Interview question

**Question:** Why is `nullptr` safer than `0`?

**Answer:** It has a dedicated null-pointer type, so overload resolution treats it as pointer intent rather than an integer.

---

## 16. `enum class`

Unscoped enum values enter the surrounding scope and convert implicitly to integers:

```cpp
enum Color {
    Red,
    Green
};
```

Scoped enumeration:

```cpp
enum class Color : std::uint8_t {
    Red,
    Green
};
```

Usage requires qualification:

```cpp
Color color = Color::Red;
```

There is no ordinary implicit integer conversion:

```cpp
// int value = Color::Red; // error
```

Use an explicit cast when needed:

```cpp
auto raw = static_cast<std::uint8_t>(color);
```

### Benefits

- Prevents enumerator name collisions.
- Prevents accidental arithmetic/comparison with integers.
- Allows explicit underlying type.
- Improves overload type safety.

### Flags

Bitmask enums need explicitly defined operators:

```cpp
enum class Permission : unsigned {
    Read  = 1u << 0,
    Write = 1u << 1
};

constexpr Permission operator|(Permission left, Permission right) {
    return static_cast<Permission>(
        static_cast<unsigned>(left) |
        static_cast<unsigned>(right));
}
```

Do not assume every enum should permit bitwise operations.

### Interview question

**Question:** What are the main differences between `enum` and `enum class`?

**Answer:** `enum class` scopes its enumerators and prevents implicit conversion to integers, while also supporting a specified underlying type.

---

## 17. `using` aliases

Modern type alias:

```cpp
using DeviceId = std::uint32_t;
using Callback = std::function<void(const Event&)>;
```

Traditional equivalent:

```cpp
typedef std::uint32_t DeviceId;
```

`using` reads naturally from left to right.

### Template aliases

```cpp
template<class T>
using DeviceMap = std::unordered_map<DeviceId, T>;
```

Template aliases are much clearer than equivalent `typedef` patterns.

### Alias is not a strong type

```cpp
using Meters = int;
using Milliseconds = int;
```

These are both exactly `int`; the compiler allows mixing them.

For real type safety:

```cpp
struct Meters {
    int value;
};

struct Milliseconds {
    int value;
};
```

### Namespace using-declaration

This is a different use of `using`:

```cpp
using std::string;
```

It introduces a name rather than creating a type alias.

### Interview question

**Question:** Does `using DeviceId = unsigned;` create a distinct type?

**Answer:** No. It creates another name for the same type. Use a wrapper/strong type when accidental mixing must be rejected.

---

## 18. `constexpr`, `consteval`, and `constinit`

### `constexpr`

A constexpr object is a constant-expression value:

```cpp
constexpr std::size_t buffer_size = 128;
std::array<std::byte, buffer_size> buffer;
```

A constexpr function can execute at compile time when used with suitable inputs/context:

```cpp
constexpr int square(int value) {
    return value * value;
}

constexpr int compile_time = square(5);

int runtime_input = read_input();
int runtime_result = square(runtime_input);
```

The second call can execute at runtime.

### `consteval`

```cpp
consteval std::uint32_t make_id(unsigned major, unsigned minor) {
    return major * 1000u + minor;
}

constexpr auto id = make_id(2, 5);
```

Every potentially evaluated call must produce a compile-time result.

### `constinit`

```cpp
constinit int startup_state = 0;
```

`constinit` applies to static/thread storage and requires static initialization, helping avoid dynamic initialization-order problems. It does not make the object immutable:

```cpp
startup_state = 1; // allowed
```

### Comparison

| Keyword | Main guarantee |
|---|---|
| `const` | No mutation through this object/access path |
| `constexpr` object | Constant-expression value |
| `constexpr` function | May run at compile time |
| `consteval` function | Must run at compile time |
| `constinit` variable | Must be statically initialized |

### Interview question

**Question:** Is a constexpr function always executed at compile time?

**Answer:** No. It can execute at runtime when called with runtime values unless the context requires constant evaluation; `consteval` requires compile-time calls.

---

## 19. `noexcept`

A function can promise not to let exceptions escape:

```cpp
void reset() noexcept {
}
```

If an exception escapes a `noexcept` function, the program calls `std::terminate`.

### Query form

```cpp
static_assert(noexcept(reset()));
```

Conditional specification:

```cpp
template<class T>
void swap_values(T& a, T& b)
    noexcept(noexcept(std::swap(a, b))) {
    std::swap(a, b);
}
```

### Move operations

Containers often prefer a `noexcept` move constructor during reallocation:

```cpp
Widget(Widget&&) noexcept;
```

If moving might throw and copying is available, a vector may copy to preserve its strong exception guarantee.

### Destructors

Destructors are normally non-throwing. Allowing an exception to escape during stack unwinding can terminate the process.

### Embedded code

`noexcept` does not mean:

- No failure.
- No blocking.
- Constant-time behavior.
- No allocation.
- No error code.

It only concerns exception escape.

### Interview question

**Question:** Why does `noexcept` matter for move constructors?

**Answer:** Standard containers can safely choose moving during reallocation without risking loss of their exception guarantees.

---

## 20. Initialization statements in `if` and `switch`

C++17 allows an initializer before the condition:

```cpp
if (auto iterator = devices.find(id);
    iterator != devices.end()) {
    use(iterator->second);
}
```

`iterator` exists only within the `if` and its `else`.

### Lock scope

```cpp
if (std::lock_guard lock{mutex_}; ready_) {
    process();
}
```

The lock remains alive for the entire `if`/`else` statement.

### Structured binding

```cpp
if (auto [iterator, inserted] = devices.insert(entry);
    inserted) {
    // new element
} else {
    // already existed
}
```

### Switch initializer

```cpp
switch (auto status = read_status(); status.code()) {
case Code::Ok:
    break;
case Code::Error:
    log(status);
    break;
}
```

### Benefit

The helper variable's scope matches exactly where it is valid, reducing accidental later use.

### Interview question

**Question:** What is the main benefit of an `if` initializer?

**Answer:** It keeps lookup results, locks, or other helper objects scoped to the condition and both branches where they are needed.

---

## 21. Class template argument deduction (CTAD)

Before C++17:

```cpp
std::pair<int, double> pair{1, 2.0};
std::lock_guard<std::mutex> lock{mutex};
```

With CTAD:

```cpp
std::pair pair{1, 2.0};
std::lock_guard lock{mutex};
```

Constructors and deduction guides determine template arguments.

### User-defined deduction guide

```cpp
template<class Iterator>
class Range {
public:
    Range(Iterator begin, Iterator end);
};

template<class Iterator>
Range(Iterator, Iterator) -> Range<Iterator>;
```

Now:

```cpp
Range range{values.begin(), values.end()};
```

### Limitations

CTAD applies to class-template variable construction, not to every type position:

```cpp
// void process(std::vector values); // not a normal deduced function parameter
```

Use a template, abbreviated template, or explicit specialization:

```cpp
template<class T>
void process(const std::vector<T>& values);
```

### Tradeoff

CTAD reduces repetition, but explicit arguments can document intended representation or prevent deduction surprises.

### Interview question

**Question:** What does CTAD deduce?

**Answer:** Class-template arguments for a constructed variable from constructors and deduction guides.

---

## 22. `if constexpr` and concepts

### `if constexpr`

```cpp
template<class T>
void serialize(const T& value) {
    if constexpr (std::is_integral_v<T>) {
        serialize_integer(value);
    } else {
        serialize_object(value);
    }
}
```

The non-selected branch is discarded during template instantiation, allowing type-dependent code that would not compile for the selected type.

This is compile-time selection, not an ordinary runtime branch.

### Concepts

```cpp
template<std::integral T>
T saturating_add(T left, T right);
```

Or:

```cpp
template<class T>
requires std::integral<T>
T saturating_add(T left, T right);
```

Concepts:

- State template requirements in the interface.
- Improve diagnostics.
- Participate in overload resolution.
- Document intended operations.

They do not automatically prove semantic properties such as “this comparison is logically correct.”

### Abbreviated function template

```cpp
void print(const auto& value) {
    std::cout << value;
}
```

In C++20, this declares a function template.

### Interview question

**Question:** How does `if constexpr` differ from `if`?

**Answer:** Its condition is compile-time, and the non-selected branch is discarded for the current template instantiation rather than being compiled as an ordinary runtime path.

---

## 23. `std::optional`, `std::variant`, and vocabulary types

### `std::optional`

Represents a value that may be absent:

```cpp
std::optional<Device> find_device(DeviceId id);
```

Usage:

```cpp
if (auto device = find_device(id)) {
    device->start();
}
```

Tradeoffs:

- Expresses absence without sentinel values.
- Stores the value inline in the optional object.
- Does not itself explain why the value is absent.
- Copy/move cost follows the contained type.

### `std::variant`

Represents one of a fixed set of types:

```cpp
using Message = std::variant<Status, Command, Error>;
```

Visit safely:

```cpp
std::visit([](const auto& message) {
    process(message);
}, value);
```

It is a type-safe alternative to untagged unions and some inheritance designs.

### `std::any`

Stores a value of almost any copyable type with runtime type checking. It trades compile-time exhaustiveness for flexibility and is less common in performance-sensitive interfaces.

### `std::expected` (C++23)

Represents either a success value or an error value:

```cpp
std::expected<Device, Error> create_device();
```

It communicates failure reasons more directly than `optional`.

### Interview question

**Question:** When is `optional<T>` better than returning `T*`?

**Answer:** When the function should return an optional value with clear value semantics rather than a borrowed address; pointer is appropriate when borrowing an existing object is the intended contract.

---

## 24. `std::span` and `std::string_view`

### `std::span`

A non-owning view over contiguous elements:

```cpp
void transmit(std::span<const std::byte> bytes);
```

It carries pointer and size together and accepts compatible arrays/vectors.

Mutable view:

```cpp
void clear(std::span<std::byte> bytes);
```

### `std::string_view`

A non-owning character sequence:

```cpp
void log(std::string_view message);
```

It can avoid allocation/copying when observing strings.

### Lifetime risk

Neither owns or extends data lifetime:

```cpp
std::string_view bad() {
    std::string local = "temporary";
    return local; // dangling view
}
```

A string view is not guaranteed null-terminated. Do not pass `.data()` to a C string API unless termination is established.

### Const handle versus const elements

```cpp
const std::span<int> span = values;
span[0] = 42; // allowed: handle constness does not make elements const
```

For read-only elements:

```cpp
std::span<const int> span = values;
```

### Interview question

**Question:** What does `span<const T>` provide over `const T*`?

**Answer:** It carries the element count together with read-only borrowed access, while still not owning or extending the data lifetime.

---

## 25. `override`, `final`, `= default`, and `= delete`

### `override`

```cpp
class Device {
public:
    virtual ~Device() = default;
    virtual void start() = 0;
};

class Camera : public Device {
public:
    void start() override;
};
```

The compiler verifies that `Camera::start` actually overrides a virtual base function. A signature mismatch becomes an error rather than silently creating a new function.

### `final`

```cpp
class FixedDevice final : public Device {
};
```

Or:

```cpp
void start() final;
```

It prevents further derivation or overriding where the design requires closure.

### Defaulted functions

```cpp
Device() = default;
~Device() = default;
```

Explicitly request compiler-generated behavior.

### Deleted functions

```cpp
Device(const Device&) = delete;
Device& operator=(const Device&) = delete;
```

Express that an operation is prohibited and obtain clear diagnostics.

### Interview question

**Question:** Why should overrides include the `override` keyword?

**Answer:** It asks the compiler to verify the intended virtual override and catches const, parameter, spelling, and other signature mismatches.

---

## 26. Attributes and designated initialization

### Attributes

```cpp
[[nodiscard]] Result initialize();

[[maybe_unused]] int diagnostic_value{};

switch (state) {
case State::Starting:
    prepare();
    [[fallthrough]];
case State::Running:
    run();
}
```

`[[nodiscard]]` warns when an important result is ignored. It is useful for error-return types, ownership factories, and resource operations.

`[[likely]]` and `[[unlikely]]` can express branch expectations in C++20, but profile-guided optimization and measurement are preferable to guessing.

### Designated initialization

C++20 aggregates support:

```cpp
struct Configuration {
    int channel{};
    int rate{};
    bool enabled{};
};

Configuration config{
    .channel = 2,
    .rate = 100,
    .enabled = true
};
```

C++ designated initialization is more restricted than C's:

- It applies to aggregates.
- Designators follow declaration order.
- Nested/out-of-order C forms are not generally supported.

Adding constructors/private members can remove aggregate status and break designated initialization.

### Interview question

**Question:** What does `[[nodiscard]]` guarantee?

**Answer:** It requests a compiler diagnostic when the marked result is discarded; it does not force runtime handling or prove that the result was used correctly.

---

## 27. Common modern C++ mistakes

### Using `auto` without checking copy/reference semantics

```cpp
auto value = container.front(); // copy
```

### Copying every element accidentally

```cpp
for (auto element : expensive_objects) {
}
```

### Using references into a container while structurally modifying it

Reallocation or erasure may invalidate the loop's traversal state and element references.

### Capturing references in an escaping lambda

The closure may outlive locals or `this`.

### Treating views as owners

Ranges, spans, and string views may dangle.

### Overusing clever range pipelines

A simple loop can be more readable, debuggable, and predictable.

### Believing `constexpr` always means compile-time execution

Only a constant-expression context or `consteval` requires it.

### Believing `noexcept` means no failure or no cost

It concerns exception escape only.

### Treating aliases as strong types

`using Meters = int` does not prevent mixing with other integers.

### Assuming the latest standard is available

Embedded compilers, ABI policies, and safety-qualified toolchains may lag.

### Interview question

**Question:** What mistake appears most often when replacing explicit types with `auto`?

**Answer:** Accidentally changing value/reference semantics—for example, copying an element with plain `auto` when borrowing through `const auto&` was intended.

---

## 28. Embedded and systems tradeoffs

Modern C++ features are often zero-overhead abstractions, but inspect their consequences.

### Usually compile-time-only mechanisms

- `auto`.
- `decltype`.
- Structured bindings.
- Scoped enums.
- `using`.
- Concepts.
- `override`.
- Most overload resolution.

### Features whose use may introduce runtime behavior

- Lambda captures store state.
- `std::function` may allocate and type-erase.
- `optional<T>` stores a discriminator plus `T`.
- `variant` stores a discriminator plus space for its largest alternative.
- Ranges may recompute lazy transformations.
- `shared_ptr` uses reference counting.
- `string_view`/`span` add no ownership and therefore require lifetime discipline.
- `constexpr` functions can still run at runtime.
- Local statics may use initialization guards.

### Range loops and determinism

A range loop is normally no less deterministic than the iterator operations it represents. The range type decides complexity and behavior.

```cpp
for (const auto& item : linked_list) {
}
```

is linear traversal with pointer chasing. Syntax does not change the container's memory behavior.

### Avoid hidden allocation

Review:

- Lambda conversion to `std::function`.
- Ranges that materialize containers.
- String construction from views.
- Copies caused by `auto` by value.
- Optional/variant contained values.
- CTAD selecting an unexpected owning type.

### Interview question

**Question:** Is range-based `for` inherently slower than an indexed loop?

**Answer:** No. It expands to iterator-style traversal and is often optimized equivalently; performance depends on the range, element binding, and operations performed.

---

## 29. Practical style guidelines

1. Use `auto` when the initializer makes the type/semantics clear.
2. Write `auto&`, `const auto&`, or `auto&&` intentionally; never assume plain `auto` preserves a reference.
3. Prefer `const auto&` for read-only traversal of non-trivial elements.
4. Use `auto&` for element mutation.
5. Use a value loop variable intentionally for cheap or independent copies.
6. Use index loops when the index is part of the algorithm.
7. Use iterator loops when traversal/erasure control matters.
8. Prefer named algorithms when they express the operation clearly.
9. Use structured bindings with a reference qualifier when copies are not intended.
10. Capture lambda lifetimes and ownership explicitly.
11. Use `nullptr`, scoped enums, explicit constructors, and strong types.
12. Use `constexpr` for values/operations that should support compile-time evaluation.
13. Apply `noexcept` only when the guarantee is true.
14. Treat spans, string views, and range views as borrowed unless proven owning.
15. Use concepts and attributes to express interface constraints, not to add decoration.
16. Choose the oldest/newest standard intentionally for the deployment environment.

### Interview question

**Question:** What is a good default loop for reading every element of a vector of large objects?

**Answer:** `for (const auto& element : vector)`, assuming references remain valid throughout the body and no structural mutation occurs.

---

## 30. Practice examples

### Example 1: Find and print

```cpp
if (auto iterator = devices.find(id);
    iterator != devices.end()) {
    const auto& device = iterator->second;
    std::cout << device.name();
}
```

Identify:

- `auto` deduces the iterator type.
- The `if` initializer limits iterator scope.
- `const auto&` avoids copying the device.

### Example 2: Modify mapped values

```cpp
for (auto& [name, count] : event_counts) {
    ++count;
}
```

Identify:

- Structured binding.
- Reference binding to map elements.
- Key remains non-modifiable.
- Mapped value changes in place.

### Example 3: Lazy filtered traversal

```cpp
auto healthy_devices =
    devices
    | std::views::filter([](const Device& device) {
          return device.healthy();
      });

for (const Device& device : healthy_devices) {
    device.report();
}
```

Identify:

- Lambda predicate.
- Lazy view.
- Borrowed lifetime from `devices`.
- No requirement to materialize a second container.

### Example 4: Ownership in a lambda

```cpp
auto worker = [device = std::make_unique<Device>()]() mutable {
    device->run();
};
```

Identify:

- Init-capture.
- Exclusive ownership moved into closure.
- Closure becomes move-only because its member is move-only.
- Converting it to some copy-requiring wrappers may fail.

### Example 5: Safe buffer API

```cpp
void checksum(std::span<const std::byte> bytes);

std::array<std::byte, 64> packet{};
checksum(packet);
```

Identify:

- No ownership transfer.
- Size travels with pointer.
- Read-only element access.
- `packet` must remain alive throughout the call.

### Interview question

**Question:** In `for (auto& [key, value] : map)`, which parts can normally be modified?

**Answer:** The mapped `value` can be modified, but a standard map's key is const within its stored pair so changing it in place is rejected.

---

## Final interview checklist

You should be able to explain:

- Why `auto` is statically typed.
- Plain `auto` versus `auto&`, `const auto&`, `auto*`, and `auto&&`.
- Brace deduction and proxy-type surprises.
- `decltype(x)` versus `decltype((x))`.
- The conceptual range-based-for transformation.
- Range expression evaluation and begin/end lookup.
- Value/reference choices for loop variables.
- When index and iterator loops remain appropriate.
- Structured bindings with value and reference semantics.
- Lambda closure types, captures, `mutable`, generic lambdas, and lifetime.
- Algorithms versus loops and lazy range views.
- `nullptr`, `enum class`, and type aliases.
- `constexpr`, `consteval`, and `constinit`.
- `noexcept` behavior and move implications.
- `if` initializers and CTAD.
- `if constexpr`, concepts, and abbreviated templates.
- `optional`, `variant`, `span`, and `string_view`.
- `override`, `final`, defaulted/deleted functions, and attributes.
- Embedded/runtime costs hidden behind otherwise compile-time syntax.
