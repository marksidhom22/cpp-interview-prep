from __future__ import annotations

import re
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
NOTES_ROOT = APP_ROOT.parents[1]
DECKS_ROOT = APP_ROOT / "decks"
CANONICAL_DECK = DECKS_ROOT / "cpp-interview.deck.yaml"
sys.path.insert(0, str(APP_ROOT))

from src.storage import read_deck_document, write_deck_document

NOTE_FILES = {
    "00": "00_cpp_embedded_interview_mastery_plan.md",
    "01": "01_cpp_references_vs_pointers.md",
    "02": "02_cpp_const_brief_interview_notes.md",
    "03": "03_const_correctness.md",
    "04": "04_constructors_destructors_initialization.md",
    "05": "05_copy_constructor_and_copy_assignment.md",
    "06": "06_namespaces_and_overloading.md",
    "07": "07_static_explicit_friend.md",
    "08": "08_stack_heap_lifetime_scope_temporaries.md",
    "09": "09_modern_cpp_language_features_and_iteration.md",
    "10": "10_cpp_standards_and_version_comparison.md",
    "11": "11_cpp_templates_and_generic_programming.md",
    "12": "12_cpp_standard_template_library_stl.md",
}

# Each entry selects one or more detailed-reference sections from the existing
# study notes. The original flashcard answer remains the short answer.
SECTION_BY_CARD = {
    "00.3": ("Coding",),
    "00.4": ("Rule of Three", "Rule of Five", "Rule of Zero"),
    "00.5": ("RAII Beyond Memory",),
    "00.6": ("Smart Pointers",),
    "00.7": (
        "Single Responsibility Principle", "Open/Closed Principle",
        "Liskov Substitution Principle", "Interface Segregation Principle",
        "Dependency Inversion Principle",
    ),
    "00.10": ("Concurrency",),
    "00.11": ("Embedded",),
    "01.1": ("Pointer", "Reference"),
    "01.3": ("Reference",),
    "01.4": ("Reference",),
    "01.7": ("Pass by Value",),
    "01.8": ("Prefer `T&` when", "Prefer `const T&` when", "Prefer `T*` when"),
    "01.9": ("Buffer",),
    "01.10": ("Pointer to Const", "Const Pointer"),
    "02.1": ("1. The access-path model",),
    "02.2": ("2. Const objects and initialization",),
    "02.3": ("3. Pointers and two independent kinds of const",),
    "02.4": ("5. Top-level and low-level const",),
    "02.5": ("4. Const references",),
    "02.6": ("5. Top-level and low-level const",),
    "02.7": ("8. Const member functions",),
    "02.8": ("9. Const overloads",),
    "02.9": ("10. Logical constness and `mutable`",),
    "02.10": ("11. `const_cast`",),
    "02.11": ("12. `auto`, templates, and const deduction",),
    "02.12": ("14. Const and concurrency", "15. Const and volatile in embedded code"),
    "03.1": ("1. Const correctness is an API property",),
    "03.2": ("2. Designing parameter contracts",),
    "03.3": ("3. Designing const member functions",),
    "03.4": ("4. The implicit object and overload resolution",),
    "03.5": ("5. Const and non-const overloads",),
    "03.6": ("5. Const and non-const overloads", "6. Accessor design"),
    "03.7": ("7. Shallow const and pointer members",),
    "03.8": ("10. Containers, iterators, and smart pointers",),
    "03.9": ("9. Const propagation",),
    "03.10": ("11. Views and borrowed data",),
    "03.11": ("8. Logical constness",),
    "03.12": ("13. Const correctness and concurrency",),
    "04.1": ("1. Storage, initialization, and construction",),
    "04.2": ("1. Storage, initialization, and construction", "2. Initialization forms"),
    "04.3": ("2. Initialization forms",),
    "04.4": ("4. Member initializer lists",),
    "04.5": ("6. Initialization order",),
    "04.6": ("17. Construction and destruction in inheritance",),
    "04.7": ("7. Default member initializers",),
    "04.8": ("8. Delegating constructors",),
    "04.9": ("10. Converting constructors and `explicit`",),
    "04.10": ("11. `std::initializer_list` constructors",),
    "04.11": ("13. Destruction timing and order",),
    "04.12": ("14. Virtual destructors",),
    "04.13": ("15. Exceptions during construction",),
    "04.14": ("16. Virtual dispatch during construction and destruction",),
    "05.1": ("2. Copy construction", "3. Copy assignment"),
    "05.2": ("2. Copy construction",),
    "05.3": ("4. Compiler-generated copying",),
    "05.4": ("5. Memberwise copy: when it is correct",),
    "05.5": ("6. Shallow-copy failure with owning pointers",),
    "05.6": ("7. Deep-copy Buffer: Rule of Three",),
    "05.7": ("8. Copy-assignment design",),
    "05.8": ("8. Copy-assignment design",),
    "05.9": ("10. Non-copyable types",),
    "05.10": ("13. Move interaction",),
    "05.11": ("14. Inheritance, slicing, and cloning",),
    "05.12": ("11. Rule of Zero", "12. Rule of Three, Five, and Zero"),
    "06.1": ("1. Namespace fundamentals",),
    "06.2": ("4. Using declarations and directives",),
    "06.3": ("6. Unnamed namespaces and internal linkage",),
    "06.4": ("7. Argument-dependent lookup (ADL)",),
    "06.5": ("8. Function overloading",),
    "06.6": ("9. What does not create a distinct overload",),
    "06.7": ("10. Overload resolution",),
    "06.8": ("11. Conversion ranking",),
    "06.9": ("14. Overload hiding in inheritance",),
    "06.10": ("16. Operator-overload fundamentals", "20. Operator pitfalls"),
    "06.11": ("17. Member versus non-member operators",),
    "06.12": ("22. Operator-design guidelines",),
    "07.1": ("1. One keyword, several meanings",),
    "07.2": ("2. Local static variables",),
    "07.3": ("6. Static initialization, concurrency, and order",),
    "07.4": ("3. Static data members",),
    "07.5": ("4. Static member functions",),
    "07.6": ("5. Namespace-scope static and internal linkage",),
    "07.7": ("6. Static initialization, concurrency, and order",),
    "07.8": ("9. Converting constructors",),
    "07.9": ("10. Direct versus copy initialization with explicit",),
    "07.10": ("14. Friend functions",),
    "07.11": ("17. Friendship rules",),
    "07.12": ("18. Hidden friends and operators",),
    "08.1": ("1. Separate scope, storage duration, lifetime, and ownership",),
    "08.2": ("2. The four storage durations",),
    "08.3": ("8. Scope and name hiding",),
    "08.5": ("5. `new`, `delete`, `malloc`, and `free`",),
    "08.6": ("9. Borrowed handles and dangling",),
    "08.7": ("10. Returning pointers, references, and views",),
    "08.8": ("11. Temporary objects",),
    "08.9": ("12. Temporary lifetime extension",),
    "08.10": ("14. Container invalidation",),
    "08.11": ("15. Lambda, callback, and thread lifetimes",),
    "08.12": ("16. Ownership models",),
    "09.1": ("2. `auto` type deduction",),
    "09.2": ("3. `auto` with references, pointers, and const",),
    "09.3": ("4. Brace deduction and `auto` pitfalls",),
    "09.4": ("5. `decltype` and `decltype(auto)`",),
    "09.5": ("6. Range-based `for` fundamentals", "8. Choosing the loop variable"),
    "09.6": ("9. Index loops, iterator loops, and range loops",),
    "09.7": ("10. Structured bindings",),
    "09.8": ("12. Lambda lifetime and `this`",),
    "09.9": ("13. Algorithms versus handwritten loops",),
    "09.10": ("14. C++20 ranges and views",),
    "09.11": ("15. `nullptr`",),
    "09.12": ("16. `enum class`",),
    "09.13": ("18. `constexpr`, `consteval`, and `constinit`",),
    "09.14": ("19. `noexcept`",),
    "09.15": ("23. `std::optional`, `std::variant`, and vocabulary types", "24. `std::span` and `std::string_view`"),
    "09.16": ("25. `override`, `final`, `= default`, and `= delete`",),
    "10.1": ("1. What a C++ version means",),
    "10.2": ("12. Selecting a standard in builds",),
    "10.3": ("2. C++98: the first ISO standard", "3. C++03: stabilization and correction"),
    "10.4": ("4. The pre-modern versus modern boundary", "5. C++11: the major modernization"),
    "10.5": ("6. C++14: refinement of C++11",),
    "10.6": ("7. C++17: practical modern C++",),
    "10.7": ("8. C++20: concepts, ranges, coroutines, and modules",),
    "10.8": ("9. C++23: library and language refinement",),
    "10.9": ("10. C++26: work in progress",),
    "10.10": ("11. Feature-test macros",),
    "10.11": ("13. Source compatibility, binary compatibility, and ABI",),
    "10.12": ("16. Choosing a project baseline",),
    "11.1": ("1. The template mental model",),
    "11.2": ("2. Template parameter kinds",),
    "11.3": ("8. Instantiation",),
    "11.4": ("4. Template requirements and compile-time duck typing",),
    "11.5": ("9. Why template definitions usually live in headers",),
    "11.6": ("11. Full and partial specialization",),
    "11.7": ("12. Overloading versus specialization",),
    "11.8": ("14. Variadic templates and parameter packs", "15. Fold expressions"),
    "11.9": ("19. SFINAE",),
    "11.10": ("20. Concepts and `requires`",),
    "11.11": ("23. Forwarding references and perfect forwarding",),
    "11.12": ("21. `if constexpr`",),
    "11.13": ("27. Templates versus runtime polymorphism",),
    "11.14": ("25. Static polymorphism and CRTP",),
    "11.15": ("26. Template cost model",),
    "12.1": ("2. The STL architecture",),
    "12.2": ("5. `std::vector`",),
    "12.3": ("4. `std::array`", "6. `std::deque`", "7. `std::list` and `std::forward_list`"),
    "12.4": ("8. Ordered associative containers", "9. Unordered associative containers"),
    "12.5": ("18. Complexity guarantees and amortization",),
    "12.6": ("18. Complexity guarantees and amortization",),
    "12.7": ("19. `size`, `capacity`, `reserve`, and `resize`",),
    "12.8": ("15. Iterator, pointer, and reference invalidation",),
    "12.9": ("15. Iterator, pointer, and reference invalidation",),
    "12.10": ("14. Iterator categories",),
    "12.11": ("7. `std::list` and `std::forward_list`", "14. Iterator categories"),
    "12.12": ("24. The erase-remove pattern",),
    "12.13": ("20. Insertion, emplacement, and assignment APIs",),
    "12.14": ("22. Hashing and custom keys",),
    "12.15": ("17. C++20 ranges algorithms and views",),
    "12.16": ("25. Numeric algorithms",),
    "12.17": ("11. Container adapters",),
    "12.18": ("30. Embedded and real-time considerations",),
}

CUSTOM_DETAILS = {
    "00.1": """A balanced plan should connect language knowledge to problem solving and system constraints. Modern C++ supplies safe ownership and expressive types; algorithms supply problem-solving patterns; OOP and design organize change; OS/concurrency explains execution and synchronization; embedded/system design adds timing, memory, hardware, failure recovery, and debugging constraints.\n\nDo not study these as isolated silos. For example, a producer-consumer exercise combines containers, ownership, concurrency, shutdown design, and complexity analysis.""",
    "00.2": """The split is a starting budget, not a law. Use the largest block for coding practice because interviews require fluent implementation under time pressure. Keep modern C++ and systems work in the weekly loop so correct algorithms are also expressed with safe ownership, clear interfaces, and realistic concurrency assumptions.\n\nRebalance using evidence: move time toward categories where timed practice, mock interviews, or review statistics show repeated misses.""",
    "00.4": """These rules describe which special member functions a resource-owning type may need.\n\n- **Rule of Three:** if a type requires a custom destructor, copy constructor, or copy-assignment operator, it probably needs all three because those operations must agree on ownership.\n- **Rule of Five:** in modern C++, also consider the move constructor and move-assignment operator. Moves can transfer a resource instead of duplicating it.\n- **Rule of Zero:** the preferred design is to store resources in RAII members such as containers, strings, and smart pointers so the compiler-generated special members are already correct.\n\n```cpp\nclass Report {\npublic:\n    Report(std::string name, std::vector<int> values)\n        : name_{std::move(name)}, values_{std::move(values)} {}\n\nprivate:\n    std::string name_;\n    std::vector<int> values_;\n}; // Rule of Zero: no custom destructor/copy/move code\n```\n\nDo not implement all five mechanically. First decide whether the type should be copyable, movable, both, or neither. A unique operating-system handle, for example, is usually movable but not copyable.""",
    "00.5": """RAII makes cleanup a consequence of normal C++ lifetime rules. A constructor establishes a valid resource-owning object; its destructor releases the resource. When control leaves a scope—by normal return, early return, or exception—fully constructed local objects are destroyed in reverse order.\n\nA lock is the classic example:\n\n```cpp\nvoid update(State& state, std::mutex& mutex) {\n    std::lock_guard<std::mutex> lock{mutex};\n    modify(state);\n} // lock is released automatically\n```\n\nThe same idea applies to memory (`std::unique_ptr`, containers), files (`std::fstream`), threads (`std::jthread`), and custom handles. RAII does not require dynamic allocation; an embedded program can use fixed-capacity objects and still use deterministic scope-based cleanup.\n\nA well-designed RAII type maintains a clear invariant: either construction succeeds and the object owns a valid resource, or construction fails without exposing a partially usable object. Destructors should release resources reliably and ordinarily must not throw.""",
    "00.7": """SOLID is a set of design heuristics, not a requirement to create many interfaces or classes.\n\n| Principle | Practical question |\n|---|---|\n| Single Responsibility | Does this unit have one cohesive reason to change? |\n| Open/Closed | Can expected variation be added through a stable extension point? |\n| Liskov Substitution | Can a derived implementation replace the base without surprising clients? |\n| Interface Segregation | Does each client depend only on operations it actually needs? |\n| Dependency Inversion | Does policy depend on abstractions rather than construction details? |\n\n```cpp\nstruct SensorReader {\n    virtual Reading read() = 0;\n    virtual ~SensorReader() = default;\n};\n\nclass AlarmPolicy {\npublic:\n    explicit AlarmPolicy(SensorReader& sensor) : sensor_{sensor} {}\n    bool should_alarm() { return sensor_.read().temperature > limit_; }\nprivate:\n    SensorReader& sensor_;\n    double limit_{80.0};\n};\n```\n\n`AlarmPolicy` depends on the small `SensorReader` abstraction, so hardware and test implementations can be substituted. Apply the principles when they reduce coupling and clarify contracts; mechanical application can instead add indirection and complexity.""",
    "00.8": """Composition builds a type from independently replaceable collaborators, which keeps ownership and dependencies visible. Inheritance permanently couples a derived type to a base contract and is appropriate when clients can safely substitute the derived object wherever the base is expected.\n\n```cpp\nclass ReportService {\npublic:\n    explicit ReportService(Renderer& renderer) : renderer_{renderer} {}\n    void run(const Report& report) { renderer_.render(report); }\nprivate:\n    Renderer& renderer_; // composed dependency; not owned\n};\n```\n\nPrefer inheritance for an intentional polymorphic interface, not merely to reuse implementation.""",
    "00.9": """Recognize the signal behind each pattern: pair or partition constraints suggest two pointers; a contiguous subrange suggests sliding window or prefix sums; monotonic decisions suggest binary search; reachability suggests DFS/BFS; repeated best-next selection suggests a heap; overlapping subproblems suggest dynamic programming.\n\nIn an interview, state the invariant before coding. For a sliding window, for example, explain what the current window represents, when it becomes invalid, and why moving the left boundary restores validity.""",
    "00.10": """Start by naming every piece of shared mutable state and which thread or task owns it. Then define how access is synchronized: mutex, atomic operation, message passing, immutable snapshot, or single-thread confinement. “It uses a mutex” is incomplete unless the protected invariant and locking scope are clear.\n\nDiscuss ordering and progress properties as well:\n\n- Which events must happen-before other events?\n- Can operations block, starve, deadlock, or suffer priority inversion?\n- What wakes a waiting thread, and is the condition checked in a loop?\n- How are cancellation, shutdown, errors, and partially completed work handled?\n- Which objects must remain alive until background work finishes?\n\n```cpp\nstd::mutex mutex;\nstd::condition_variable ready;\nbool stopping = false;\nstd::queue<Job> jobs;\n\nready.wait(lock, [&] { return stopping || !jobs.empty(); });\n```\n\nFinally, state how the design will be tested: stress tests, race detectors, deterministic scheduling where possible, and explicit shutdown tests.""",
    "00.11": """Embedded and real-time evaluation focuses on bounds and failure modes rather than only average throughput. Ask for worst-case execution time, maximum memory use, stack depth, allocation behavior, interrupt latency, scheduling policy, and the consequences of missing a deadline.\n\nHardware access adds constraints that ordinary desktop code may not have:\n\n- memory-mapped I/O and the correct use of `volatile` or platform primitives;\n- interrupt-safe communication and minimal ISR work;\n- DMA/cache coherency and alignment requirements;\n- watchdog servicing and recovery after partial failure;\n- bounded queues and defined overload behavior;\n- no hidden unbounded allocation or blocking on critical paths.\n\n```cpp\n// Sketch only: the platform API defines the required ordering semantics.\nvolatile std::uint32_t* const status = status_register_address;\nconst auto snapshot = *status;\n```\n\n`volatile` describes observable accesses; it does not provide thread synchronization. Use the platform's atomic, barrier, or critical-section facilities where concurrency or device ordering requires them.""",
    "00.12": """Readiness is demonstrated under realistic constraints, not by finishing a reading list. You should be able to clarify an unfamiliar problem, choose a defensible design, implement it without relying on accidental behavior, test edge cases, and explain complexity and tradeoffs aloud.\n\nUse timed problems and mock interviews as the final feedback loop. A weak result identifies the next practice target; it is not a reason to restart the entire curriculum.""",
    "01.2": """These types communicate two independent API properties: whether the argument is required and whether mutation is allowed through that access path.\n\n| Type | Nullable? | Reseatable? | Mutation through it? | Typical meaning |\n|---|---:|---:|---:|---|\n| `T&` | No | No | Yes | required mutable borrow |\n| `const T&` | No | No | No | required read-only borrow |\n| `T*` | Yes | Yes | Yes | optional mutable borrow |\n| `const T*` | Yes | Yes | No | optional read-only borrow |\n\nNone of these types normally owns the object. Use an owning value, container, or smart pointer when ownership transfer or sharing is part of the contract.""",
    "01.3": """A reference is bound during initialization and is not later reseated. Assignment through a reference therefore invokes assignment on the referred object.\n\n```cpp\nint first = 1;\nint second = 9;\nint& ref = first;\n\nref = second; // assigns 9 to first; ref still aliases first\n```\n\nAfter the assignment, both `first` and `second` contain `9`, and `&ref == &first` remains true. By contrast, assigning a pointer changes the stored address:\n\n```cpp\nint* ptr = &first;\nptr = &second; // ptr is now reseated\n```\n\nThis distinction is why a reference expresses one stable alias while a pointer can represent a changing traversal or optional target.""",
    "01.4": """A reference must be bound to an object when it is initialized, and the language provides no operation that reseats it. This makes `T&` a good syntax-level expression of “required object.”\n\n```cpp\nvoid update(Device& device);  // caller must provide a Device\nvoid update(Device* device);  // nullptr can represent absence\n```\n\nLow-level tricks can form an invalid reference—for example, dereferencing a null pointer—but using the result has undefined behavior. That does not make null a supported reference state.\n\nA reference can still dangle after its target's lifetime ends. Non-nullability and lifetime safety are separate properties: the type prevents an intentional empty value, but the program must still guarantee that the referred object remains alive.""",
    "01.5": """A raw pointer or reference normally describes access, not lifetime management. The caller must ensure the referred object outlives every use. Ownership should be explicit in the type: a value or container owns its state, `std::unique_ptr<T>` expresses exclusive ownership, and `std::shared_ptr<T>` expresses shared lifetime.\n\nA raw pointer can technically point to dynamically allocated storage, but the pointer type alone does not say who must release it. That ambiguity is why owning raw pointers are avoided in modern interfaces.""",
    "01.6": """Both can dangle because neither extends the target's lifetime. Common causes include returning a handle to a local variable, retaining a handle after its owner is destroyed, vector reallocation, erasing a container element, and asynchronous callbacks that outlive captured objects.\n\n```cpp\nconst int& bad() {\n    int local = 42;\n    return local; // dangling immediately after return\n}\n```\n\nA reference's non-null syntax is not a lifetime guarantee; lifetime must still be established by design.""",
    "01.7": """Pass small scalar or cheaply copied value types by value because the callee receives an independent value and the interface is simple. Also pass by value when the function needs to store or transform its own copy; callers can copy lvalues or move rvalues into the parameter.\n\n```cpp\nclass Worker {\npublic:\n    explicit Worker(std::string name) : name_{std::move(name)} {}\nprivate:\n    std::string name_;\n};\n```\n\nThis “value then move” sink pattern is often a good tradeoff when the function unconditionally retains the argument. It can be less suitable when copying an lvalue is expensive and the function may not keep it, or when separate `const T&` and `T&&` overloads are justified by measured performance.\n\nDo not apply a fixed byte-size rule blindly. Consider copy cost, ownership intent, ABI conventions, and whether the type is a lightweight view such as `std::span` or `std::string_view`.""",
    "01.8": """Choose the parameter type from the contract rather than from a blanket performance rule:\n\n| Contract | Typical parameter |\n|---|---|\n| Required, read-only borrow | `const T&` |\n| Required, mutable borrow | `T&` |\n| Optional, read-only borrow | `const T*` |\n| Optional, mutable borrow | `T*` |\n| Transfer exclusive ownership | `std::unique_ptr<T>` |\n| Share lifetime | `std::shared_ptr<T>` only when genuinely required |\n\n```cpp\nvoid inspect(const Device& device);\nvoid reset(Device& device);\nvoid inspect_if_present(const Device* device);\nvoid install(std::unique_ptr<Device> device);\n```\n\nReferences make required presence obvious and avoid repeated null checks. Pointers make optionality and reseating visible. Neither raw form normally owns the object, so document the lifetime relationship when it is not self-evident. For contiguous sequences, prefer a range/view type such as `std::span<T>` over a pointer-plus-unrelated-length pair.""",
    "01.9": """Use `std::span<T>` for a borrowed contiguous sequence when C++20 is available. It carries a pointer and an element count together, supports arrays, vectors, and pointer/count sources, and does not own or extend the lifetime of the elements.\n\n```cpp\nvoid normalize(std::span<float> samples) {\n    for (float& sample : samples) {\n        sample = std::clamp(sample, -1.0f, 1.0f);\n    }\n}\n\nstd::array<float, 128> buffer{};\nnormalize(buffer);\n```\n\nUse `std::span<const T>` for read-only access. A naked `T*` does not communicate the number of elements; a C-style pointer plus length can work at an ABI boundary, but the pair should be wrapped into a span as soon as practical. The caller must keep the underlying storage alive and avoid invalidating it while the span is used.""",
    "01.11": """An array element must be an object with its own storage, size, and assignable element semantics. References are aliases rather than objects, cannot be reseated, and do not satisfy those requirements. Pointers are ordinary objects, so an array can store and assign pointer values.\n\nUse `std::reference_wrapper<T>` when a reseatable, storable reference-like element is needed:\n\n```cpp\nstd::array<std::reference_wrapper<int>, 2> refs{x, y};\nrefs[0].get() = 7;\n```""",
    "01.12": """Returning a reference is safe only when the referred object is guaranteed to outlive the caller's use of the result. Typical safe sources are the object itself (`return *this`), a member of a sufficiently long-lived object, or an element in a container whose lifetime and invalidation rules are understood.\n\nNever return a reference to a local automatic object. Also document invalidation: a reference to a vector element may become invalid after reallocation even though the vector itself remains alive.""",
    "08.4": """The smart-pointer object and its pointee have independent storage durations. A local `std::unique_ptr<T>` usually has automatic storage, while the object created by `std::make_unique<T>()` has dynamic storage. Moving the `unique_ptr` transfers ownership of that same pointee; it does not move the allocation itself.\n\n```cpp\nauto p = std::make_unique<Device>(); // p: automatic; Device: dynamic\nauto q = std::move(p);               // q now owns the Device\n```\n\nA `unique_ptr` can itself be a data member, a static object, or dynamically allocated, so saying that it “lives on the stack” is not generally correct.""",
    "11.7": """Function templates cannot be partially specialized. Use function overloading—often constrained with concepts—because overload resolution is the language mechanism designed to choose among function implementations.\n\n```cpp\ntemplate<class T>\nvoid encode(const T& value);\n\ntemplate<std::integral T>\nvoid encode(T value);\n\ntemplate<class T>\nvoid encode(const std::vector<T>& values);\n```\n\nFull specialization of a function template is legal, but overloads usually interact more predictably with overload resolution and are easier to extend. For type-dependent implementation details, another option is to delegate to a class template, because class templates do support partial specialization.""",
    "11.15": """Templates trade runtime abstraction cost for compile-time work and per-specialization code. The main costs are longer builds, larger binaries from repeated instantiations, complex diagnostics, more implementation exposed in headers, and accidental coupling to compile-time details.\n\nMitigations include explicit instantiation for common types, small non-template implementation functions behind template front ends, concepts that fail early with clear contracts, and avoiding unnecessary combinations of template parameters.\n\nThe runtime benefit can be substantial: types and operations are known statically, enabling inlining, constant propagation, and zero-overhead abstraction. But “compile-time” does not automatically mean “free”—inspect build time, object size, final binary size, and generated code when those constraints matter.""",
}

MERMAID_BY_CARD = {
    "00.3": """flowchart LR
    A[Clarify requirements] --> B[State brute force]
    B --> C[Derive optimized approach]
    C --> D[State invariant]
    D --> E[Implement]
    E --> F[Test edge cases]
    F --> G[Explain complexity]""",
    "00.4": """flowchart TD
    A[Does the type directly manage a resource?] -->|No| Z[Rule of Zero]
    A -->|Yes| B[Custom destructor/copy needed]
    B --> C[Rule of Three]
    C --> D[Add move operations]
    D --> E[Rule of Five]""",
    "00.5": """flowchart LR
    A[Enter scope] --> B[Construct RAII owner]
    B --> C[Use the resource]
    C --> D{How scope exits}
    D -->|Normal return| E[Destructor releases resource]
    D -->|Early return| E
    D -->|Exception| E""",
    "01.8": """flowchart TD
    A[Borrowed parameter] --> B{May it be absent?}
    B -->|Yes| C{May callee mutate it?}
    C -->|Yes| D[T pointer]
    C -->|No| E[const T pointer]
    B -->|No| F{May callee mutate it?}
    F -->|Yes| G[T reference]
    F -->|No| H[const T reference]""",
    "04.6": """flowchart TD
    A[Virtual base classes] --> B[Direct base classes]
    B --> C[Data members in declaration order]
    C --> D[Derived constructor body]
    D --> E[Destruction runs in exact reverse order]""",
    "04.13": """flowchart TD
    A[Begin construction] --> B[Construct bases and members]
    B --> C{Constructor throws?}
    C -->|No| D[Object becomes fully constructed]
    C -->|Yes| E[Destroy completed subobjects in reverse order]
    E --> F[Most-derived destructor does not run]""",
    "05.5": """flowchart LR
    A[Object A] --> P[Same allocation]
    B[Shallow-copied Object B] --> P
    A --> D1[Destructor deletes allocation]
    B --> D2[Second delete: undefined behavior]""",
    "06.7": """flowchart LR
    A[Name lookup] --> B[Build candidate set]
    B --> C[Discard non-viable functions]
    C --> D[Rank implicit conversions]
    D --> E{Unique best candidate?}
    E -->|Yes| F[Call it]
    E -->|No| G[Compile-time ambiguity/error]""",
    "08.1": """flowchart TD
    S[Scope: where a name is visible] --> O[Object]
    D[Storage duration: how long storage exists] --> O
    L[Lifetime: when an object exists in that storage] --> O
    W[Ownership: who releases or controls the resource] --> O""",
    "08.12": """flowchart TD
    A[Resource] --> B[Value ownership]
    A --> C[Exclusive ownership: unique_ptr]
    A --> D[Shared ownership: shared_ptr]
    A --> E[Non-owning observation: reference pointer span view]
    D --> F[weak_ptr observes without extending lifetime]""",
    "10.4": """timeline
    title Modern C++ evolution
    1998 : First ISO C++ standard
    2011 : Move semantics, RAII vocabulary, lambdas, concurrency
    2014 : Refinement
    2017 : Practical library and language improvements
    2020 : Concepts, ranges, coroutines, modules
    2023 : Further language and library refinement""",
    "11.3": """flowchart LR
    A[Template definition] --> B[Use with concrete arguments]
    B --> C[Substitution and constraint checking]
    C --> D[Instantiate specialization]
    D --> E[Compile generated function or class]""",
    "12.1": """flowchart LR
    C[Container owns elements] --> I[Iterators describe a range]
    I --> A[Algorithms operate on the range]
    P[Callables and policies customize behavior] --> A
    M[Allocator controls storage mechanics] --> C""",
}


def note_sections(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^## (.+)$", text, flags=re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        body = re.split(r"^### Interview question\s*$", body, maxsplit=1, flags=re.MULTILINE)[0].strip()
        if body:
            sections[heading] = body
    return sections


def short_answer(answer: str) -> str:
    if answer.startswith("## Short answer"):
        return answer.split("## Detailed answer", 1)[0].removeprefix("## Short answer").strip()
    return answer.strip()


def build_detail(card_id: str, all_sections: dict[str, dict[str, str]]) -> str:
    if card_id in CUSTOM_DETAILS:
        return CUSTOM_DETAILS[card_id].strip()
    prefix = card_id.split(".", 1)[0]
    headings = SECTION_BY_CARD.get(card_id)
    if not headings:
        raise KeyError(f"No detailed-answer source configured for {card_id}")
    sections = all_sections[prefix]
    missing = [heading for heading in headings if heading not in sections]
    if missing:
        raise KeyError(f"Missing sections for {card_id}: {missing}")
    return "\n\n".join(sections[heading] for heading in headings)


def enriched_answer(card_id: str, answer: str, all_sections: dict[str, dict[str, str]]) -> str:
    result = (
        f"## Short answer\n\n{short_answer(answer)}\n\n"
        f"## Detailed answer\n\n{build_detail(card_id, all_sections)}"
    )
    diagram = MERMAID_BY_CARD.get(card_id)
    if diagram:
        result += f"\n\n### Concept diagram\n\n```mermaid\n{diagram}\n```"
    return result.strip()


def main() -> None:
    all_sections = {
        prefix: note_sections(NOTES_ROOT / filename)
        for prefix, filename in NOTE_FILES.items()
    }
    canonical = read_deck_document(CANONICAL_DECK)
    canonical_cards = canonical["cards"]
    if not isinstance(canonical_cards, list) or len(canonical_cards) != 171:
        raise ValueError("The canonical C++ deck must contain exactly 171 cards")

    enriched: dict[str, str] = {}
    for card in canonical_cards:
        card_id = str(card["id"])
        answer = enriched_answer(card_id, str(card["answer"]), all_sections)
        card["answer"] = answer
        enriched[card_id] = answer
    write_deck_document(CANONICAL_DECK, canonical)

    updated_files = [CANONICAL_DECK.name]
    updated_cards = len(enriched)
    for path in sorted(DECKS_ROOT.glob("cpp-study-*.deck.yaml")):
        document = read_deck_document(path)
        cards = document["cards"]
        if not isinstance(cards, list):
            raise ValueError(f"Invalid cards collection in {path}")
        for card in cards:
            card_id = str(card["id"])
            if card_id not in enriched:
                raise KeyError(f"Topic deck card {card_id} is missing from the canonical deck")
            card["answer"] = enriched[card_id]
        write_deck_document(path, document)
        updated_files.append(path.name)
        updated_cards += len(cards)

    print(f"Updated {updated_cards} card copies across {len(updated_files)} deck files")


if __name__ == "__main__":
    main()
