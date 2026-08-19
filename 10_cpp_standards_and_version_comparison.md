# C++ Standards and Version Comparison: C++98 Through C++23

C++ evolves through ISO standards. Each standard adds language features, library facilities, corrections, and clearer rules, while implementations adopt those changes at different speeds.

**Status checked August 18, 2026:** C++23 is the current published ISO C++ standard, formally published as ISO/IEC 14882:2024. C++26 is still an in-progress standard and must not be treated as a completed portable target.

Official status references:

- [Current ISO C++ standard](https://isocpp.org/std/the-standard)
- [ISO/IEC 14882:2024](https://www.iso.org/standard/83626.html)
- [Current WG21 standardization status](https://isocpp.org/std/status)

---

## Part I - Five-Minute Interview Review

### Version timeline

| Name | Publication/technical cycle | Main identity |
|---|---:|---|
| C++98 | 1998 | First ISO C++ standard; templates, exceptions, RTTI, namespaces, STL |
| C++03 | 2003 | Corrections and smaller refinements to C++98 |
| C++11 | 2011 | Major modernization: move semantics, lambdas, `auto`, concurrency, smart pointers |
| C++14 | 2014 | Refinement of C++11; generic lambdas, relaxed `constexpr`, `make_unique` |
| C++17 | 2017 | Structured bindings, `if constexpr`, CTAD, filesystem, `optional`/`variant` |
| C++20 | 2020 | Concepts, ranges, coroutines, modules, comparison, major library expansion |
| C++23 | Technical work completed 2023; ISO publication 2024 | `expected`, explicit object parameters, `print`, `mdspan`, ranges/library improvements |
| C++26 | Work in progress as of August 2026 | Draft features only; verify current draft and implementation support |

### The three standards to know best

For modern interviews, concentrate on:

- [C++11](#5-c11-the-major-modernization): the foundation of modern C++.
- [C++17](#7-c17-practical-modern-c): a common production baseline.
- [C++20](#8-c20-concepts-ranges-coroutines-and-modules): the current major language expansion.

Know [C++23](#9-c23-library-and-language-refinement) enough to identify newer facilities, but do not assume every compiler/library implements all of it.

### High-frequency feature map

| Feature | Introduced |
|---|---:|
| `bool`, namespaces, standard templates/STL | C++98 |
| Rvalue references and move semantics | C++11 |
| `auto` type deduction for variables | C++11 |
| Lambdas | C++11 |
| Range-based `for` | C++11 |
| `nullptr`, `enum class` | C++11 |
| `unique_ptr`, `shared_ptr`, threading library | C++11 |
| Generic lambdas | C++14 |
| `make_unique` | C++14 |
| Structured bindings | C++17 |
| `if constexpr` | C++17 |
| `optional`, `variant`, `string_view`, filesystem | C++17 |
| Concepts and `requires` | C++20 |
| Ranges/views | C++20 |
| Coroutines and modules | C++20 |
| `span`, `jthread`, `format`, synchronization primitives | C++20 |
| `expected`, `print`, `mdspan` | C++23 |

### Five interview checks

1. **What changed most in C++11?** Ownership/move semantics, lambdas, type deduction, uniform initialization, and standard concurrency transformed everyday C++.
2. **What is a common C++17 answer?** Structured bindings, `if constexpr`, CTAD, guaranteed copy-elision cases, filesystem, `optional`, `variant`, and `string_view`.
3. **What are the headline C++20 features?** Concepts, ranges, coroutines, and modules.
4. **Does selecting `-std=c++20` guarantee every C++20 library feature?** No; compiler front end and standard-library implementation support are separate.
5. **Is C++26 currently a published standard?** No, not as of August 18, 2026.

---

## Part II - Detailed Reference

## 1. What a C++ version means

A C++ standard specifies:

- Core language grammar and semantics.
- Standard-library interfaces and behavior.
- Requirements on conforming implementations.
- Undefined, unspecified, implementation-defined, and conditionally supported behavior.
- Compatibility and defect-resolution rules.

The standard does not specify one compiler, ABI, build system, or operating system.

### Language support versus library support

A compiler may implement a language feature while its paired standard library lacks a facility:

```cpp
// Language feature
if constexpr (condition) {
}

// Library feature
std::filesystem::path path;
```

`if constexpr` depends on the compiler front end. `std::filesystem` depends heavily on library implementation and linkage/runtime support.

### Published standard versus working draft

A working draft contains changes under committee development. Vendors may implement draft features early, but:

- Syntax or behavior can change.
- Feature-test macros may change.
- Different compilers may implement different revisions.
- Shipping ABI/API based on a draft can create maintenance risk.

### Interview question

**Question:** What does it mean for code to target C++20?

**Answer:** It intends to use the C++20 language and library specification, but actual portability still depends on compiler, standard library, ABI, platform, and implementation completeness.

---

## 2. C++98: the first ISO standard

C++98 established the standardized foundation.

### Major language facilities

- Classes and inheritance.
- Virtual functions and runtime polymorphism.
- Function and operator overloading.
- Templates.
- Exceptions.
- Namespaces.
- References.
- RTTI (`dynamic_cast`, `typeid`).
- `bool`.
- C++ casts.
- Const correctness.
- Dynamic allocation with `new` and `delete`.

### Standard library and STL

The standard library included:

- `std::string`.
- I/O streams.
- Containers such as `vector`, `list`, `deque`, `map`, and `set`.
- Iterators.
- Algorithms such as `sort`, `find`, and `copy`.
- Function objects.
- Allocators.
- Numeric facilities.

The STL's central idea was generic algorithms working through iterator abstractions.

### Typical C++98 style

```cpp
std::vector<int> values;

for (std::vector<int>::iterator iterator = values.begin();
     iterator != values.end();
     ++iterator) {
    std::cout << *iterator << '\n';
}
```

No language-level `auto` deduction, range-for, lambdas, move semantics, or standard smart-pointer ownership model comparable to `unique_ptr`.

### Interview question

**Question:** Was the STL added in C++11?

**Answer:** No. Containers, iterators, and algorithms were part of the first ISO C++ standard; C++11 expanded and modernized them.

---

## 3. C++03: stabilization and correction

C++03 was primarily a correction/revision of C++98 rather than a redesign.

Notable areas included:

- Defect fixes and wording clarification.
- Value-initialization rules.
- Library corrections.
- Improved consistency for templates and standard-library behavior.

Typical source code looks essentially like C++98.

### Why the version still matters

Legacy embedded and enterprise code may identify itself as “C++03” to mean:

- No move semantics.
- No lambdas.
- No standard threading library.
- No `unique_ptr`.
- No `constexpr`.
- No variadic templates.
- Heavy use of Boost or proprietary facilities.

### `auto_ptr`

C++03 used `std::auto_ptr` as an ownership type, but its copy-transfers-ownership behavior was surprising. It was deprecated in C++11 and removed in C++17. Modern code uses `std::unique_ptr`.

### Interview question

**Question:** What is the practical difference between C++98 and C++03?

**Answer:** C++03 is mostly a corrected/stabilized C++98, not the major feature shift seen in C++11.

---

## 4. The pre-modern versus modern boundary

C++11 is commonly treated as the boundary between “classic” and “modern” C++ because it changed routine design.

### Pre-C++11 limitations

- Copies were the primary value-transfer mechanism.
- Ownership types were weaker or library-specific.
- Threading was platform-specific.
- Anonymous callbacks required function objects or function pointers.
- Iterator types were verbose.
- Compile-time computation facilities were limited.
- Variadic generic code relied on macros or generated overloads.

### Modern approach

```cpp
auto device = std::make_unique<Device>();

std::thread worker([device = device.get()] {
    device->run();
});

for (const auto& reading : readings) {
    process(reading);
}
```

Modern features improve expression, but they also introduce new responsibilities: moved-from states, lambda capture lifetime, concurrency, and deduction rules.

### Interview question

**Question:** Why is C++11 considered more than an incremental release?

**Answer:** It introduced move semantics, standard ownership/concurrency facilities, lambdas, deduction, variadic templates, and many features that changed everyday API and class design.

---

## 5. C++11: the major modernization

### Move semantics

```cpp
std::vector<int> source{1, 2, 3};
std::vector<int> destination = std::move(source);
```

Rvalue references, move constructors, and move assignment allow resource transfer instead of expensive deep copying.

### Type deduction

```cpp
auto iterator = values.begin();
decltype(values.size()) count{};
```

### Lambdas

```cpp
auto predicate = [](int value) {
    return value > 0;
};
```

### Range-based loops

```cpp
for (const auto& value : values) {
}
```

### Safer core-language tools

```cpp
nullptr
enum class State { Idle, Running };
static_assert(sizeof(int) >= 4);
```

Also:

- Brace/list initialization.
- `constexpr`.
- `noexcept`.
- Delegating and inherited constructors.
- `= default` and `= delete`.
- `override` and `final`.
- Strongly typed enums.
- User-defined literals.
- Variadic templates.
- Alias templates.
- Thread-local storage.
- Alignments (`alignas`, `alignof`).

### Library additions

- `std::unique_ptr`, `std::shared_ptr`, `std::weak_ptr`.
- `std::array`.
- `std::tuple`.
- `std::unordered_map` and related unordered containers.
- `std::thread`, mutexes, condition variables, futures, atomics.
- `std::chrono`.
- Type traits.
- Random-number facilities.
- Regular expressions.
- `std::function` and `std::bind`.
- `std::initializer_list`.

### Tradeoffs

C++11 compatibility can still be attractive for older toolchains, but it lacks many readability and library improvements from C++14/17/20.

### Interview question

**Question:** Name the three C++11 changes with the greatest design impact.

**Answer:** A strong answer usually includes move semantics, RAII ownership through modern smart pointers, and lambdas/concurrency/type deduction, with explanation rather than only a list.

---

## 6. C++14: refinement of C++11

C++14 made C++11 easier to use.

### Generic lambdas

```cpp
auto add = [](auto left, auto right) {
    return left + right;
};
```

### Function return-type deduction

```cpp
auto square(int value) {
    return value * value;
}
```

### Relaxed `constexpr`

C++14 allowed more ordinary statements in constexpr functions:

```cpp
constexpr int sum_to(int n) {
    int result = 0;
    for (int i = 1; i <= n; ++i) {
        result += i;
    }
    return result;
}
```

### Variable templates

```cpp
template<class T>
constexpr T pi = T{3.1415926535897932385L};
```

### Language conveniences

- Binary literals: `0b1010`.
- Digit separators: `1'000'000`.
- Generalized lambda capture/init-capture.
- Improved aggregate/member initialization rules.
- `decltype(auto)`.

### Library additions

- `std::make_unique`.
- `std::integer_sequence`.
- Shared timed mutex facilities.
- Additional user-defined literal and tuple/type-trait helpers.

### Interview question

**Question:** What did C++14 add that made lambdas substantially more generic?

**Answer:** `auto` parameters for generic lambdas and init-capture for creating/moving state into the closure.

---

## 7. C++17: practical modern C++

C++17 is a widely used production baseline because it adds expressive features without requiring every major C++20 subsystem.

### Structured bindings

```cpp
auto [iterator, inserted] = map.insert({key, value});
```

### `if constexpr`

```cpp
template<class T>
void process(const T& value) {
    if constexpr (std::is_integral_v<T>) {
        process_integer(value);
    } else {
        process_object(value);
    }
}
```

### Initialization in `if` and `switch`

```cpp
if (auto iterator = map.find(key); iterator != map.end()) {
}
```

### Class template argument deduction

```cpp
std::pair pair{1, 2.0};
std::lock_guard lock{mutex};
```

### Guaranteed copy elision in specified cases

```cpp
Widget make_widget() {
    return Widget{};
}
```

The result object can be initialized directly under the new prvalue model.

### Other language additions

- Inline variables.
- Fold expressions.
- Nested namespace syntax.
- `constexpr` lambdas.
- `[[nodiscard]]`, `[[maybe_unused]]`, `[[fallthrough]]`.
- New deduction and evaluation rules.

### Library additions

- `std::optional`.
- `std::variant`.
- `std::any`.
- `std::string_view`.
- `std::filesystem`.
- Parallel algorithm overloads/execution policies.
- `std::byte`.
- `std::pmr` polymorphic memory resources.
- `std::shared_mutex`.
- `std::scoped_lock`.
- `std::from_chars` / `std::to_chars`.
- Searchers and numerous algorithm/type-trait additions.

### Removed/deprecated legacy facilities

C++17 removed facilities including `std::auto_ptr` and some old function-object adapters.

### Interview question

**Question:** Why is C++17 often chosen as a baseline?

**Answer:** It provides structured bindings, `if constexpr`, CTAD, strong vocabulary types, filesystem, string views, and mature compiler support without requiring C++20 modules/ranges/concepts adoption.

---

## 8. C++20: concepts, ranges, coroutines, and modules

C++20 is another major release.

### Concepts

```cpp
template<std::integral T>
T add(T left, T right);
```

Concepts make template constraints part of interfaces and overload resolution.

### Ranges

```cpp
auto even =
    values | std::views::filter([](int value) {
        return value % 2 == 0;
    });

std::ranges::sort(values);
```

Ranges introduce range-based algorithms, views, projections, sentinels, and a formal range model.

### Coroutines

Functions can suspend and resume using:

```cpp
co_await
co_yield
co_return
```

C++20 provides language machinery but relatively little high-level coroutine library infrastructure; frameworks define task/generator/event-loop types.

### Modules

```cpp
export module geometry;

export struct Point {
    int x;
    int y;
};
```

Modules aim to improve encapsulation and build scalability compared with textual headers, but build-system/compiler integration varies.

### Three-way comparison

```cpp
auto operator<=>(const Version&) const = default;
```

This can synthesize consistent comparison operations when memberwise semantics are appropriate.

### Compile-time features

- `consteval`.
- `constinit`.
- Expanded `constexpr`.
- `std::is_constant_evaluated`.
- Designated initialization for aggregates.
- Template lambdas.
- Abbreviated function templates.
- `using enum`.

### Library additions

- `std::span`.
- `std::format`.
- `std::source_location`.
- `std::jthread` and `std::stop_token`.
- Semaphores, latches, and barriers.
- Atomic wait/notify and `atomic_ref`.
- Calendar/time-zone chrono support.
- `std::bit_cast` and `<bit>` utilities.
- String `starts_with`/`ends_with`.
- More constexpr containers/algorithms.

### Implementation reality

C++20 support is not one Boolean. Modules, format, ranges, and library components matured at different speeds across vendors.

### Interview question

**Question:** What are the four headline C++20 features?

**Answer:** Concepts, ranges, coroutines, and modules, followed by explanation of what problem each addresses.

---

## 9. C++23: library and language refinement

C++23 is the current published standard as of August 18, 2026. The formal ISO publication is ISO/IEC 14882:2024 because publication followed completion of the C++23 technical work.

### Explicit object parameters (“deducing this”)

```cpp
struct Buffer {
    template<class Self>
    auto&& data(this Self&& self) {
        return std::forward<Self>(self).data_;
    }

private:
    std::vector<int> data_;
};
```

This can unify const/value-category overload patterns and supports new generic techniques.

### `if consteval`

```cpp
constexpr int evaluate(int value) {
    if consteval {
        return compile_time_path(value);
    } else {
        return runtime_path(value);
    }
}
```

### Language refinements

Examples include:

- Multidimensional subscript support.
- Static call/subscript operators.
- Additional constexpr capabilities.
- Simpler implicit move rules.
- More portable assumptions and preprocessing/literal improvements.

### Library additions

High-value examples include:

- `std::expected`.
- `std::print` / `std::println`.
- `std::mdspan`.
- `std::move_only_function`.
- `std::stacktrace`.
- `std::flat_map` and `std::flat_set`.
- `std::generator`.
- `std::byteswap`.
- `std::unreachable`.
- Span-based streams.
- Monadic operations for `optional` and `expected`.
- `ranges::to` and additional range views/algorithms.

### Adoption tradeoff

C++23 availability varies across:

- Compiler parsing.
- Standard-library implementation.
- Operating-system/runtime packaging.
- IDE/build-system recognition.
- Embedded vendor support.

Use feature-test macros and a compatibility matrix before choosing facilities.

### Interview question

**Question:** Why is the current standard called C++23 when ISO/IEC 14882 is dated 2024?

**Answer:** The C++23 technical work and approval cycle completed in 2023; ISO administrative publication occurred in 2024.

---

## 10. C++26: work in progress

As of August 18, 2026, C++26 is not a published ISO standard. Committee work and compiler experiments exist, but this chapter intentionally does not present a draft feature list as final.

### How to discuss draft features responsibly

Say:

- “This feature is in the current C++26 working draft,” if verified.
- “Compiler X implements an experimental revision,” when implementation-specific.
- “The syntax/semantics may still change.”
- “This is not part of the current published C++23 standard.”

Do not say:

- “C++26 guarantees this” before publication.
- “All C++26 compilers support it.”
- “Draft support is portable.”

### When to experiment

Draft features can be useful for:

- Library/toolchain research.
- Non-production experiments.
- Evaluating upcoming design directions.
- Providing committee/implementation feedback.

They are risky for long-lived ABI, safety-certified code, or multi-vendor portability.

### Interview question

**Question:** How should you answer a question about a C++26 feature today?

**Answer:** Clearly label it as draft/current-working-status, identify compiler support separately, and avoid presenting it as a finalized portable standard.

---

## 11. Feature-test macros

Do not infer support only from compiler version.

### Language-version macro

```cpp
#if __cplusplus >= 202002L
    // C++20-or-later language mode
#endif
```

Common values:

| Mode | `__cplusplus` value |
|---|---:|
| C++98/03 | `199711L` |
| C++11 | `201103L` |
| C++14 | `201402L` |
| C++17 | `201703L` |
| C++20 | `202002L` |
| C++23 | `202302L` |

Do not hard-code an assumed final C++26 value before standardization/toolchain documentation confirms it.

Microsoft compilers historically required `/Zc:__cplusplus` for an accurate standard value in some configurations.

### Feature-test macros

```cpp
#include <version>

#if defined(__cpp_lib_expected) && __cpp_lib_expected >= 202202L
    // expected support at required revision
#endif
```

Language macros often begin `__cpp_`; library macros often begin `__cpp_lib_`.

### Why macros matter

A toolchain may be in C++20 mode but lack a particular library component. Check the exact feature, not just the umbrella mode.

### Interview question

**Question:** Why is `__cplusplus >= 202002L` insufficient to prove that `std::format` works?

**Answer:** It indicates language mode, while `std::format` is a library feature whose implementation may be incomplete or unavailable.

---

## 12. Selecting a standard in builds

Common compiler flags:

```text
GCC/Clang: -std=c++17, -std=c++20, -std=c++23
MSVC:      /std:c++17, /std:c++20, /std:c++latest
```

Use build-system target properties rather than scattered flags when possible.

CMake example:

```cmake
target_compile_features(vehicle_controller PRIVATE cxx_std_20)
```

Or set explicit standard properties according to project policy.

### Avoid “latest” for reproducible production builds

A `latest` mode can change behavior when the compiler updates. Pin:

- Compiler version.
- Standard-library version.
- Language mode.
- Build flags.
- Dependency versions.

### GNU extensions

`-std=gnu++20` enables GNU extensions in addition to standard C++20, while `-std=c++20` aims for the standard dialect. Extensions can reduce portability.

### Interview question

**Question:** Why avoid `/std:c++latest` or equivalent in a reproducible release build?

**Answer:** Its meaning changes with compiler upgrades, potentially changing accepted syntax, semantics, ABI interactions, and diagnostics.

---

## 13. Source compatibility, binary compatibility, and ABI

These are different.

### Source compatibility

Old source compiles under a newer mode. It can fail because:

- Removed facilities.
- New keywords.
- Changed overload resolution.
- Stricter rules.
- Library API changes.
- Previously accepted extensions are rejected.

### Binary compatibility

Already compiled components can link and work together. It depends on:

- Name mangling.
- Object layout.
- Calling conventions.
- Exception/runtime model.
- Standard-library ABI.
- Compiler flags.
- Debug/release modes.
- Allocator ownership across boundaries.

Selecting a newer language standard does not automatically break ABI, but compiler/library choices might.

### API compatibility

Source may compile while behavior changes because overload sets or defaults differ.

### Dynamic libraries/plugins

Expose a stable boundary deliberately. A C ABI entry point is often safer:

```cpp
extern "C" PluginApi* create_plugin(std::uint32_t abi_version);
```

Internal implementation can use any agreed C++ version, but objects crossing the boundary require precise ABI and ownership rules.

### Interview question

**Question:** Does upgrading from C++17 to C++20 necessarily break binary compatibility?

**Answer:** Not necessarily, but ABI depends on compiler, standard library, flags, types crossing boundaries, and implementation choices—not only the language-version label.

---

## 14. Removed and deprecated features

Modernization sometimes removes old facilities.

Examples across versions include:

- `std::auto_ptr` removed in C++17.
- Dynamic exception specifications removed/reworked.
- Old `std::bind1st`/`bind2nd`, `unary_function`, and `binary_function` facilities removed.
- Trigraph support removed from core language.
- `register` lost its old keyword use.
- Some C compatibility and codecvt facilities deprecated/removed over time.

### Migration principle

Replace semantics, not spelling.

`auto_ptr` to `unique_ptr` is not a mechanical rename because copy behavior changes to explicit move-only ownership.

### Interview question

**Question:** Why can replacing `auto_ptr` with `unique_ptr` require design changes?

**Answer:** `auto_ptr` transferred ownership during copying, while `unique_ptr` prohibits copying and requires explicit moves, exposing ownership transfer correctly.

---

## 15. Version-to-version code evolution

### C++03 traversal

```cpp
for (std::vector<Device>::const_iterator iterator = devices.begin();
     iterator != devices.end();
     ++iterator) {
    process(*iterator);
}
```

### C++11 traversal

```cpp
for (const auto& device : devices) {
    process(device);
}
```

### C++20 range algorithm

```cpp
std::ranges::for_each(devices, process);
```

None is automatically correct in every situation. The latter forms express common intent with less bookkeeping.

### Ownership evolution

C++03-style manual ownership:

```cpp
Device* device = new Device;
// ...
delete device;
```

C++11:

```cpp
auto device = std::make_unique<Device>();
```

C++14 made `make_unique` standard:

```cpp
auto device = std::make_unique<Device>();
```

### Conditional generic code

Pre-C++17 often used template specialization/SFINAE. C++17 added `if constexpr`; C++20 added concepts for the interface.

### Interview question

**Question:** Does modernizing syntax alone modernize a design?

**Answer:** No. The important changes are ownership, lifetime, invariants, type safety, constraints, and error behavior; shorter syntax is secondary.

---

## 16. Choosing a project baseline

Evaluate:

- Target compiler versions.
- Standard-library versions.
- Embedded/vendor toolchains.
- Operating-system packaging.
- Safety certification.
- Third-party dependencies.
- ABI requirements.
- Team experience.
- Required features.
- Maintenance lifespan.

### Common choices

**C++17:** mature support and many modern vocabulary types.

**C++20:** strong choice when concepts/ranges/coroutines/modules or modern synchronization are valuable and toolchain support is verified.

**C++23:** appropriate when required components are implemented across every supported toolchain.

### Lowest common denominator tradeoff

A conservative baseline improves reach but may require custom versions of standard facilities and more boilerplate. A newer baseline improves expression but can reduce platform coverage.

### Interview question

**Question:** How would you choose between C++17 and C++20 for a new project?

**Answer:** Build a feature/toolchain/ABI matrix, identify required platforms and features, test standard-library support, and choose the newest version consistently supported and justified.

---

## 17. Embedded-system version considerations

Embedded constraints include:

- Vendor compiler lag.
- Partial standard-library implementation.
- Exceptions/RTTI disabled.
- No operating-system threading layer.
- Code-size constraints.
- Heap restrictions.
- Certification requirements.
- Freestanding rather than hosted implementations.

### Freestanding C++

A freestanding implementation supports a required subset suitable for environments without a full operating system. The available standard-library surface has expanded over recent standards, but never assume hosted facilities exist.

### Language features can still be useful

Even without heap or exceptions:

- `auto`.
- Scoped enums.
- `constexpr`.
- Templates.
- Concepts, if supported.
- Range-based loops.
- `std::array`.
- `std::span`.
- `unique_ptr` with appropriate allocation/ownership, if dynamic storage is allowed.
- RAII for locks, interrupts, and device handles.

### Interview question

**Question:** Does “embedded C++” imply C++03?

**Answer:** No. Modern language features can improve type safety and generate zero-overhead code; the actual baseline depends on toolchain, library, runtime, memory, and certification constraints.

---

## 18. Exceptions and RTTI across versions

Exceptions and RTTI predate modern C++, but projects may disable them:

```text
-fno-exceptions
-fno-rtti
```

This is a toolchain/project choice, not a separate language standard.

### Consequences

If exceptions are disabled:

- Avoid facilities/contracts that throw on expected paths.
- Define allocation-failure policy.
- Use error codes, `optional`, `expected`, or project-specific result types.
- Verify standard-library behavior.

If RTTI is disabled:

- `dynamic_cast` and `typeid` uses are restricted.
- Design explicit type tags, variants, or non-RTTI polymorphism where needed.

### Interview question

**Question:** Is exception support a C++11 feature?

**Answer:** No. Exceptions were standardized in C++98; modern versions add alternative vocabulary and library facilities but project flags may disable exceptions.

---

## 19. Concurrency evolution

### Before C++11

Threads, mutexes, atomics, and memory-order semantics were platform/vendor-specific.

### C++11

Introduced:

- `std::thread`.
- Mutexes and locks.
- Condition variables.
- Futures/promises.
- Atomics.
- The C++ memory model.

### C++14/17

Added/refined timed/shared locking and parallel algorithm facilities.

### C++20

Added:

- `std::jthread`.
- Stop tokens.
- Semaphores.
- Latches.
- Barriers.
- Atomic wait/notify.
- `atomic_ref`.

### C++23 and beyond

Library refinement continues, but support must be verified per toolchain.

### Interview question

**Question:** Why was C++11 concurrency more significant than merely adding `std::thread`?

**Answer:** It standardized the memory model and data-race/atomic ordering semantics, giving portable meaning to concurrent C++ execution.

---

## 20. Compile-time programming evolution

### C++98/03

Template metaprogramming could perform compile-time computation but was verbose and error-prone.

### C++11

Introduced `constexpr`, type traits, variadic templates, and alias templates.

### C++14

Relaxed constexpr function bodies and added variable templates.

### C++17

Added `if constexpr` and fold expressions.

### C++20

Added concepts, consteval, constinit, expanded constexpr allocation/library support, and template lambdas.

### Tradeoff

Compile-time work can improve runtime performance and validation but increases:

- Compile times.
- Diagnostic complexity.
- Binary code duplication.
- Toolchain requirements.

### Interview question

**Question:** How did concepts improve template programming compared with only SFINAE?

**Answer:** They make requirements explicit in interfaces and overload resolution, generally producing clearer intent and diagnostics.

---

## 21. Standard-library evolution

The library grew alongside the language:

```text
C++98: containers, iterators, algorithms, strings, streams
C++11: smart pointers, concurrency, unordered containers, chrono, tuple
C++14: make_unique and generic-support refinements
C++17: filesystem, optional, variant, any, string_view, parallel algorithms
C++20: ranges, span, format, jthread, synchronization primitives
C++23: expected, print, mdspan, stacktrace, expanded ranges
```

A feature's standard version does not guarantee implementation availability on every platform.

The STL and standard library are explained in [`12_cpp_standard_template_library_stl.md`](./12_cpp_standard_template_library_stl.md).

### Interview question

**Question:** Is the STL the entire C++ standard library?

**Answer:** No. STL traditionally refers to the iterator/container/algorithm/function-object generic design, while the standard library also contains strings, I/O, threading, filesystem, utilities, and more.

---

## 22. Interview comparison table

| Interview prompt | Strong short answer |
|---|---|
| C++98 vs C++11 | C++11 adds move semantics, lambdas, deduction, modern ownership, concurrency, variadic templates, and constexpr |
| C++11 vs C++14 | C++14 mainly refines usability: generic lambdas, relaxed constexpr, return deduction, make_unique |
| C++14 vs C++17 | C++17 adds structured bindings, if constexpr, CTAD, vocabulary types, filesystem, and guaranteed elision cases |
| C++17 vs C++20 | C++20 adds concepts, ranges, coroutines, modules, comparison, span, format, and concurrency facilities |
| C++20 vs C++23 | C++23 refines language and library with expected, print, mdspan, explicit object parameters, and ranges improvements |
| Current published version | C++23, formally ISO/IEC 14882:2024 |
| C++26 status | In progress as of August 18, 2026 |

### Interview question

**Question:** Which version should you say you “know”?

**Answer:** State the baseline you use, then demonstrate feature semantics, cost, ownership, and compatibility rather than listing version labels.

---

## 23. Common version mistakes

### Assuming version equals complete support

Check compiler and library feature matrices/macros.

### Treating draft features as published

Label C++26 material as work in progress.

### Believing new syntax has zero design cost

Lambdas can dangle; views can dangle; coroutines require lifetime ownership; modules affect builds.

### Upgrading mode without warnings/tests

New overload resolution, removed APIs, and stricter diagnostics can expose latent bugs.

### Confusing standard year with ISO publication date

C++23 is published as ISO/IEC 14882:2024.

### Assuming ABI from source compatibility

Recompilation success does not prove mixed-binary compatibility.

### Using newest features in public headers without checking consumers

Header syntax forces every consumer compiler to support that feature.

### Interview question

**Question:** What is the first thing to verify before using a new standard-library feature?

**Answer:** Support in every required compiler and standard-library combination, including runtime/ABI packaging and the feature-test macro revision.

---

## 24. Upgrade workflow

1. Inventory supported platforms and compilers.
2. Record current language/library mode.
3. Enable strong warnings and tests first.
4. Compile in the newer mode without immediately rewriting.
5. Address removed/deprecated behavior.
6. Verify ABI boundaries and third-party dependencies.
7. Introduce new features incrementally.
8. Measure compile time, binary size, runtime, and stack/heap effects.
9. Use feature-test macros only where multiple baselines are truly required.
10. Document the chosen baseline and forbidden/required features.

### Avoid compatibility-macro sprawl

If the whole project can move to C++20, prefer one clear baseline over many branches:

```cpp
#if CPP_VERSION_A
// ...
#elif CPP_VERSION_B
// ...
#endif
```

Compatibility layers are justified for libraries serving multiple consumers, not automatically for every application.

### Interview question

**Question:** Should a C++17-to-C++20 migration begin by rewriting loops into ranges?

**Answer:** No. First change and validate the build mode, warnings, tests, ABI, and dependencies; then adopt features where they improve design.

---

## 25. Practical recommendations

For interview preparation:

1. Understand C++11 ownership, move semantics, lambdas, deduction, and concurrency deeply.
2. Be fluent with C++17 structured bindings, `if constexpr`, optional/variant/string_view, filesystem, and CTAD.
3. Understand C++20 concepts, ranges, coroutines, modules, span, jthread, and synchronization at least conceptually.
4. Recognize important C++23 vocabulary such as `expected`, `print`, and `mdspan`.
5. Label C++26 as draft work until published.
6. Know how to detect language and individual library features.
7. Separate language version, compiler support, library support, ABI, and platform runtime.
8. For embedded interviews, explain why a feature is or is not suitable under memory, timing, and toolchain constraints.

### Interview question

**Question:** Which C++ version provides the foundation of modern interview knowledge?

**Answer:** C++11, with C++17 as a highly practical baseline and C++20 as the next major feature set.

---

## Final interview checklist

You should be able to explain:

- The role of each standard from C++98 through C++23.
- Why C++11 is the modern boundary.
- C++14 as refinement.
- Major C++17 language and library features.
- The four headline C++20 features.
- Important C++23 additions and its 2024 ISO publication date.
- C++26's draft status as of August 2026.
- Language support versus standard-library support.
- `__cplusplus` and feature-test macros.
- Build flags and reproducible standard selection.
- Source compatibility versus ABI compatibility.
- Removed/deprecated feature migration.
- Embedded/freestanding/toolchain constraints.
- Concurrency and compile-time-programming evolution.
- A safe, test-driven version-upgrade workflow.
