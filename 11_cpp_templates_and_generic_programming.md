# C++ Templates and Generic Programming

A template is a compile-time pattern for producing functions, classes, aliases, or variables for different types or values.

> Write one type-safe algorithm or data structure in terms of requirements, then let the compiler instantiate it for concrete arguments.

Templates are the foundation of the STL. Read this chapter before or alongside [`12_cpp_standard_template_library_stl.md`](./12_cpp_standard_template_library_stl.md).

---

## Part I - Five-Minute Interview Review

### Basic function template

Without templates:

```cpp
int max_value(int left, int right);
double max_value(double left, double right);
```

With a template:

```cpp
template<class T>
T max_value(T left, T right) {
    return left < right ? right : left;
}
```

Usage:

```cpp
int a = max_value(10, 20);       // max_value<int>
double b = max_value(1.5, 2.5);  // max_value<double>
```

`T` is a compile-time type parameter, not runtime dynamic typing. See [The template mental model](#1-the-template-mental-model) and [Function templates](#3-function-templates).

### Basic class template

```cpp
template<class T, std::size_t N>
class Buffer {
public:
    T& operator[](std::size_t index) {
        return data_[index];
    }

private:
    T data_[N]{};
};

Buffer<int, 16> integers;
Buffer<float, 8> samples;
```

`T` is a type parameter; `N` is a non-type parameter. See [Class templates](#7-class-templates) and [Non-type template parameters](#13-non-type-template-parameters).

### Mandatory rules

- Templates are compile-time patterns until instantiated for concrete arguments. See [Instantiation](#8-instantiation).
- A substituted type must support every operation used by the selected code. See [Template requirements](#4-template-requirements-and-compile-time-duck-typing).
- Function arguments can often determine template arguments. See [Template argument deduction](#5-template-argument-deduction).
- `template<class T>` and `template<typename T>` are normally equivalent type-parameter declarations. See [Template parameter kinds](#2-template-parameter-kinds).
- Definitions usually live in headers because instantiating translation units need to see them. See [Why definitions usually live in headers](#9-why-template-definitions-usually-live-in-headers).
- Full specialization replaces one exact argument set; partial specialization matches a family and is unavailable for function templates. See [Specialization](#11-full-and-partial-specialization).
- Variadic templates accept compile-time parameter packs. See [Variadic templates](#14-variadic-templates-and-parameter-packs).
- SFINAE is a classic constraint mechanism; C++20 concepts express requirements more clearly. See [SFINAE](#19-sfinae) and [Concepts](#20-concepts-and-requires).
- A forwarding reference plus `std::forward` preserves the caller's value category. See [Perfect forwarding](#23-forwarding-references-and-perfect-forwarding).
- Templates enable static polymorphism but can increase build time and binary size. See [Cost model](#26-template-cost-model).

### Templates versus alternatives

| Mechanism | Selection | Main tradeoff |
|---|---|---|
| Overload | Compile time | Clear for a small known set |
| Template | Compile time | Generic and type-safe; build/code-size cost |
| Virtual function | Runtime | Open runtime extensibility; indirection |
| `variant` + visit | Runtime active alternative | Closed type set; exhaustive handling |
| Macro | Preprocessing | Text substitution without C++ type/scope rules |
| `void*` | Manual runtime convention | Loses type safety |

### Five interview checks

1. **Is one template one generated function?** Potentially many specializations are instantiated, subject to optimization/merging.
2. **Why are definitions usually in headers?** The compiler needs the pattern at an implicit-instantiation point.
3. **Can function templates be partially specialized?** No; use overloads or constraints.
4. **What is a forwarding reference?** `T&&` in a context where `T` is deduced under the forwarding-reference rules.
5. **Why use concepts?** They put requirements in the interface and improve overload resolution and diagnostics.

---

## Part II - Detailed Reference

## 1. The template mental model

```cpp
template<class T>
T square(T value) {
    return value * value;
}
```

Using it:

```cpp
int i = square(4);
double d = square(1.5);
```

creates/uses specializations conceptually like:

```cpp
int square<int>(int);
double square<double>(double);
```

The compiler may inline, merge, or eliminate emitted code, but the language reasons about distinct specializations.

`T` becomes one concrete static type for each specialization. A template does not store an arbitrary runtime type.

The selected `T` must support multiplication and conversion to the result:

```cpp
struct Device {};
// square(Device{}); // error: required operation does not exist
```

### Interview question

**Question:** Is a template instantiated for every possible C++ type?

**Answer:** No. Relevant specializations are instantiated when required or explicitly requested.

---

## 2. Template parameter kinds

### Type parameter

```cpp
template<class T>
class Box {};
```

Equivalent:

```cpp
template<typename T>
class Box {};
```

### Non-type parameter

```cpp
template<class T, std::size_t N>
class FixedBuffer {};
```

`N` is a compile-time value and part of the type.

### Template-template parameter

```cpp
template<class T, template<class...> class Container>
class Collection {
    Container<T> values_;
};
```

### Defaults

```cpp
template<class T, class Allocator = std::allocator<T>>
class Buffer {};
```

Caller:

```cpp
Buffer<int> buffer;
```

### Interview question

**Question:** What is the difference between `class T` and `typename T` in a template parameter list?

**Answer:** For declaring a type parameter they are equivalent; `typename` also disambiguates dependent qualified type names elsewhere.

---

## 3. Function templates

```cpp
template<class T>
T minimum(T left, T right) {
    return right < left ? right : left;
}

auto a = minimum(10, 20);   // T = int
auto b = minimum(2.5, 1.5); // T = double
```

Explicit argument:

```cpp
auto value = minimum<double>(10, 2.5);
```

Multiple type parameters:

```cpp
template<class Left, class Right>
auto add(const Left& left, const Right& right) {
    return left + right;
}
```

Templates can coexist with overloads:

```cpp
template<class T>
void print(const T&);

void print(int);
```

The non-template overload is generally preferred when both are otherwise equally good.

### Interview question

**Question:** Which wins when a non-template and template are equally good matches?

**Answer:** The non-template function is normally preferred after conversion ranking finds equivalent matches.

---

## 4. Template requirements and compile-time duck typing

```cpp
template<class T>
T combine(const T& left, const T& right) {
    return left + right;
}
```

Any `T` with a suitable `+` and result can work. It need not inherit from a designated base class.

This is sometimes called compile-time duck typing: capability comes from supported operations.

Unconstrained failures can produce deep diagnostics. Pre-C++20 code used documentation, traits, SFINAE, and static assertions. C++20 concepts place requirements in the declaration.

Syntax is not the whole contract. A sort comparator must obey strict weak ordering; the compiler generally cannot prove that semantic law.

### Interview question

**Question:** What must a type provide for a template?

**Answer:** Every syntactic and semantic requirement used by the selected template specialization, not necessarily a specific inheritance relationship.

---

## 5. Template argument deduction

By-value parameter:

```cpp
template<class T>
void inspect(T value);

const int original = 10;
inspect(original); // T = int
```

Top-level const and references are dropped by value deduction.

Reference parameter:

```cpp
template<class T>
void inspect(T& value);
```

Passing `const int` deduces `T = const int`.

Const-reference parameter:

```cpp
template<class T>
void inspect(const T& value);
```

Passing an ordinary `int` generally deduces `T = int`; const is in the parameter pattern.

Same `T` twice:

```cpp
template<class T>
T max_value(T left, T right);

// max_value(1, 2.5); // conflicting deduction: int versus double
```

Fix by selecting a type:

```cpp
max_value<double>(1, 2.5);
```

or intentionally design two type parameters.

### Interview question

**Question:** Why does `max_value(1, 2.5)` fail for `template<class T> T max_value(T, T)`?

**Answer:** Deduction finds conflicting candidates for one `T`; it does not first convert both arguments to a common type.

---

## 6. Explicit arguments and non-deduced information

Some arguments can be explicit while others are deduced:

```cpp
template<class Result, class Input>
Result convert(const Input& value);

auto result = convert<double>(integer);
```

The receiving variable's type normally does not deduce a return-only parameter:

```cpp
template<class T>
T make_value();

// int value = make_value(); // cannot normally deduce T
int value = make_value<int>();
```

Non-deduced contexts can deliberately force one argument to determine a type before conversions apply elsewhere.

### Interview question

**Question:** Can `T` normally be deduced only from a function's return destination?

**Answer:** No. Function-template deduction normally uses call arguments; a return-only parameter must be supplied or determined another way.

---

## 7. Class templates

```cpp
template<class T>
class Box {
public:
    explicit Box(T value)
        : value_{std::move(value)} {}

    const T& value() const {
        return value_;
    }

private:
    T value_;
};

Box<int> number{42};
Box<std::string> text{"sensor"};
```

`Box<int>` and `Box<std::string>` are distinct types.

Out-of-class member definition:

```cpp
template<class T>
const T& Box<T>::value() const {
    return value_;
}
```

C++17 CTAD may allow:

```cpp
Box box{42}; // Box<int>
```

Deduction guides can customize deduction:

```cpp
Box(const char*) -> Box<std::string>;
```

### Interview question

**Question:** Are two specializations of one class template in an inheritance relationship?

**Answer:** No. They are distinct types unless the template explicitly defines conversions or common bases.

---

## 8. Instantiation

Implicit use requests the needed specialization:

```cpp
Box<int> box{42};
```

A class layout must be formed, while unused member function bodies are often not instantiated until required.

```cpp
template<class T>
class Wrapper {
public:
    void sort() {
        value_.sort();
    }

private:
    T value_;
};

Wrapper<int> wrapper; // can be valid if sort() is never instantiated
```

Explicit definition:

```cpp
template class Box<int>;
```

Explicit declaration:

```cpp
extern template class Box<int>;
```

The latter tells a translation unit that a definition is provided elsewhere.

### Interview question

**Question:** Are all class-template member functions instantiated when an object is declared?

**Answer:** Generally no; the specialization/layout is formed as required, while member definitions are instantiated when needed, subject to precise standard rules.

---

## 9. Why template definitions usually live in headers

An ordinary function caller can compile from a declaration and link one precompiled definition.

A template caller needs the definition to instantiate a new specialization:

```cpp
template<class T>
T add(T left, T right) {
    return left + right;
}
```

If only a declaration is visible and no matching explicit instantiation is linked, the result is often an undefined-reference link error.

Options:

- Define in the header.
- Put implementation in a `.tpp`/`.ipp` included by the header.
- Explicitly instantiate a closed supported type set in a `.cpp`.
- Use a suitable modules/toolchain model.

### Interview question

**Question:** Can templates be implemented in `.cpp` files?

**Answer:** Yes for a closed explicitly instantiated set or another supported visibility model; open implicit instantiation normally needs the definition visible.

---

## 10. ODR and template definitions

Identical template definitions can appear through headers in multiple translation units under One Definition Rule requirements.

Danger arises when macros/configuration change a definition:

```cpp
#ifdef FAST_MODE
template<class T>
T process(T value) { return fast(value); }
#else
template<class T>
T process(T value) { return checked(value); }
#endif
```

If translation units disagree, the program may violate the ODR without a required diagnostic.

Also review:

- Build flags affecting layout.
- Explicit-specialization placement.
- Lookup differences.
- Inline variables/static data.

### Interview question

**Question:** Why may one template definition appear in multiple translation units?

**Answer:** ODR rules permit equivalent template/inline definitions; differing definitions create an ODR violation.

---

## 11. Full and partial specialization

Primary template:

```cpp
template<class T>
struct TypeName {
    static constexpr std::string_view value = "unknown";
};
```

Full specialization:

```cpp
template<>
struct TypeName<int> {
    static constexpr std::string_view value = "int";
};
```

Partial specialization:

```cpp
template<class T>
struct TypeName<T*> {
    static constexpr std::string_view value = "pointer";
};
```

Partial specialization matches a family and is available for class and variable templates.

Function templates cannot be partially specialized. Use overloading:

```cpp
template<class T>
void process(T value);

template<class T>
void process(T* value);
```

### Interview question

**Question:** Can a function template be partially specialized?

**Answer:** No. Use overloading, constraints, tag dispatch, or a specialized helper class.

---

## 12. Overloading versus specialization

Function overloads participate naturally in overload resolution:

```cpp
template<class T>
void serialize(const T& value);

template<class T>
void serialize(T* value);

void serialize(bool value);
```

Prefer overloads/constraints for parameter families. Use an explicit specialization when one exact template specialization truly needs replacement and its interaction is understood.

### Interview question

**Question:** For special pointer behavior, should you first consider function specialization or overloading?

**Answer:** Usually overloading, because it models the parameter form directly and participates predictably in overload resolution.

---

## 13. Non-type template parameters

```cpp
template<class T, std::size_t N>
class FixedBuffer {
    T data_[N]{};
};

FixedBuffer<int, 16> a;
FixedBuffer<int, 32> b;
```

The two capacities produce different types.

Uses include:

- Fixed capacity/extents.
- Alignment or addresses.
- Enum policies.
- Compile-time IDs.
- Function/member pointers.
- Structural values where the language version permits them.

Tradeoff: each value can create another specialization and complicate interoperability/code size. A runtime `span` can erase a fixed extent when appropriate.

### Interview question

**Question:** Why are `array<int, 4>` and `array<int, 8>` different types?

**Answer:** Size is a non-type template argument and therefore part of the specialization's type identity.

---

## 14. Variadic templates and parameter packs

```cpp
template<class... Types>
struct TypeList {};
```

`Types...` declares a template parameter pack.

```cpp
template<class... Args>
void log(Args&&... args);
```

Pack expansion:

```cpp
template<class... Args>
auto make_device(Args&&... args) {
    return Device(std::forward<Args>(args)...);
}
```

Pack size:

```cpp
sizeof...(Args)
```

Recursive expansion style:

```cpp
void print_all() {}

template<class First, class... Rest>
void print_all(const First& first, const Rest&... rest) {
    std::cout << first;
    print_all(rest...);
}
```

### Interview question

**Question:** What do the ellipses mean in `template<class... Args> void f(Args... args)`?

**Answer:** The first declares a template parameter pack; the second expands it into function parameters.

---

## 15. Fold expressions

C++17:

```cpp
template<class... Values>
auto sum(Values... values) {
    return (0 + ... + values);
}
```

Forms include:

```cpp
(args + ...)
(... + args)
(initial + ... + args)
(args + ... + initial)
```

Left and right folds group operations differently; this matters for non-associative/user-defined operations.

Comma fold for effects:

```cpp
((std::cout << values << '\n'), ...);
```

Empty-pack validity depends on fold form/operator; an explicit initial value often clarifies identity.

### Interview question

**Question:** Why can left and right folds differ?

**Answer:** They associate operations in opposite directions, which matters for subtraction, division, concatenation, and user-defined operators.

---

## 16. Alias and variable templates

Alias:

```cpp
template<class T>
using Vector = std::vector<T>;
```

Variable template:

```cpp
template<class T>
inline constexpr bool is_byte_like_v =
    std::is_same_v<T, std::byte> ||
    std::is_same_v<T, unsigned char>;
```

Traits commonly expose:

```cpp
Trait<T>::value
typename Trait<T>::type
Trait_v<T>
Trait_t<T>
```

An alias does not create a new/strong type.

### Interview question

**Question:** Does an alias template create a distinct type?

**Answer:** No. It creates a parameterized alternate name for a type expression.

---

## 17. Dependent `typename` and `template`

```cpp
template<class Container>
void process(const Container& container) {
    typename Container::const_iterator iterator = container.begin();
}
```

Because `Container` is dependent, the compiler needs `typename` to know the qualified name denotes a type.

Dependent template member:

```cpp
template<class Object>
void call(Object& object) {
    object.template convert<int>();
}
```

The `template` keyword disambiguates `<` as template arguments.

### Interview question

**Question:** Why is `typename T::value_type` required in some templates?

**Answer:** The dependent qualified name could denote a type or value; `typename` tells the parser it is a type.

---

## 18. Two-phase lookup

Names can be:

- Non-dependent: resolved largely at template definition.
- Dependent: resolved further at instantiation with applicable lookup/ADL.

```cpp
void helper(int);

template<class T>
void call(T value) {
    helper(0);      // non-dependent
    process(value); // dependent
}
```

This catches some errors early while allowing type-associated customization.

### Interview question

**Question:** What is two-phase lookup?

**Answer:** Templates are checked partly when defined, while dependent names are resolved further when instantiated.

---

## 19. SFINAE

SFINAE means “Substitution Failure Is Not An Error.”

```cpp
template<class T,
         std::enable_if_t<std::is_integral_v<T>, int> = 0>
T twice(T value) {
    return value * 2;
}
```

If substitution fails in a specified immediate context, the candidate is removed rather than making the whole program immediately ill-formed.

Detection idiom:

```cpp
template<class, class = void>
struct has_size : std::false_type {};

template<class T>
struct has_size<T,
    std::void_t<decltype(std::declval<T&>().size())>>
    : std::true_type {};
```

Not every template error is SFINAE. Body-instantiation failures can be hard errors.

### Interview question

**Question:** Does every template substitution error become SFINAE?

**Answer:** No. Only specified substitution failures in immediate contexts remove a candidate.

---

## 20. Concepts and `requires`

```cpp
template<class T>
concept Addable = requires(T left, T right) {
    left + right;
};

template<Addable T>
T add(T left, T right) {
    return left + right;
}
```

Standard concept:

```cpp
template<std::integral T>
T saturating_add(T left, T right);
```

Requires expression with return constraint:

```cpp
template<class T>
concept Sized = requires(const T& value) {
    { value.size() } -> std::convertible_to<std::size_t>;
};
```

Concepts state requirements in interfaces, affect viability/specialization, and improve diagnostics. They cannot generally prove semantic laws.

### Interview question

**Question:** How do concepts improve on raw SFINAE?

**Answer:** They name requirements directly and integrate clearly with interfaces and overload ordering rather than encoding candidate removal indirectly.

---

## 21. `if constexpr`

```cpp
template<class T>
void encode(const T& value) {
    if constexpr (std::is_integral_v<T>) {
        encode_integer(value);
    } else {
        encode_object(value);
    }
}
```

The non-selected branch is discarded for that instantiation.

An ordinary `if` is a runtime branch and both branches normally must be valid after instantiation.

Use `if constexpr` when implementation largely overlaps. Use overloads/specialization when interfaces or algorithms differ substantially.

### Interview question

**Question:** Is `if constexpr` a runtime condition?

**Answer:** No. Its condition is compile-time and the non-selected branch is discarded for the specialization.

---

## 22. Generic lambdas

```cpp
auto compare = [](const auto& left, const auto& right) {
    return left.priority() < right.priority();
};
```

The closure has a templated call operator.

C++20:

```cpp
auto convert = []<class T>(T&& value) {
    return make_result(std::forward<T>(value));
};
```

Constrained:

```cpp
auto twice = []<std::integral T>(T value) {
    return value * 2;
};
```

A generic lambda differs from a free function template because it is an object and may capture state.

### Interview question

**Question:** What does `auto` in a lambda parameter create?

**Answer:** A generic lambda whose closure has a templated call operator.

---

## 23. Forwarding references and perfect forwarding

```cpp
template<class T>
void wrapper(T&& value) {
    target(std::forward<T>(value));
}
```

With an lvalue `Widget`:

```text
T = Widget&
T&& collapses to Widget&
```

With an rvalue:

```text
T = Widget
T&& remains Widget&&
```

The named variable `value` is always an lvalue expression. `std::forward<T>` restores the caller's original category.

Not every `T&&` is forwarding:

```cpp
void consume(Widget&&); // ordinary rvalue reference
```

Forwarding can steal overloads, increase instantiations, and produce lifetime problems. Constrain it.

### Interview question

**Question:** Why is a named `T&&` parameter an lvalue expression?

**Answer:** Names identify objects and name expressions are lvalues; `std::forward<T>` conditionally casts to preserve the original category.

---

## 24. Traits and compile-time programming

Standard type traits:

```cpp
std::is_integral_v<T>
std::remove_reference_t<T>
std::conditional_t<condition, A, B>
```

Classic recursive template metaprogramming can compute types/values, but modern tools are often clearer:

- `constexpr` functions for values.
- Alias templates for type transformations.
- `if constexpr` for branches.
- Concepts for requirements.

### Interview question

**Question:** When is a constexpr function preferable to template metaprogramming?

**Answer:** When the problem is naturally a value computation expressible as ordinary code, improving readability and diagnostics.

---

## 25. Static polymorphism and CRTP

```cpp
template<class Derived>
class DeviceBase {
public:
    void start() {
        static_cast<Derived&>(*this).start_impl();
    }
};

class Camera : public DeviceBase<Camera> {
public:
    void start_impl() {}
};
```

Benefits:

- Compile-time dispatch/inlining.
- No required vtable.
- Mixin/policy composition.

Costs:

- Tight coupling and code duplication.
- No simple heterogeneous runtime base collection.
- More complex diagnostics.
- Unsafe relationship if misused.

### Interview question

**Question:** CRTP versus virtual functions?

**Answer:** CRTP selects behavior at compile time using the derived type; virtual functions select at runtime through a dynamic interface.

---

## 26. Template cost model

Potential runtime benefits:

- Inlining.
- Constant propagation.
- Static dispatch.
- Type-specific optimization.

Costs:

- Parsing/instantiation time.
- Rebuild dependencies.
- Diagnostic complexity.
- Binary code per specialization.
- ABI exposure in public headers.

A template is not automatically fast: its implementation can still allocate, copy, block, or use a poor algorithm.

### Interview question

**Question:** Are templates always zero-cost?

**Answer:** They can remove runtime abstraction cost, but may increase compilation, binary size, coupling, and diagnostics; runtime work still depends on the implementation.

---

## 27. Templates versus runtime polymorphism

Template:

```cpp
template<class Device>
void start(Device& device) {
    device.start();
}
```

Use when types are compile-time known and static optimization/value semantics matter.

Virtual interface: use for runtime-selected/open implementation sets and stable non-template boundaries.

Variant: use for a closed set with value semantics and exhaustive visitation.

Type erasure: use to hide concrete types behind a runtime wrapper such as `std::function`.

### Interview question

**Question:** When choose a template over a virtual interface?

**Answer:** When concrete types are known at compile time and static requirements/inlining are more important than runtime substitutability and ABI stability.

---

## 28. Templates in embedded systems

Fixed-capacity type:

```cpp
template<class T, std::size_t Capacity>
class StaticQueue;
```

Policy configuration:

```cpp
template<class Transport, class Clock, class ErrorPolicy>
class Driver;
```

Compile-time register address:

```cpp
template<std::uintptr_t Address>
class Register {
public:
    static volatile std::uint32_t& value() {
        return *reinterpret_cast<volatile std::uint32_t*>(Address);
    }
};
```

Production MMIO must obey platform alignment, width, volatile, ordering, and safety rules.

Benefits include no dynamic allocation and static optimization. Costs include code-size multiplication, slow builds, older compiler limitations, and certification/tool complexity.

### Interview question

**Question:** Why use templates in heap-free embedded code?

**Answer:** They encode capacity, addresses, types, and policies at compile time, enabling static allocation and dispatch.

---

## 29. Templates and the STL

The STL is template-based:

```cpp
std::vector<int>
std::array<std::byte, 64>
std::map<DeviceId, Device>
std::sort(first, last)
```

- Containers are class templates.
- Algorithms are function templates.
- Iterators communicate traversal capabilities.
- Comparators, hashes, allocators, and projections are policies/callables.
- C++20 concepts formalize requirements.

`std::sort` needs random-access iterators, so vector iterators work but list iterators do not.

### Interview question

**Question:** Why can `std::sort` use vector iterators but not list iterators?

**Answer:** Its template requires random-access operations; list iterators are only bidirectional.

---

## 30. Common errors

- Hiding definitions in `.cpp` without explicit instantiation.
- Omitting dependent `typename`/`template`.
- Asking one `T` to deduce from mixed argument types.
- Creating accidental copies through by-value interfaces.
- Leaving forwarding references unconstrained.
- Assuming every error is SFINAE.
- Specializing in an invalid namespace.
- Generating too many specializations.
- Using a syntactically valid but semantically invalid comparator.
- Confusing compile-time templates with runtime heterogeneous storage.
- Exposing template-heavy implementation across a stable ABI.

### Interview question

**Question:** What commonly causes “undefined reference” for a function template?

**Answer:** The caller saw a declaration but not the definition, and no matching explicit instantiation was linked.

---

## 31. Interview implementation example

```cpp
template<class T, std::size_t Capacity>
class RingBuffer {
public:
    bool push(const T& value);
    bool push(T&& value);
    std::optional<T> pop();

private:
    std::array<T, Capacity> storage_;
};
```

Discuss:

- `T` requirements.
- Capacity in the type.
- Copy/move operations.
- Lifetime of occupied elements.
- Full/empty state.
- Error policy.
- Concurrency.
- Code-size effects across specializations.
- Whether `optional<T>` fits the target.

### Interview question

**Question:** What should you explain after writing a template?

**Answer:** Requirements/concepts, deduction, ownership/copying, instantiation/code size, complexity, failure cases, and whether runtime polymorphism is more appropriate.

---

## 32. Practical guidelines

1. Use templates for genuinely shared compile-time-generic behavior.
2. Use concepts in C++20 to state requirements.
3. Prefer overloads for a small set of meaningfully different cases.
4. Keep definitions visible or explicitly instantiate a closed set.
5. Use standard traits/concepts rather than duplicating detection machinery.
6. Constrain forwarding references.
7. Use `std::forward` only for actual forwarding.
8. Measure build time and binary size in template-heavy code.
9. Avoid templates across stable C/plugin ABI boundaries.
10. Document semantic requirements such as ordering laws.
11. Use `if constexpr` for small internal branches and overloads/specializations for distinct interfaces.
12. Understand the iterator/range requirements of STL algorithms.

### Interview question

**Question:** What is the best reason to use a template?

**Answer:** One type-safe compile-time design correctly serves multiple types or values under a clear common contract.

---

## Final interview checklist

You should be able to explain:

- Templates as compile-time patterns.
- Type, non-type, and template-template parameters.
- Function and class templates.
- Deduction and explicit arguments.
- Instantiation and header visibility.
- Explicit instantiation and ODR.
- Full versus partial specialization.
- Function overloading versus specialization.
- Variadic packs and folds.
- Alias/variable templates.
- Dependent names and two-phase lookup.
- SFINAE versus concepts.
- `if constexpr` and generic lambdas.
- Forwarding references, collapsing, and `std::forward`.
- Traits and compile-time programming.
- CRTP versus virtual polymorphism.
- Runtime, build-time, binary-size, and ABI costs.
- Embedded template use.
- How templates power STL containers and algorithms.
