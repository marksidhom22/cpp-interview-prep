from __future__ import annotations

import copy
import sys
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage import read_deck_document, write_deck_document


SOURCE_PATH = PROJECT_ROOT / "decks" / "cpp-interview.deck.yaml"
TOPIC_SLUGS = {
    "00": "study-plan",
    "01": "references-vs-pointers",
    "02": "const-syntax-and-meaning",
    "03": "const-correctness",
    "04": "constructors-and-initialization",
    "05": "copy-and-assignment",
    "06": "namespaces-and-overloading",
    "07": "static-explicit-and-friend",
    "08": "lifetime-ownership-and-temporaries",
    "09": "modern-cpp-and-iteration",
    "10": "cpp-standards",
    "11": "templates-and-generic-programming",
    "12": "standard-library",
}

DETAILS = {
    "00.1": "These areas reinforce one another: strong language fundamentals help you reason about algorithms, and systems context helps you explain real tradeoffs.",
    "00.2": "Treat these percentages as a starting point, then shift time toward weak areas based on timed practice and review results.",
    "00.3": "State input constraints and edge cases before coding; after implementation, test both representative cases and boundary conditions.",
    "00.4": "These rules matter most when a class directly manages a resource; standard RAII members often make the Rule of Zero possible.",
    "00.5": "Examples include `std::lock_guard` releasing a mutex and `std::unique_ptr` deleting its object when the owner leaves scope.",
    "00.6": "Prefer `unique_ptr` until sharing is required; a `weak_ptr` must be locked to obtain a temporary `shared_ptr` before use.",
    "00.7": "Use the principles to evaluate coupling and changeability, not as a requirement to create extra classes or layers.",
    "00.8": "Composition delegates work to owned or borrowed components; inheritance should preserve the base type's behavioral contract.",
    "00.9": "Pattern recognition is a starting hypothesis; verify the pattern against the input constraints and prove its correctness.",
    "00.10": "A complete design also identifies who owns shared objects and how shutdown waits for workers to stop safely.",
    "00.11": "For hard real-time paths, justify worst-case execution time and memory behavior rather than relying only on average benchmarks.",
    "00.12": "Readiness is demonstrated by repeatable performance on unfamiliar tasks, not by finishing a fixed reading list.",
    "01.1": "A pointer has its own value and can be copied or changed to refer elsewhere; a reference acts as another name for its referent.",
    "01.2": "The type communicates whether a value is required, nullable, mutable through this access path, and owning; raw handles alone do not own.",
    "01.3": "After initialization, `ref` continues to designate its original object, so assignment writes into that object.",
    "01.4": "Use a pointer or `std::optional<std::reference_wrapper<T>>` when absence or reselection must be represented explicitly.",
    "01.5": "Ownership types document cleanup responsibility and encode it in destruction, unlike a borrowed pointer or reference.",
    "01.6": "Lifetime safety depends on the referent outliving each use; vector reallocation, erasure, and owner destruction can invalidate handles.",
    "01.7": "Passing by value is also useful for a sink parameter that the function will store or move from, especially for movable types.",
    "01.8": "A reference communicates required access; a pointer naturally communicates optional access, but either contract should be documented clearly.",
    "01.9": "A span does not own its elements, so its backing storage must outlive the span and any operation using it.",
    "01.10": "Read pointer declarations from the variable outward: `const` next to the base type qualifies the pointee, while trailing `const` qualifies the pointer.",
    "01.11": "A reference cannot be default-initialized or rebound like an ordinary value, while pointers have those value semantics.",
    "01.12": "Returning a reference is safe only when the referenced storage has a lifetime that clearly exceeds the caller's use.",
    "02.1": "Constness applies to an access path: another non-const alias may still modify the same object if the object itself was not declared const.",
    "02.2": "A const object's initialization is its one opportunity to establish its value; later assignment would violate the const contract.",
    "02.3": "In these declarations, `const` qualifies the pointed-to `int`; placing it before or after `int` does not change the type.",
    "02.4": "For `const int* const p`, both levels are const: the pointer cannot be reseated and the pointee cannot be modified through it.",
    "02.5": "A temporary bound directly to a local const reference can live to the reference's scope, subject to specific language lifetime rules.",
    "02.6": "Top-level cv-qualification is ignored when forming a function type for a by-value parameter, so those declarations collide.",
    "02.7": "The const member-function qualifier affects overload resolution and restricts ordinary mutation through the implicit `this` access path.",
    "02.8": "This pair preserves constness in both directions: callers get writable access only when the container itself is mutable.",
    "02.9": "A cache may be `mutable` if changing it cannot change the object's externally observable value or violate synchronization requirements.",
    "02.10": "Writing through a cast-away-const pointer is undefined when the original object was declared const, even if the cast compiles.",
    "02.11": "Use `decltype(auto)` or an explicit reference declaration when a wrapper must preserve the expression's reference and cv-qualification.",
    "02.12": "Use atomics or synchronization for data-race prevention; use volatile only for implementation-specific observable access requirements such as MMIO.",
    "03.1": "A const-correct API lets callers and the compiler verify mutation permissions consistently from parameters through return values.",
    "03.2": "Together these questions reveal the ownership and mutation contract, preventing accidental copies, hidden output parameters, and unclear lifetimes.",
    "03.3": "A const query can be used with const objects and can be called by other const operations, improving composability.",
    "03.4": "A non-const object can bind to either member overload, while a const object cannot call a member requiring mutable access.",
    "03.5": "Member overloads may differ by the cv/ref qualification of the implicit object parameter, but not by return type alone.",
    "03.6": "The returned reference remains borrowed: callers must not outlive the object or retain it across invalidating mutations.",
    "03.7": "Const prevents reassignment of the pointer member itself, but does not automatically make the pointed-to object const.",
    "03.8": "For `const unique_ptr<T>`, the handle is const while `T` can still be mutable; `unique_ptr<const T>` makes the pointee read-only.",
    "03.9": "Const qualification must be carried through every helper in the call chain or the outer const operation cannot call it.",
    "03.10": "A view such as `span` or `string_view` carries access information, not ownership or automatic lifetime extension.",
    "03.11": "If callers can observe the mutation as a change in the object's meaningful value, it is not merely implementation detail.",
    "03.12": "Even a const method can race with another thread or alias; const is a type-level access rule, not a synchronization primitive.",
    "04.1": "Storage can exist before an object lifetime begins, for example in raw storage; construction establishes the object's valid state.",
    "04.2": "Initialization is part of object creation and may invoke a constructor; assignment operates on an already-live destination.",
    "04.3": "The declaration creates `w` by invoking copy initialization; only a later assignment expression targets an existing `w`.",
    "04.4": "Direct member initialization avoids constructing a default value and then assigning, and it supports members that cannot be default-constructed.",
    "04.5": "The compiler initializes members in declaration order even if the initializer list is written differently; matching the order avoids bugs and warnings.",
    "04.6": "The destructor runs in reverse order, so each subobject is torn down while the subobjects it may depend on are still alive.",
    "04.7": "An explicit member initializer in a constructor takes precedence over the in-class default for that constructor.",
    "04.8": "The delegating target constructor completes initialization first, after which the delegating constructor body runs.",
    "04.9": "An implicit converting constructor can make overload resolution accept unintended argument conversions; `explicit` keeps that choice visible.",
    "04.10": "For example, a brace expression may select an `initializer_list` overload instead of a count-and-value constructor.",
    "04.11": "RAII makes these lifetime endpoints predictable, including cleanup during stack unwinding after an exception.",
    "04.12": "A virtual destructor ensures destruction dispatches through the dynamic type when deleting a derived object via a base pointer.",
    "04.13": "Only fully constructed subobjects are cleaned up; the constructor's own destructor cannot run because the complete object never finished construction.",
    "04.14": "Calling a virtual function from a constructor or destructor does not dispatch into a derived portion that is not currently alive.",
    "05.1": "The distinction determines which special member is selected and whether a destination's old resources must first be released.",
    "05.2": "A const lvalue reference avoids making a copy just to enter the copy constructor and supports ordinary source objects.",
    "05.3": "Memberwise copying is recursive: each base and member applies its own copy semantics to its corresponding subobject.",
    "05.4": "Members such as `std::vector` own and copy their contents correctly, so the compiler-generated operation usually expresses value semantics.",
    "05.5": "Both copies may later free the same address; use a value-owning member or define a deliberate deep-copy/unique-ownership policy.",
    "05.6": "A deep copy gives each object independent owned storage, so updates and destruction of one do not affect the other.",
    "05.7": "Acquire replacement resources safely before discarding old state, so failure does not leave the destination invalid or leak memory.",
    "05.8": "The temporary copy is built before the swap, so a copy failure leaves the target unchanged; this guarantee may cost an allocation.",
    "05.9": "Deleting copy operations prevents accidental duplication at compile time; moving may still be allowed if transfer is meaningful.",
    "05.10": "A user-declared destructor is often a signal to review all copy and move operations rather than assuming moves will be generated.",
    "05.11": "Slicing loses derived state and dynamic behavior; polymorphic APIs should generally pass or own objects through pointers or references.",
    "05.12": "The Rule of Zero reduces custom lifetime code, which in turn reduces exception-safety and maintenance risks.",
    "06.1": "Qualified names such as `sensor::read` make ownership of names explicit and allow independent libraries to reuse common identifiers.",
    "06.2": "Headers are included into many translation units, so a using-directive there can unexpectedly affect unrelated client code.",
    "06.3": "Names in an unnamed namespace are private to that translation unit and cannot be linked as the same entity from another one.",
    "06.4": "ADL enables calls such as `swap(a, b)` to find operations associated with argument types without qualifying a namespace at the call site.",
    "06.5": "The parameter list or member cv/ref qualification must differ in a way the language recognizes; return type alone is insufficient.",
    "06.6": "The compiler resolves the call before considering how its result is used, so return types cannot disambiguate otherwise identical candidates.",
    "06.7": "If no unique best viable candidate exists, the call is ambiguous and must be corrected with better types or explicit qualification.",
    "06.8": "This ranking is a useful summary; ties, reference binding, list-initialization, and user-defined conversions have additional rules.",
    "06.9": "The `using` declaration adds the base overload set to derived lookup, after which normal overload resolution can select among candidates.",
    "06.10": "Overloaded operators retain the language's built-in precedence and evaluation model, so they cannot alter parsing or sequencing rules.",
    "06.11": "A non-member can support conversions on either operand; a hidden friend limits ordinary lookup while remaining discoverable by ADL.",
    "06.12": "Surprising operators make code harder to read and can violate users' expectations about familiar syntax.",
    "07.1": "These are independent properties: a name can have local scope while referring to storage that persists for the entire program.",
    "07.2": "Its initialization occurs on the first pass through the declaration, and the initialized object remains alive until program termination.",
    "07.3": "The guarantee covers one-time initialization only; concurrent mutation of the initialized object still needs synchronization.",
    "07.4": "A static data member is not stored separately inside each object, so changing it affects the shared class-level state.",
    "07.5": "A static function can be called without an instance, but it needs an object parameter to access non-static state.",
    "07.6": "Internal linkage prevents other translation units from naming that entity; unnamed namespaces are the common C++ alternative.",
    "07.7": "The object is initialized when first requested rather than during cross-file static initialization, reducing initialization-order hazards.",
    "07.8": "Explicit conversions remain available at the call site, so intentional conversion is possible without silently changing overload selection.",
    "07.9": "Direct-list and direct initialization can use an explicit constructor; copy-initialization cannot use it as an implicit conversion.",
    "07.10": "Friendship grants access but does not make the function a member; it still has ordinary non-member calling and overload behavior.",
    "07.11": "If another class needs access, it must receive its own explicit friendship grant from the class that owns the private data.",
    "07.12": "Because ADL finds the function through its argument types, the hidden friend is available to relevant calls without broad namespace visibility.",
    "08.1": "These terms answer different questions: visibility, storage availability, valid object existence, and who must release a resource.",
    "08.2": "Dynamic storage is commonly managed through RAII owners; choosing a duration does not by itself define who owns the resource.",
    "08.3": "Name visibility and object lifetime are independent, which is why a pointer can outlive the local name but still risk leaking its allocation.",
    "08.4": "Destroying the automatic `unique_ptr` releases its dynamically stored pointee, linking two objects with different storage durations.",
    "08.5": "Pair `new` with `delete` and `new[]` with `delete[]`; prefer standard containers and smart pointers to manage these pairs automatically.",
    "08.6": "A borrowed handle is valid only while its owner and the referenced region remain alive and uninvalidated.",
    "08.7": "Returning the local object's address or reference does not extend its lifetime; return by value or return a handle to longer-lived storage.",
    "08.8": "The end of the full expression is typically the semicolon, but binding and language-specific lifetime rules can extend selected temporaries.",
    "08.9": "Lifetime extension is not transitive through a function return or another reference, so inspect where the temporary is first bound.",
    "08.10": "Check the exact operation's invalidation guarantees in the container requirements; do not infer them from pointer stability alone.",
    "08.11": "Asynchronous work needs an explicit lifetime policy, such as owning a value or sharing ownership for the duration of the task.",
    "08.12": "Make ownership visible in interfaces so reviewers can identify who keeps an object alive and who is responsible for cleanup.",
    "09.1": "The deduced type is fixed at compile time and can be inspected by the compiler; `auto` does not add runtime type discovery.",
    "09.2": "Deduction follows template-like rules; write the desired reference and cv-qualification explicitly when copies or mutation matter.",
    "09.3": "The first form uses direct-list initialization of one element, while the equals form deduces an initializer-list type.",
    "09.4": "These tools are most valuable in generic code where spelling the exact dependent type would be brittle or difficult.",
    "09.5": "Prefer references for large elements or mutation; use a value when an independent copy is intentional and affordable.",
    "09.6": "An index is appropriate when it is part of the logic, but otherwise range-for avoids manual bounds and indexing errors.",
    "09.7": "Binding by value copies the decomposed elements; reference-qualified bindings preserve access to the original object.",
    "09.8": "A closure does not automatically extend the lifetime of objects captured by reference or of an object reached through `this`.",
    "09.9": "Standard algorithms separate the operation from traversal details and often work consistently across different iterator-based containers.",
    "09.10": "A view pipeline may defer work until iteration, so both the source range and any referenced state must still be valid then.",
    "09.11": "`nullptr` converts to pointer types but not integer types, making overloaded calls clearer and safer than using `0` or `NULL`.",
    "09.12": "Enumerators are qualified, for example `Color::Red`, and conversion requires an explicit cast when integer representation is intended.",
    "09.13": "`constinit` addresses initialization timing, not immutability; a `constinit` object may still be mutable after startup.",
    "09.14": "Use conditional `noexcept` where appropriate for move operations, and ensure the promise reflects every operation they perform.",
    "09.15": "`span` and `string_view` are non-owning views; `optional` and `variant` store their contained value directly.",
    "09.16": "`override` catches signature mismatches, `= default` requests generated behavior, and `= delete` rejects selected operations at compile time.",
    "10.1": "The standard defines portable language and library contracts while leaving many platform and implementation details to toolchains.",
    "10.2": "Check both compiler and standard-library feature support on the actual target toolchain, especially for embedded platforms.",
    "10.3": "C++03 primarily clarified and corrected the original language and library rather than introducing the scale of changes seen in later standards.",
    "10.4": "C++11 changed common design through move-aware value semantics, library ownership types, and standardized concurrency primitives.",
    "10.5": "C++14 refined C++11 features and added conveniences without replacing the overall language model.",
    "10.6": "C++17 improved compile-time branching and deduction while adding widely used library vocabulary types and filesystem support.",
    "10.7": "Feature availability varies by compiler and library version, so selecting the language mode alone does not prove support.",
    "10.8": "Validate each C++23 facility against the exact compiler, standard library, and target platform used by the project.",
    "10.9": "Draft wording and feature sets can change before publication, and early implementations may be experimental or incomplete.",
    "10.10": "A feature-test macro provides a targeted compile-time capability check that is usually more reliable than compiler-version guesses.",
    "10.11": "A source-compatible update may still require rebuilding all binaries if object layout, calling convention, or library ABI changes.",
    "10.12": "Record the chosen baseline in build configuration and CI so developers and release builds use consistent language and library modes.",
    "11.1": "A template is instantiated for supplied arguments, allowing one definition to express operations over multiple compatible types.",
    "11.2": "Non-type arguments can represent compile-time values such as array extents, while template-template parameters accept template families.",
    "11.3": "Instantiation makes the specialization available to the compiler; distinct argument sets can increase generated code and build work.",
    "11.4": "Requirements are determined by operations actually instantiated, so a type may work for one algorithm path and fail for another.",
    "11.5": "A visible definition lets each using translation unit generate the required specialization; explicit instantiation is a controlled alternative.",
    "11.6": "Partial specialization is useful for type traits and class behavior selected by a pattern of template arguments.",
    "11.7": "Constrained overloads are generally clearer for function selection; a helper class enables specialization when structural customization is needed.",
    "11.8": "Fold expressions provide concise reductions over parameter packs, but the operator's identity and evaluation order still matter.",
    "11.9": "SFINAE applies only in specified substitution contexts; failures elsewhere remain hard errors and can produce difficult diagnostics.",
    "11.10": "Concepts name requirements and can constrain overloads directly, making generic interfaces easier to read and diagnose.",
    "11.11": "Forwarding-reference deduction collapses references, and `std::forward<T>` restores the caller's original value category.",
    "11.12": "The discarded branch can contain operations invalid for other types, provided it is dependent and the selected branch is valid.",
    "11.13": "Static polymorphism can avoid virtual dispatch but requires types at compile time; runtime polymorphism supports substitution behind a stable interface.",
    "11.14": "CRTP behavior is resolved using the derived type at compile time, but it does not provide runtime substitution by itself.",
    "11.15": "Constrain templates and keep diagnostics understandable; use a non-template interface when genericity provides no meaningful benefit.",
    "12.1": "Iterators and algorithms decouple traversal from storage, allowing the same algorithm to operate on multiple compatible containers.",
    "12.2": "Contiguous layout also supports interoperability with C APIs and efficient bulk access; account for reallocation invalidation when appending.",
    "12.3": "`std::list` does not provide constant-time random access and often performs poorly for traversal due to per-node allocation and cache misses.",
    "12.4": "Choose ordered lookup when ordering or predictable logarithmic bounds matter, and hashing when average lookup speed suits the workload.",
    "12.5": "Complexity describes growth with input size, not fixed latency; allocation, cache behavior, and worst-case guarantees can matter in practice.",
    "12.6": "Amortized bounds apply over a sequence of operations and do not promise that every individual append is constant time.",
    "12.7": "Calling `reserve` can reduce reallocations when the expected element count is known, but it does not construct elements.",
    "12.8": "After an invalidating operation, previously saved iterators, pointers, and references must not be used unless the specific guarantee preserves them.",
    "12.9": "Unordered-container rehash changes bucket organization; reacquire iterators after rehash even when element references remain stable.",
    "12.10": "Algorithms require particular iterator capabilities, so matching the category is necessary for both correctness and complexity.",
    "12.11": "`list::sort` can relink nodes without requiring random access, preserving the list's iterator model.",
    "12.12": "The erase-remove idiom applies to sequence containers; associative containers generally erase by key or iterator directly.",
    "12.13": "Prefer the clearest construction expression and measure performance when it matters; `emplace_back` is not automatically faster.",
    "12.14": "Violating equal-keys-equal-hash breaks lookup assumptions and can make equivalent keys unreachable in an unordered container.",
    "12.15": "A lazy view may observe later changes to its source, so avoid retaining it beyond the source lifetime or across invalidation.",
    "12.16": "For integer input and a floating result, use a floating initial value such as `0.0`; the accumulator type controls intermediate arithmetic.",
    "12.17": "Adapters expose restricted operations suited to a policy; use a different underlying container only when its guarantees are needed.",
    "12.18": "Bound memory and execution time explicitly, and verify allocator and library behavior for the exact embedded toolchain and runtime context.",
}


def main() -> int:
    source = read_deck_document(SOURCE_PATH)
    cards = source["cards"]
    if not isinstance(cards, list) or len(cards) != 171:
        raise ValueError("Expected the original deck to contain exactly 171 cards")

    missing_details = {str(card["id"]) for card in cards} - DETAILS.keys()
    extra_details = DETAILS.keys() - {str(card["id"]) for card in cards}
    if missing_details or extra_details:
        raise ValueError(
            f"Answer-detail map mismatch; missing={sorted(missing_details)}, "
            f"extra={sorted(extra_details)}"
        )

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for card in cards:
        grouped[str(card["topic"])].append(card)
    if len(grouped) != len(TOPIC_SLUGS):
        raise ValueError(f"Expected {len(TOPIC_SLUGS)} topics, found {len(grouped)}")

    written = 0
    for topic, topic_cards in grouped.items():
        section = str(topic_cards[0]["id"]).split(".", 1)[0]
        slug = TOPIC_SLUGS[section]
        deck_id = f"cpp-study-{section}-{slug}"
        deck = {
            "format_version": source["format_version"],
            "id": deck_id,
            "title": f"C++ Study: {topic}",
            "description": f"Focused C++ study cards covering {topic}.",
            "study_settings": copy.deepcopy(source["study_settings"]),
            "cards": [],
            "assets": {},
        }
        for original_card in topic_cards:
            card = copy.deepcopy(original_card)
            card["answer"] = (
                f"{card['answer']}\n\n**More detail:** {DETAILS[str(card['id'])]}"
            )
            deck["cards"].append(card)

        filename = f"{deck_id}.deck.yaml"
        write_deck_document(PROJECT_ROOT / "decks" / filename, deck)
        written += len(topic_cards)
        print(f"Wrote {filename}: {len(topic_cards)} cards")

    if written != len(cards):
        raise ValueError(f"Wrote {written} cards; expected {len(cards)}")
    print(f"Created {len(grouped)} topic decks containing {written} cards.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())