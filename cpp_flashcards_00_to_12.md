# C++ Interview Flash Cards — Files 00–12

This deck contains **171 high-yield cards** across the numbered topics from 00 through 12, with extra cards for the broader modern C++, template, and STL chapters. The useful container definition from `00_Notes.md` is included in section 12.

## How to use this deck

1. Read only the question in the collapsed heading.
2. Answer aloud, including the reason or tradeoff.
3. Open the card and compare your answer.
4. Mark misses for review after 1 day, 3 days, 7 days, and 14 days.
5. For interview practice, answer each card in 30–60 seconds.

---

## 00 — Interview Mastery Plan

Source: [`00_cpp_embedded_interview_mastery_plan.md`](./00_cpp_embedded_interview_mastery_plan.md)

<details>
<summary><strong>00.1 — What five areas should the interview plan cover?</strong></summary>

Modern C++; data structures and algorithms; OOP and software design; operating systems, concurrency, and embedded systems; and embedded/autonomous-system design and debugging.

</details>

<details>
<summary><strong>00.2 — What is the recommended preparation-time split?</strong></summary>

- Data structures and algorithms: 35%
- Modern C++: 25%
- Embedded, OS, and concurrency: 20%
- OOP and design: 10%
- System design, behavioral preparation, and applications: 10%

</details>

<details>
<summary><strong>00.3 — What should a strong coding-problem workflow look like?</strong></summary>

Clarify requirements, give a brute-force solution, derive an optimized solution, state invariants, implement cleanly, test edge cases, and explain time and space complexity.

</details>

<details>
<summary><strong>00.4 — What are the Rule of Three, Rule of Five, and Rule of Zero?</strong></summary>

- Rule of Three: if a type needs a custom destructor, copy constructor, or copy assignment, it often needs all three.
- Rule of Five: add move constructor and move assignment.
- Rule of Zero: prefer members that manage their own resources so the class declares none of these operations.

</details>

<details>
<summary><strong>00.5 — What is RAII?</strong></summary>

Resource Acquisition Is Initialization ties resource ownership to object lifetime: acquire during construction, release during destruction. It provides deterministic cleanup during normal exit and exception unwinding.

</details>

<details>
<summary><strong>00.6 — When should you use `unique_ptr`, `shared_ptr`, and `weak_ptr`?</strong></summary>

Use `unique_ptr` for exclusive ownership, `shared_ptr` only for genuine shared lifetime, and `weak_ptr` for non-owning observation of shared state or to break ownership cycles.

</details>

<details>
<summary><strong>00.7 — What are the core SOLID principles?</strong></summary>

Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion. They guide maintainable interfaces, but should be applied according to the design rather than mechanically.

</details>

<details>
<summary><strong>00.8 — Why prefer composition over inheritance?</strong></summary>

Composition usually creates looser coupling, explicit ownership, and replaceable behavior. Use inheritance when there is a genuine substitutable “is-a” relationship or a required polymorphic interface.

</details>

<details>
<summary><strong>00.9 — What algorithm patterns should be immediately recognizable?</strong></summary>

Hashing, two pointers, sliding window, prefix sums, binary search, DFS/BFS, heaps, interval processing, greedy choice, backtracking, and dynamic programming.

</details>

<details>
<summary><strong>00.10 — What must be stated when discussing a concurrent design?</strong></summary>

Shared state, synchronization mechanism, ownership and lifetime, ordering requirements, data-race prevention, deadlock risks, blocking behavior, and shutdown/cancellation behavior.

</details>

<details>
<summary><strong>00.11 — What changes when evaluating code for embedded or real-time use?</strong></summary>

Consider deterministic timing, bounded memory use, allocation policy, interrupt context, hardware access, concurrency, error recovery, watchdogs, and worst-case rather than average-case behavior.

</details>

<details>
<summary><strong>00.12 — When are you interview-ready?</strong></summary>

When you can solve unfamiliar problems while communicating clearly, write and debug modern C++, reason about ownership and concurrency, discuss embedded tradeoffs, and explain prior projects and failures with evidence.

</details>

---

## 01 — References vs Pointers

Source: [`01_cpp_references_vs_pointers.md`](./01_cpp_references_vs_pointers.md)

<details>
<summary><strong>01.1 — What is the core difference between a pointer and a reference?</strong></summary>

A pointer is an object that stores an address. A reference is an alias for another object.

</details>

<details>
<summary><strong>01.2 — What contracts do `T&`, `const T&`, `T*`, and `const T*` express?</strong></summary>

- `T&`: required, mutable, non-owning alias.
- `const T&`: required, read-only through this alias, non-owning.
- `T*`: nullable and reseatable address, normally non-owning.
- `const T*`: nullable, reseatable pointer giving read-only access to `T`.

</details>

<details>
<summary><strong>01.3 — What does `ref = other;` do?</strong></summary>

It assigns `other` to the object already named by `ref`; it does not reseat the reference.

</details>

<details>
<summary><strong>01.4 — Can a valid reference be null or be reseated?</strong></summary>

No. A reference must be initialized and cannot later be reseated. Invalid tricks can manufacture a bad reference, but using one has undefined behavior and is not a valid optional-state design.

</details>

<details>
<summary><strong>01.5 — Do raw pointers or references express ownership?</strong></summary>

Normally no. Modern interfaces should express ownership with RAII types such as `unique_ptr`, `shared_ptr`, containers, or resource-owning classes.

</details>

<details>
<summary><strong>01.6 — Can pointers and references dangle?</strong></summary>

Yes. Neither keeps the target alive. The target object must outlive every use, and container operations may invalidate existing handles.

</details>

<details>
<summary><strong>01.7 — When should an input be passed by value?</strong></summary>

For small, cheap-to-copy values, or when the function deliberately needs its own value. A by-value sink can then move from its parameter.

</details>

<details>
<summary><strong>01.8 — When should an API use a reference versus a pointer?</strong></summary>

Use `const T&` for required read-only access, `T&` for required mutation, and `const T*` or `T*` when absence is meaningful.

</details>

<details>
<summary><strong>01.9 — What should represent a borrowed contiguous buffer?</strong></summary>

Prefer `std::span<T>` when available because it carries both address and length without ownership. A naked pointer alone does not describe the range size.

</details>

<details>
<summary><strong>01.10 — What is the difference between `const T*` and `T* const`?</strong></summary>

`const T*` is a reseatable pointer to read-only `T`. `T* const` is a fixed pointer to mutable `T`. `const T* const` fixes both access and pointer value.

</details>

<details>
<summary><strong>01.11 — Why are arrays of references disallowed, while pointer arrays are valid?</strong></summary>

References are not ordinary reseatable objects with independent value semantics. Pointers are objects, so they can be stored, copied, assigned, and placed in arrays.

</details>

<details>
<summary><strong>01.12 — When is returning a reference safe?</strong></summary>

Only when the referred-to object outlives the caller’s use—for example, an element of a still-live object or a valid static object. Never return a reference or pointer to a local automatic object.

</details>

---

## 02 — `const` Syntax and Meaning

Source: [`02_cpp_const_brief_interview_notes.md`](./02_cpp_const_brief_interview_notes.md)

<details>
<summary><strong>02.1 — What is the best mental model for `const`?</strong></summary>

`const` prevents mutation through a particular access path. It is a compile-time interface guarantee, not necessarily global or deep immutability.

</details>

<details>
<summary><strong>02.2 — Why must a const object be initialized?</strong></summary>

Because ordinary assignment is unavailable after initialization. Its initial state must be established when the object is created.

</details>

<details>
<summary><strong>02.3 — Are `const int*` and `int const*` different?</strong></summary>

No. Both are pointers to const `int`.

</details>

<details>
<summary><strong>02.4 — What is top-level versus low-level const?</strong></summary>

Top-level const qualifies the object itself, such as the pointer in `T* const`. Low-level const qualifies an object reached through another type, such as the pointee in `const T*`.

</details>

<details>
<summary><strong>02.5 — Can `const T&` bind to a mutable object or temporary?</strong></summary>

Yes. It prevents mutation through that reference. Direct binding can also extend a temporary’s lifetime under the language’s lifetime-extension rules.

</details>

<details>
<summary><strong>02.6 — Can free functions overload on top-level const of a by-value parameter?</strong></summary>

No. `void f(int)` and `void f(const int)` are the same function type for overload purposes.

</details>

<details>
<summary><strong>02.7 — What does a trailing `const` on a member function mean?</strong></summary>

It makes the implicit object parameter const for that call, prevents ordinary direct mutation through `this`, and allows the function to be called on const objects.

</details>

<details>
<summary><strong>02.8 — Why provide const and non-const accessor overloads?</strong></summary>

So mutable objects may receive writable access while const objects receive read-only access, for example `T& operator[](...)` and `const T& operator[](...) const`.

</details>

<details>
<summary><strong>02.9 — What is logical constness, and what is `mutable` for?</strong></summary>

Logical constness means the externally observable value does not change. `mutable` permits implementation-only state such as caches or mutexes to change in a const operation.

</details>

<details>
<summary><strong>02.10 — When is mutation after `const_cast` undefined behavior?</strong></summary>

When the underlying object was originally declared const. Casting away const from an originally mutable object can be legal, but is usually a design smell.

</details>

<details>
<summary><strong>02.11 — How does plain `auto` treat top-level const and references?</strong></summary>

Plain `auto` normally drops references and top-level const, similar to template by-value deduction. Write `auto&`, `const auto&`, or `auto&&` when those semantics matter.

</details>

<details>
<summary><strong>02.12 — Does `const` imply thread safety or replace `volatile` for MMIO?</strong></summary>

No. `const` is not synchronization, and `volatile` serves a different purpose for observable accesses such as memory-mapped I/O. Neither makes concurrent non-atomic access race-free.

</details>

---

## 03 — Const Correctness

Source: [`03_const_correctness.md`](./03_const_correctness.md)

<details>
<summary><strong>03.1 — What is const correctness?</strong></summary>

It is the consistent design of types and APIs so read-only and mutable access are accurately expressed and enforced across parameters, members, call chains, and returned access.

</details>

<details>
<summary><strong>03.2 — What four questions should a parameter type answer?</strong></summary>

Is the argument required? May it be modified? Is ownership transferred or shared? Is copying intended?

</details>

<details>
<summary><strong>03.3 — Why should logically read-only member functions be `const`?</strong></summary>

It documents the contract, allows calls on const objects, supports const propagation, and expands safe reuse of the type.

</details>

<details>
<summary><strong>03.4 — How does object constness affect overload resolution?</strong></summary>

A mutable object can call const or non-const members, with the non-const match generally preferred. A const object can call only compatible const-qualified members.

</details>

<details>
<summary><strong>03.5 — Can member overloads differ by return type alone?</strong></summary>

No. Const/non-const accessors differ through the member function’s trailing `const`, which changes the implicit object parameter.

</details>

<details>
<summary><strong>03.6 — What should const and non-const direct accessors return?</strong></summary>

When exposing direct access is appropriate, return `T&` from the non-const overload and `const T&` from the const overload.

</details>

<details>
<summary><strong>03.7 — Why is C++ const usually shallow?</strong></summary>

A const object cannot modify its direct ordinary members, but a pointer member may still point to mutable external data. The handle is part of the const object; the pointee may not be.

</details>

<details>
<summary><strong>03.8 — How does const affect containers and smart pointers?</strong></summary>

A const container exposes const element access. A const smart-pointer handle usually cannot be reseated, but it may still give mutable access to its pointee unless the pointee type is const.

</details>

<details>
<summary><strong>03.9 — What is const propagation?</strong></summary>

A const operation must call other operations through const-compatible interfaces. One missing qualifier in a helper can make the full call chain unusable from const objects.

</details>

<details>
<summary><strong>03.10 — What lifetime obligation remains when a const accessor returns a view?</strong></summary>

The source object and its storage must outlive the view. Const limits mutation; it does not create ownership or extend lifetime.

</details>

<details>
<summary><strong>03.11 — When is `mutable` appropriate?</strong></summary>

For logically invisible state such as a cache, statistics that are not part of value semantics, or a mutex. It should not hide changes to the object’s meaningful observable state.

</details>

<details>
<summary><strong>03.12 — Why are const correctness and thread safety separate contracts?</strong></summary>

Const methods can touch mutable state or externally shared objects, and other aliases can mutate the same object. Race freedom requires synchronization or atomic operations.

</details>

---

## 04 — Constructors, Destructors, and Initialization

Source: [`04_constructors_destructors_initialization.md`](./04_constructors_destructors_initialization.md)

<details>
<summary><strong>04.1 — What is the difference between allocation and construction?</strong></summary>

Allocation obtains raw storage. Construction establishes a live object in that storage by initializing bases and members and executing the constructor when required.

</details>

<details>
<summary><strong>04.2 — What is the difference between initialization and assignment?</strong></summary>

Initialization establishes an object’s first state as its lifetime begins. Assignment replaces the state of an already-live object.

</details>

<details>
<summary><strong>04.3 — What does `Widget w = other;` mean?</strong></summary>

It is copy-initialization of a new object, not assignment. `w = other;` is assignment only if `w` already exists.

</details>

<details>
<summary><strong>04.4 — Why prefer member initializer lists?</strong></summary>

They directly initialize members and are required for bases, references, const members, and members without suitable default constructors. Assignment in the body happens too late for these cases.

</details>

<details>
<summary><strong>04.5 — What determines data-member initialization order?</strong></summary>

Declaration order inside the class, not the textual order in the constructor’s initializer list.

</details>

<details>
<summary><strong>04.6 — What is the construction order in inheritance?</strong></summary>

Virtual bases, direct bases, data members in declaration order, then the constructor body. Destruction reverses the completed construction order.

</details>

<details>
<summary><strong>04.7 — What happens to an in-class member initializer?</strong></summary>

It supplies a default when a constructor does not explicitly initialize that member. A constructor’s member initializer overrides it.

</details>

<details>
<summary><strong>04.8 — What is a delegating constructor?</strong></summary>

A constructor that invokes another constructor of the same class, centralizing common initialization and reducing duplicated logic.

</details>

<details>
<summary><strong>04.9 — Why mark a single-argument constructor `explicit` by default?</strong></summary>

To prevent surprising implicit conversions. Leave it implicit only when conversion is intentional and natural for the type.

</details>

<details>
<summary><strong>04.10 — Why do `initializer_list` constructors require care?</strong></summary>

Brace initialization strongly prefers matching `initializer_list` overloads, which can select a different constructor than parentheses and can reject narrowing conversions.

</details>

<details>
<summary><strong>04.11 — When does an object’s destructor run?</strong></summary>

At lifetime end: scope exit, owner deletion, container destruction, exception unwinding, or destruction of the containing object.

</details>

<details>
<summary><strong>04.12 — When does a base class need a virtual destructor?</strong></summary>

When objects may be deleted through a base pointer. Without a virtual destructor, such deletion has undefined behavior. A protected non-virtual destructor can intentionally forbid base-pointer deletion.

</details>

<details>
<summary><strong>04.13 — What happens if construction throws?</strong></summary>

Already-constructed bases and members are destroyed automatically in reverse order. The incomplete object’s own destructor is not called.

</details>

<details>
<summary><strong>04.14 — How does virtual dispatch behave in constructors and destructors?</strong></summary>

Dispatch is limited to the class currently under construction or destruction; it does not call overrides in a more-derived portion whose lifetime has not begun or has already ended.

</details>

---

## 05 — Copy Construction and Copy Assignment

Source: [`05_copy_constructor_and_copy_assignment.md`](./05_copy_constructor_and_copy_assignment.md)

<details>
<summary><strong>05.1 — How do copy construction and copy assignment differ?</strong></summary>

Copy construction initializes a new object from another object. Copy assignment replaces the state of an existing object.

</details>

<details>
<summary><strong>05.2 — Why is a copy constructor normally `Foo(const Foo&)`?</strong></summary>

Passing by reference avoids recursive copying, and const permits copying from const objects and ordinary lvalues.

</details>

<details>
<summary><strong>05.3 — What does compiler-generated copying do?</strong></summary>

It copies each direct base and non-static data member using that subobject’s copy operation.

</details>

<details>
<summary><strong>05.4 — When is memberwise copy correct?</strong></summary>

When every base and member already has the desired copy semantics—for example, value-like members such as `string`, `vector`, and other Rule-of-Zero types.

</details>

<details>
<summary><strong>05.5 — Why is generated copying dangerous for an owning raw pointer?</strong></summary>

It copies only the address, so two objects may believe they own the same allocation, causing aliasing, double deletion, use-after-free, or leaks.

</details>

<details>
<summary><strong>05.6 — What is a deep copy?</strong></summary>

It creates a distinct owned resource and copies the resource’s contents, so the two objects can be modified and destroyed independently.

</details>

<details>
<summary><strong>05.7 — What must copy assignment handle?</strong></summary>

Existing owned state, self-assignment, exception safety, and a valid result if resource acquisition fails. It conventionally returns `*this` by reference.

</details>

<details>
<summary><strong>05.8 — What does the copy-and-swap idiom provide?</strong></summary>

Construct a safe copy first, then swap it with the target. This naturally handles self-assignment and can provide the strong exception guarantee, at a possible extra-allocation or performance cost.

</details>

<details>
<summary><strong>05.9 — When should copying be deleted?</strong></summary>

When a resource has unique identity or cannot be meaningfully duplicated, such as many mutexes, threads, hardware channels, or unique OS handles.

</details>

<details>
<summary><strong>05.10 — How can declaring special members affect moves?</strong></summary>

User-declared copy operations or a destructor can suppress implicit move generation. Explicitly default, delete, or implement operations according to the intended ownership model.

</details>

<details>
<summary><strong>05.11 — What is object slicing?</strong></summary>

Copying a derived object into a base object by value discards the derived portion. For polymorphic copying, consider an explicit virtual `clone()` interface.

</details>

<details>
<summary><strong>05.12 — What is the preferred modern copy-design rule?</strong></summary>

Rule of Zero: compose the type from members whose ownership, copy, move, and destruction behavior are already correct.

</details>

---

## 06 — Namespaces and Overloading

Source: [`06_namespaces_and_overloading.md`](./06_namespaces_and_overloading.md)

<details>
<summary><strong>06.1 — What problem do namespaces solve?</strong></summary>

They organize names and prevent collisions between components without creating objects or runtime overhead.

</details>

<details>
<summary><strong>06.2 — Why avoid `using namespace ...` in a header?</strong></summary>

It imports names into every including translation unit, potentially creating collisions, ambiguities, and changed overload sets far from the header.

</details>

<details>
<summary><strong>06.3 — What does an unnamed namespace provide?</strong></summary>

Internal linkage for names within one translation unit. It is generally preferred to namespace-scope `static` for C++ implementation-only names.

</details>

<details>
<summary><strong>06.4 — What is argument-dependent lookup (ADL)?</strong></summary>

For an unqualified function call, ADL also searches namespaces and classes associated with the argument types. It is important for operators, customization functions, and swap-style calls.

</details>

<details>
<summary><strong>06.5 — What makes two function declarations overloads?</strong></summary>

They share a name in the relevant scope but have distinct parameter-type lists or, for members, distinct qualifying forms such as trailing const or reference qualification.

</details>

<details>
<summary><strong>06.6 — Can return type alone distinguish overloads?</strong></summary>

No, because a call must be resolved before its return value can select a function.

</details>

<details>
<summary><strong>06.7 — What are the main steps of overload resolution?</strong></summary>

Build the candidate set, keep viable functions, rank required conversions, and select one unique best match. Otherwise the call is ill-formed.

</details>

<details>
<summary><strong>06.8 — How are common implicit conversions ranked?</strong></summary>

Exact matches beat promotions; promotions beat other standard conversions; standard conversions generally beat user-defined conversions.

</details>

<details>
<summary><strong>06.9 — How can a derived declaration hide base overloads?</strong></summary>

Declaring any function with the same name in the derived class can hide the entire base overload set. Use `using Base::function;` to restore it when intended.

</details>

<details>
<summary><strong>06.10 — What can operator overloading not change?</strong></summary>

It cannot invent new operators or change an operator’s precedence, associativity, arity, or evaluation rules.

</details>

<details>
<summary><strong>06.11 — When should an operator be a non-member?</strong></summary>

Use a non-member for symmetric binary operations when the left operand need not be the class type, often implemented as a hidden friend when private access is appropriate.

</details>

<details>
<summary><strong>06.12 — What is the main operator-design rule?</strong></summary>

Define an operator only when its meaning is natural, unsurprising, and consistent with the built-in operator’s conceptual behavior.

</details>

---

## 07 — `static`, `explicit`, and `friend`

Source: [`07_static_explicit_friend.md`](./07_static_explicit_friend.md)

<details>
<summary><strong>07.1 — What three separate concepts are often confused around `static`?</strong></summary>

Storage duration answers how long storage exists; scope answers where a name is visible; linkage answers whether declarations in different places name the same entity.

</details>

<details>
<summary><strong>07.2 — What does a function-local static mean?</strong></summary>

It has block scope, is initialized once when control first reaches the declaration, and has static storage duration, so it persists across calls.

</details>

<details>
<summary><strong>07.3 — Is function-local static initialization thread-safe?</strong></summary>

Since C++11, initialization is thread-safe. Later reads and writes to the object are not automatically synchronized.

</details>

<details>
<summary><strong>07.4 — What is a static data member?</strong></summary>

One class-associated object shared by all instances rather than a separate member inside each instance.

</details>

<details>
<summary><strong>07.5 — What restriction does a static member function have?</strong></summary>

It has no implicit object and no `this` pointer, so it directly accesses only static members unless given an object explicitly.

</details>

<details>
<summary><strong>07.6 — What does namespace-scope `static` mean?</strong></summary>

It gives the declared name internal linkage, restricting it to the translation unit. An unnamed namespace is generally the more idiomatic C++ choice.

</details>

<details>
<summary><strong>07.7 — What problem does construct-on-first-use address?</strong></summary>

A function-local static delays construction until first use, helping avoid cross-translation-unit static initialization-order problems.

</details>

<details>
<summary><strong>07.8 — What does `explicit` prevent?</strong></summary>

It prevents the constructor or conversion operator from participating in unintended implicit conversions while still allowing appropriate direct or explicit use.

</details>

<details>
<summary><strong>07.9 — Does `explicit` reject direct initialization?</strong></summary>

No. `Type x{arg};` may call an explicit constructor; copy-initialization such as `Type x = arg;` may not use it as an implicit conversion.

</details>

<details>
<summary><strong>07.10 — What is a friend function?</strong></summary>

A non-member function granted access to a class’s private and protected members.

</details>

<details>
<summary><strong>07.11 — Is friendship inherited, transitive, or reciprocal?</strong></summary>

No. Each friendship grant is explicit and limited to the named friend.

</details>

<details>
<summary><strong>07.12 — What is a hidden friend?</strong></summary>

A friend function defined or declared inside a class and primarily found through ADL. It is useful for symmetric operators without broadly polluting ordinary lookup.

</details>

---

## 08 — Storage, Scope, Lifetime, Ownership, and Temporaries

Source: [`08_stack_heap_lifetime_scope_temporaries.md`](./08_stack_heap_lifetime_scope_temporaries.md)

<details>
<summary><strong>08.1 — How do scope, storage duration, lifetime, and ownership differ?</strong></summary>

Scope is name visibility; storage duration is how long storage exists; lifetime is when a valid object exists in that storage; ownership identifies responsibility for releasing a resource.

</details>

<details>
<summary><strong>08.2 — What are C++’s four storage-duration categories?</strong></summary>

Automatic, static, thread, and dynamic storage duration.

</details>

<details>
<summary><strong>08.3 — Can a name be out of scope while its object remains alive?</strong></summary>

Yes. A local static object persists after leaving its block, and a dynamic object can outlive the local pointer that originally referred to it.

</details>

<details>
<summary><strong>08.4 — Where does a `unique_ptr` live?</strong></summary>

The `unique_ptr` object may have automatic storage while the object it owns has dynamic storage. They are separate objects with linked ownership lifetimes.

</details>

<details>
<summary><strong>08.5 — Why should `new`/`delete` not be mixed with `malloc`/`free`?</strong></summary>

They use different allocation/lifetime mechanisms. `new` constructs and `delete` destroys; `malloc` and `free` only manage raw storage. Mismatching them is undefined behavior.

</details>

<details>
<summary><strong>08.6 — Does a raw pointer, reference, iterator, span, or view extend lifetime?</strong></summary>

No. These are borrowed handles; their source object must remain alive and valid.

</details>

<details>
<summary><strong>08.7 — Why is returning a reference to a local object wrong?</strong></summary>

The local object’s lifetime ends when the function returns, leaving the returned reference dangling.

</details>

<details>
<summary><strong>08.8 — How long do most temporaries live?</strong></summary>

Until the end of the full expression in which they were created, unless a specific lifetime-extension rule applies.

</details>

<details>
<summary><strong>08.9 — When can a reference extend a temporary’s lifetime?</strong></summary>

Certain direct bindings, such as a local `const T&` bound directly to a temporary, extend it to the reference’s lifetime. Passing through or returning another reference does not re-extend it.

</details>

<details>
<summary><strong>08.10 — What commonly invalidates container handles?</strong></summary>

Reallocation, erasure, and container-specific structural changes. The exact rules differ by container and operation and must be checked.

</details>

<details>
<summary><strong>08.11 — Why are reference-capturing lambdas dangerous asynchronously?</strong></summary>

The closure may execute after captured local objects have died, leaving dangling references. Capture owned values or establish an explicit shared-lifetime strategy.

</details>

<details>
<summary><strong>08.12 — What are the major ownership models?</strong></summary>

Value ownership, exclusive ownership, shared ownership, and non-owning borrowing. The type system should make the chosen model visible.

</details>

---

## 09 — Modern C++ Language Features and Iteration

Source: [`09_modern_cpp_language_features_and_iteration.md`](./09_modern_cpp_language_features_and_iteration.md)

<details>
<summary><strong>09.1 — Does `auto` mean dynamic typing?</strong></summary>

No. The compiler deduces one static type at compile time.

</details>

<details>
<summary><strong>09.2 — What does plain `auto` usually discard?</strong></summary>

References and top-level const. Add `&`, `const &`, `*`, or `&&` when those semantics are required.

</details>

<details>
<summary><strong>09.3 — What is the brace-deduction trap with `auto`?</strong></summary>

`auto x{1}` deduces `int`, while `auto x = {1}` normally deduces `std::initializer_list<int>`.

</details>

<details>
<summary><strong>09.4 — When should `decltype` or `decltype(auto)` be used?</strong></summary>

When exact declaration/expression type rules matter, especially preserving references in generic forwarding or wrapper code. Parenthesization can change `decltype` results.

</details>

<details>
<summary><strong>09.5 — How do common range-for declarations differ?</strong></summary>

`auto x` copies; `auto& x` mutates the element; `const auto& x` reads without copying; `auto&& x` is a generic binding useful for proxy and range element types.

</details>

<details>
<summary><strong>09.6 — When is an index loop preferable to a range-for?</strong></summary>

When the index, a stride, coordinated traversal of multiple ranges, or precise mutation/erasure control is part of the algorithm.

</details>

<details>
<summary><strong>09.7 — What can structured bindings decompose?</strong></summary>

Arrays, tuple-like types, and eligible class objects. Use `auto&` or `const auto&` when you need references rather than copies.

</details>

<details>
<summary><strong>09.8 — What lifetime risk exists with lambda captures?</strong></summary>

Reference captures and captured `this` can dangle if the closure outlives the referenced object. Capturing `this` does not copy the whole object unless explicitly requested through an appropriate capture.

</details>

<details>
<summary><strong>09.9 — Why prefer a named algorithm over a handwritten loop?</strong></summary>

When it directly expresses intent—such as find, sort, transform, or count—it reduces indexing errors and communicates the operation more clearly.

</details>

<details>
<summary><strong>09.10 — What are the main benefits and risks of C++20 views?</strong></summary>

Views are lazy and composable with little copying, but many are non-owning. Their source range and captured state must outlive use.

</details>

<details>
<summary><strong>09.11 — Why is `nullptr` better than `0` or `NULL`?</strong></summary>

It has a dedicated null-pointer type, avoids integer-overload ambiguity, and expresses pointer intent.

</details>

<details>
<summary><strong>09.12 — What does `enum class` improve?</strong></summary>

It scopes enumerator names and prevents unintended implicit conversion to integers, improving type safety.

</details>

<details>
<summary><strong>09.13 — How do `constexpr`, `consteval`, and `constinit` differ?</strong></summary>

`constexpr` permits compile-time evaluation when requirements are met; `consteval` requires compile-time calls; `constinit` requires static initialization of a static/thread object but does not make it const.

</details>

<details>
<summary><strong>09.14 — What does `noexcept` communicate?</strong></summary>

The function promises not to let exceptions escape. Violating the promise calls `std::terminate`; accurate `noexcept` can also enable safer/faster container moves.

</details>

<details>
<summary><strong>09.15 — What do `optional`, `variant`, `span`, and `string_view` express?</strong></summary>

`optional` expresses possible absence; `variant` a closed set of alternatives; `span` a borrowed contiguous range; `string_view` a borrowed character sequence. The view types do not own their data.

</details>

<details>
<summary><strong>09.16 — Why use `override`, `= default`, and `= delete`?</strong></summary>

They make intent compiler-checkable: verify an override, request the generated operation, or explicitly forbid an operation.

</details>

---

## 10 — C++ Standards and Version Comparison

Source: [`10_cpp_standards_and_version_comparison.md`](./10_cpp_standards_and_version_comparison.md)

<details>
<summary><strong>10.1 — What does a C++ standard specify?</strong></summary>

Core language semantics, standard-library interfaces and behavior, implementation requirements, and categories such as undefined or implementation-defined behavior. It does not specify one compiler, ABI, OS, or build system.

</details>

<details>
<summary><strong>10.2 — Why does `-std=c++20` not guarantee complete C++20 support?</strong></summary>

Compiler front-end and standard-library support are separate, implementations may be incomplete, and platform/linkage/runtime support may also be required.

</details>

<details>
<summary><strong>10.3 — What established C++98/03?</strong></summary>

The original ISO foundation: classes, inheritance, virtual functions, templates, exceptions, namespaces, RTTI, and the standardized STL, followed by corrections and refinements in C++03.

</details>

<details>
<summary><strong>10.4 — Why is C++11 considered the modern-C++ boundary?</strong></summary>

It introduced move semantics, smart pointers, lambdas, expanded `auto`, range-for, `nullptr`, `enum class`, uniform initialization, and a standard concurrency model.

</details>

<details>
<summary><strong>10.5 — What are notable C++14 additions?</strong></summary>

Generic lambdas, relaxed `constexpr`, return-type deduction refinements, and `std::make_unique`.

</details>

<details>
<summary><strong>10.6 — What are notable C++17 additions?</strong></summary>

Structured bindings, `if constexpr`, CTAD, inline variables, guaranteed copy-elision cases, filesystem, and vocabulary types such as `optional`, `variant`, and `string_view`.

</details>

<details>
<summary><strong>10.7 — What are the headline C++20 features?</strong></summary>

Concepts, ranges, coroutines, and modules, plus facilities such as `span`, `jthread`, `format`, and new synchronization primitives.

</details>

<details>
<summary><strong>10.8 — What are notable C++23 additions?</strong></summary>

Facilities such as `expected`, `print`, and `mdspan`, explicit object parameters, and continued ranges and library refinements. Actual compiler/library support must still be verified.

</details>

<details>
<summary><strong>10.9 — How should an in-progress standard such as C++26 be treated?</strong></summary>

As a draft target whose features and implementation status must be verified, not as a universally portable published baseline.

</details>

<details>
<summary><strong>10.10 — What are feature-test macros for?</strong></summary>

They let code test whether a specific language or library feature is available instead of assuming support from a broad version mode alone.

</details>

<details>
<summary><strong>10.11 — How do source compatibility and ABI compatibility differ?</strong></summary>

Source compatibility means code can be recompiled. ABI compatibility means separately built binaries agree on calling conventions, object layout, symbol naming, library contracts, and related binary details.

</details>

<details>
<summary><strong>10.12 — How should a project choose its C++ baseline?</strong></summary>

Balance needed features against compiler/library availability, target platforms, consumers, ABI constraints, certification/tooling, embedded limitations, and maintenance cost—then enforce and test the decision consistently.

</details>

---

## 11 — Templates and Generic Programming

Source: [`11_cpp_templates_and_generic_programming.md`](./11_cpp_templates_and_generic_programming.md)

<details>
<summary><strong>11.1 — What is a template?</strong></summary>

A compile-time pattern for producing type-safe functions, classes, aliases, or variables for concrete type or value arguments.

</details>

<details>
<summary><strong>11.2 — What kinds of template parameters exist?</strong></summary>

Type parameters, non-type parameters, and template-template parameters, each of which may have defaults where allowed.

</details>

<details>
<summary><strong>11.3 — What is template instantiation?</strong></summary>

The process of forming a concrete specialization from a template and specific arguments. Separate arguments may produce distinct specializations and code.

</details>

<details>
<summary><strong>11.4 — What must a substituted template type support?</strong></summary>

Every operation required by the selected code path. Before concepts, these requirements were often implicit compile-time duck typing.

</details>

<details>
<summary><strong>11.5 — Why do template definitions usually live in headers?</strong></summary>

The translation unit performing implicit instantiation must see the complete template definition, not only a declaration.

</details>

<details>
<summary><strong>11.6 — What is the difference between full and partial specialization?</strong></summary>

Full specialization replaces one exact argument set. Partial specialization matches a family of arguments and is available for class and variable templates, not function templates.

</details>

<details>
<summary><strong>11.7 — What should be used instead of partial specialization for function templates?</strong></summary>

Overloading, constraints/concepts, or a helper class that can be partially specialized.

</details>

<details>
<summary><strong>11.8 — What are variadic templates and fold expressions?</strong></summary>

Variadic templates accept parameter packs. Fold expressions reduce a pack over a binary operator, such as `(args + ...)`, with unary/binary and left/right forms.

</details>

<details>
<summary><strong>11.9 — What is SFINAE?</strong></summary>

Substitution Failure Is Not An Error: failure while substituting into certain immediate template contexts removes that candidate from overload resolution instead of producing a hard error.

</details>

<details>
<summary><strong>11.10 — Why prefer C++20 concepts over complex SFINAE?</strong></summary>

Concepts place requirements in the interface, participate clearly in overload ordering, and usually produce better diagnostics and more maintainable code.

</details>

<details>
<summary><strong>11.11 — What is a forwarding reference?</strong></summary>

`T&&` where `T` is deduced under forwarding-reference rules. Combined with `std::forward<T>`, it preserves whether the caller supplied an lvalue or rvalue.

</details>

<details>
<summary><strong>11.12 — What does `if constexpr` do in a template?</strong></summary>

It selects a branch at compile time, and the discarded branch is not instantiated in the same way, allowing type-dependent implementations without requiring every branch to be valid for every type.

</details>

<details>
<summary><strong>11.13 — How do static and runtime polymorphism differ?</strong></summary>

Templates choose behavior at compile time and can inline but require concrete types and may grow code. Virtual functions choose at runtime and support open runtime substitution with indirection and object-model costs.

</details>

<details>
<summary><strong>11.14 — What is CRTP?</strong></summary>

The Curiously Recurring Template Pattern makes a derived type a template argument of its base, enabling forms of static polymorphism and mixin behavior without virtual dispatch.

</details>

<details>
<summary><strong>11.15 — What are the main template costs?</strong></summary>

Longer builds, verbose diagnostics, implementation exposure in headers, possible code bloat, and more complex interfaces. Use templates when genericity and static guarantees justify those costs.

</details>

---

## 12 — Standard Template Library (STL)

Sources: [`12_cpp_standard_template_library_stl.md`](./12_cpp_standard_template_library_stl.md) and the container note in [`00_Notes.md`](./00_Notes.md)

<details>
<summary><strong>12.1 — What is a container, and what are the major STL components?</strong></summary>

A container is an object that stores a collection of other objects. The STL’s generic architecture combines containers, iterators/ranges, algorithms, callables/policies, and allocators.

</details>

<details>
<summary><strong>12.2 — What is the default sequence container?</strong></summary>

`std::vector`, because it provides contiguous storage, cache locality, random access, and amortized constant-time append. Choose another container only for specific required semantics.

</details>

<details>
<summary><strong>12.3 — When should you choose `array`, `deque`, or `list`?</strong></summary>

Use `array` for compile-time fixed contiguous storage, `deque` for efficient operations at both ends, and `list` only when stable nodes and frequent known-position splicing justify allocation and locality costs.

</details>

<details>
<summary><strong>12.4 — How do `map` and `unordered_map` differ?</strong></summary>

`map` is ordered with logarithmic operations and predictable worst-case behavior. `unordered_map` uses hashing for average constant-time operations but has rehash costs and worst-case linear behavior.

</details>

<details>
<summary><strong>12.5 — What are the complexities of common operations?</strong></summary>

`vector[index]`: O(1); `vector::push_back`: amortized O(1); vector middle insertion: O(n); `map::find`: O(log n); `unordered_map::find`: average O(1), worst O(n); `sort`: O(n log n).

</details>

<details>
<summary><strong>12.6 — What is amortized complexity?</strong></summary>

An expensive operation may occur occasionally, but the cost averaged across a sequence of operations has the stated bound—for example, vector growth makes repeated `push_back` amortized O(1).

</details>

<details>
<summary><strong>12.7 — What do `size`, `capacity`, `reserve`, and `resize` mean for a vector?</strong></summary>

`size` is the number of elements; `capacity` is storage available before reallocation; `reserve` changes capacity without changing size; `resize` changes the number of elements.

</details>

<details>
<summary><strong>12.8 — What are the key vector invalidation rules?</strong></summary>

Reallocation invalidates all element pointers, references, and iterators. Erasure invalidates those at and after the erased position. Non-reallocating insertion invalidates handles at and after the insertion point.

</details>

<details>
<summary><strong>12.9 — What invalidation behavior do node-based associative containers have?</strong></summary>

Insertion into ordered associative containers normally preserves existing iterators and references; erasure invalidates only erased elements. Unordered rehash invalidates iterators, though references/pointers to elements generally remain valid.

</details>

<details>
<summary><strong>12.10 — What are the main iterator categories?</strong></summary>

Input, output, forward, bidirectional, random-access, and contiguous. Each category adds capabilities, and algorithms state the minimum category they require.

</details>

<details>
<summary><strong>12.11 — Why can’t `std::sort` sort a `std::list`?</strong></summary>

`std::sort` requires random-access iterators, while `list` provides bidirectional iterators. Use `list::sort`.

</details>

<details>
<summary><strong>12.12 — What is the erase-remove pattern?</strong></summary>

Algorithms such as `remove` move unwanted elements to the logical end and return a new end; the container’s `erase` then physically removes them. In C++20, `std::erase`/`std::erase_if` often express this directly.

</details>

<details>
<summary><strong>12.13 — Does `emplace_back` always outperform `push_back`?</strong></summary>

No. It constructs from arguments in place and can avoid a temporary, but optimization and move costs may make performance equivalent; it can also permit conversions that are less explicit.

</details>

<details>
<summary><strong>12.14 — What contract must a custom hash and equality function satisfy?</strong></summary>

If two keys compare equal, they must produce the same hash. Unequal keys may collide, but excessive collisions hurt performance.

</details>

<details>
<summary><strong>12.15 — What is the main risk of ranges views?</strong></summary>

Views are often lazy and non-owning, so the underlying range and any referenced callable state must remain alive and valid.

</details>

<details>
<summary><strong>12.16 — Why does the initial value’s type matter in `std::accumulate`?</strong></summary>

It determines the accumulator type. Starting a floating-point sum with `0` can accumulate as `int`; use a correctly typed initial value such as `0.0`.

</details>

<details>
<summary><strong>12.17 — What do container adapters provide?</strong></summary>

`stack` provides LIFO, `queue` provides FIFO, and `priority_queue` provides repeated access to the highest-priority element through a restricted underlying-container interface.

</details>

<details>
<summary><strong>12.18 — What extra questions matter before using STL facilities in embedded or real-time code?</strong></summary>

Allocation timing, bounded capacity, iterator validity, exception policy, worst-case complexity, code size, allocator strategy, library support, and whether the operation is deterministic enough for the required context.

</details>

---

## Mixed Final Drill

Use these prompts without opening the chapter sections:

1. Design a function signature for a required read-only buffer and justify it.
2. Explain why const correctness does not prove thread safety.
3. Trace construction and destruction order for a derived object with two members.
4. Decide the copy and move policy for a unique hardware handle.
5. Explain how ADL finds a hidden friend operator.
6. Diagnose a lambda that captures a local by reference and runs on another thread.
7. Compare `vector`, `deque`, and `list` for an embedded work queue.
8. Explain when `std::move` does not actually move anything.
9. Compare concepts, SFINAE, and runtime polymorphism.
10. Select a C++ language baseline for a constrained target and state what you would verify.
