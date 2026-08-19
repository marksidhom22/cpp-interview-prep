# C++ Namespaces, Function Overloading, and Operator Overloading

These topics share one central idea: C++ lets a codebase reuse readable names while the compiler applies scope, lookup, and overload-resolution rules to determine the intended declaration.

---

## Part I - Five-Minute Interview Review

### Mandatory namespace rules

```cpp
namespace motor {
    void start();
}

namespace camera {
    void start();
}

motor::start();
camera::start();
```

- Namespaces prevent collisions and organize APIs. See [Namespace fundamentals](#1-namespace-fundamentals).
- Prefer qualified names or targeted using-declarations; avoid `using namespace ...` in headers. See [Using declarations and directives](#4-using-declarations-and-directives).
- An unnamed namespace gives names internal linkage within one translation unit. See [Unnamed namespaces](#6-unnamed-namespaces-and-internal-linkage).
- Argument-dependent lookup can find functions in the namespaces associated with argument types. See [Argument-dependent lookup](#7-argument-dependent-lookup-adl).

### Mandatory overload rules

```cpp
void print(int);
void print(double);
void print(const std::string&);
```

- Functions may share a name when their parameter-type lists differ. See [Function overloading](#8-function-overloading).
- Return type alone cannot distinguish overloads. See [What does not create a distinct overload](#9-what-does-not-create-a-distinct-overload).
- The compiler builds candidates, rejects non-viable functions, ranks conversions, and selects one unique best match. See [Overload resolution](#10-overload-resolution).
- Exact matches beat promotions; promotions beat general standard conversions; user-defined conversions rank below standard conversions. See [Conversion ranking](#11-conversion-ranking).
- Default arguments do not create distinct overloads and can introduce ambiguity. See [Default arguments and ambiguity](#12-default-arguments-and-ambiguity).
- Derived-class declarations can hide all base overloads of the same name; use a using-declaration to restore them. See [Overload hiding in inheritance](#14-overload-hiding-in-inheritance).

### Mandatory operator-overload rules

```cpp
Point operator+(const Point& lhs, const Point& rhs);
```

- `operator` is a C++ keyword used to define behavior for existing operators on user-defined types. See [Operator-overload fundamentals](#16-operator-overload-fundamentals).
- You cannot invent new operators or change precedence, associativity, or operand count.
- At least one operand must normally be a class or enumeration type.
- Return type alone still cannot distinguish operator overloads.
- Use operators only when their meaning is natural and unsurprising. See [Operator-design guidelines](#22-operator-design-guidelines).

### Five interview checks

1. **Why avoid `using namespace std;` in a header?** It imports names into every including file and can create collisions or changed overload sets.
2. **Can `int f()` and `double f()` coexist?** No; return type is not used to select an overload.
3. **Which wins for a `short`: `f(int)` or `f(double)`?** `f(int)`, because integral promotion is better than general conversion.
4. **What does `object[index]` call?** `object.operator[](index)` for a member overload.
5. **Can operator overloading change `+` precedence?** No.

---

## Part II - Detailed Reference

## 1. Namespace fundamentals

Namespaces create named scopes:

```cpp
namespace vehicle {
    class Controller {};
    void initialize();
}
```

Use the scope-resolution operator:

```cpp
vehicle::Controller controller;
vehicle::initialize();
```

Two namespaces may contain identical unqualified names:

```cpp
namespace can_bus {
    void send();
}

namespace ethernet {
    void send();
}
```

Qualified calls are unambiguous:

```cpp
can_bus::send();
ethernet::send();
```

### Reopening a namespace

A namespace can be defined in multiple places:

```cpp
namespace vehicle {
    class Controller;
}

namespace vehicle {
    void start(Controller&);
}
```

This supports declaring related API components across headers and source files.

### Namespaces do not allocate objects

A namespace is a compile-time naming scope, not an object and not a class. It has no instances or `this` pointer.

### Interview question

**Question:** What problem do namespaces solve?

**Answer:** They organize names and prevent collisions between independently written components without requiring object instances.

---

## 2. Nested namespaces

Traditional syntax:

```cpp
namespace company {
namespace robotics {
namespace sensors {
    class Imu {};
}
}
}
```

C++17 compact syntax:

```cpp
namespace company::robotics::sensors {
    class Imu {};
}
```

Usage:

```cpp
company::robotics::sensors::Imu imu;
```

Avoid excessively deep nesting when it makes every declaration hard to read. Namespace structure should reflect stable ownership or domain boundaries, not every directory.

### Interview question

**Question:** Does `namespace a::b` create a different concept from nested `namespace a { namespace b { ... } }`?

**Answer:** No. It is compact syntax for the same nested namespace structure.

---

## 3. Namespace aliases and inline namespaces

### Alias

```cpp
namespace autonomy = company::robotics::autonomy;

autonomy::Planner planner;
```

An alias shortens a long name without importing all of its members into the current scope.

### Inline namespace

```cpp
namespace protocol {
inline namespace v2 {
    class Packet {};
}
}
```

Members of `v2` can be referred to as:

```cpp
protocol::Packet
```

while the version remains expressible as `protocol::v2::Packet`. Inline namespaces are useful for ABI/versioning schemes, though real ABI design requires more than syntax.

### Interview question

**Question:** Why might a library use an inline namespace?

**Answer:** To expose one version as the default while retaining version information in symbol identity and allowing qualified access to versions.

---

## 4. Using declarations and directives

### Using-declaration

```cpp
using std::string;

string name;
```

It introduces a selected name.

### Using-directive

```cpp
using namespace std;
```

It makes all namespace members available for unqualified lookup in that scope.

### Header rule

Do not place broad using-directives in headers:

```cpp
// public_header.hpp
using namespace std; // avoid
```

Every source file including the header inherits the directive, which can cause:

- Name collisions.
- Ambiguous overloads.
- Behavior changes when a library adds a new name.
- Confusing diagnostics.

A local using-declaration inside a function is often fine:

```cpp
void f() {
    using std::swap;
    swap(a, b);
}
```

That pattern deliberately supports ADL.

### Interview question

**Question:** Is `using std::string;` the same as `using namespace std;`?

**Answer:** No. The first introduces one selected name; the second affects unqualified lookup for every member of the namespace.

---

## 5. Qualified lookup and unqualified lookup

Qualified lookup specifies a scope:

```cpp
motor::start();
```

Unqualified lookup searches the relevant lexical scopes and may also involve ADL for function calls:

```cpp
start(device);
```

Local declarations can hide outer declarations:

```cpp
void process(double);

void f() {
    void process(int);
    process(1.5); // local declaration participates; outer process is hidden
}
```

Name lookup happens before full overload resolution. A function that is not found cannot be selected even if its parameter types would be perfect.

### Interview question

**Question:** What is the difference between name lookup and overload resolution?

**Answer:** Lookup determines which declarations are considered; overload resolution chooses the best viable function among the declarations found.

---

## 6. Unnamed namespaces and internal linkage

```cpp
namespace {
    void helper() {}
    int local_counter{};
}
```

Names in an unnamed namespace have internal linkage: each translation unit gets its own distinct entities.

This is useful in `.cpp` files for implementation details that should not create externally visible symbols.

Older C-style code often uses:

```cpp
static void helper();
```

at namespace scope for internal linkage. Unnamed namespaces generalize cleanly to types, variables, and functions.

### Header warning

An unnamed namespace in a header creates a separate entity in every translation unit that includes it. That may be intended for certain constants/templates, but often wastes space or creates surprising identity differences.

### Interview question

**Question:** What is the purpose of an unnamed namespace in a `.cpp` file?

**Answer:** It hides implementation names within that translation unit by giving them internal linkage.

---

## 7. Argument-dependent lookup (ADL)

ADL adds namespaces and classes associated with function arguments to function lookup.

```cpp
namespace geometry {
    struct Point {
        int x{};
        int y{};
    };

    bool equal(const Point& a, const Point& b) {
        return a.x == b.x && a.y == b.y;
    }
}

geometry::Point a;
geometry::Point b;

bool same = equal(a, b); // ADL finds geometry::equal
```

No `using geometry::equal` is required because the argument type is associated with `geometry`.

### The `swap` pattern

```cpp
using std::swap;
swap(a, b);
```

Ordinary lookup provides `std::swap`; ADL can find a more specialized `swap` in the type's namespace.

### Tradeoff

ADL enables natural non-member APIs and operators, but it makes lookup less obvious. Place non-member functions intended as part of a type's interface in the same namespace as the type.

### Interview question

**Question:** How can an unqualified `swap(a, b)` find a custom swap function?

**Answer:** A using-declaration supplies `std::swap`, while ADL searches namespaces associated with the argument types for a better overload.

---

## 8. Function overloading

Overloading lets functions share a name when their parameter declarations distinguish them:

```cpp
void print(int value);
void print(double value);
void print(const std::string& value);
```

Calls:

```cpp
print(10);          // print(int)
print(3.14);        // print(double)
print(std::string{"status"}); // string overload
```

Overloads should represent one conceptual operation across different types or parameter forms. Unrelated behaviors under one name make code harder to understand.

### Member-function overloads

Member functions can differ by:

- Parameter types/count.
- Member-function cv-qualification.
- Ref-qualification.

```cpp
class Buffer {
public:
    int& data() &;
    const int& data() const &;
    int data() &&;
};
```

### Interview question

**Question:** What is function overloading?

**Answer:** Multiple declarations with the same name in one overload set, distinguished by parameter types and eligible member qualifiers, with the compiler selecting the best match.

---

## 9. What does not create a distinct overload

### Return type alone

```cpp
int read();
double read(); // error
```

A call may ignore the result:

```cpp
read();
```

so there is no return context that could choose uniquely.

### Top-level const on by-value parameters

```cpp
void f(int value);
void f(const int value); // same function type
```

The parameter is a local copy. Its internal mutability is not part of the caller-facing overload.

Low-level const does distinguish pointer/reference interfaces:

```cpp
void inspect(Device*);
void inspect(const Device*);
```

### Parameter names

```cpp
void set(int left);
void set(int right); // same declaration shape
```

Names are not part of a function signature.

### Default arguments

```cpp
void log(int level);
void log(int level = 1); // redeclaration, not an overload
```

### `noexcept`

Functions cannot generally be overloaded solely on different exception specifications.

### Interview question

**Question:** Why do `void f(int)` and `void f(const int)` conflict?

**Answer:** Top-level const on a by-value parameter is not part of the function type used for overloading.

---

## 10. Overload resolution

For a call, the compiler conceptually:

1. Performs name lookup to build candidate functions.
2. Applies template argument deduction where relevant.
3. Removes candidates whose arguments cannot form valid calls.
4. Ranks the conversions for viable candidates.
5. Selects one unique best viable function.
6. Reports ambiguity if no unique best exists.

Example:

```cpp
void process(int);
void process(double);

process(10);   // exact match to int
process(10.0); // exact match to double
```

### Ambiguity

```cpp
void process(long);
void process(double);

process(10); // potentially ambiguous: two standard conversions
```

Neither candidate is strictly better in the required way.

### Context can matter for templates and conversions

Overload resolution includes detailed rules for reference binding, qualification conversions, user-defined conversions, templates, initializer lists, and rewritten comparison candidates in modern standards.

For interviews, explain the ranking model correctly before diving into rare tie-breakers.

### Interview question

**Question:** What does "best viable function" mean?

**Answer:** A callable candidate whose required conversions rank at least as well as every competitor's and strictly better where the language rules require a unique winner.

---

## 11. Conversion ranking

A simplified useful order is:

```text
Exact match
    better than
Promotion
    better than
Other standard conversion
    better than
User-defined conversion
    better than
Ellipsis
```

### Exact match

```cpp
void f(int);
f(10);
```

Qualification and certain reference adjustments are included in exact-match categories.

### Promotion

```cpp
void f(int);
short value = 1;
f(value); // short promotes to int
```

### Standard conversion

```cpp
void f(double);
int value = 1;
f(value); // int converts to double
```

### User-defined conversion

```cpp
class Distance {
public:
    Distance(int);
};

void f(Distance);
f(10);
```

### Avoid relying on intricate overload sets

Overloads with many integral types, implicit constructors, and templates can become ambiguous or platform-dependent because fundamental type widths differ.

### Interview question

**Question:** Given `f(int)` and `f(double)`, which handles a `short`?

**Answer:** `f(int)`, because promotion from `short` to `int` ranks better than conversion to `double`.

---

## 12. Default arguments and ambiguity

```cpp
void log(int level);
void log(int level, const std::string& message = {});
```

A call with one argument:

```cpp
log(1);
```

is ambiguous because both overloads are viable with equally good conversion of the supplied argument.

Default arguments are substituted at the call site and are not part of the function type.

### Virtual-function warning

Default arguments are selected from the static type, while virtual dispatch selects the function body dynamically:

```cpp
class Base {
public:
    virtual void f(int value = 1);
};

class Derived : public Base {
public:
    void f(int value = 2) override;
};
```

Calling through `Base&` uses default `1` but may dispatch to `Derived::f`. Avoid differing default arguments on virtual overrides.

### Interview question

**Question:** Can default arguments make an otherwise reasonable overload set ambiguous?

**Answer:** Yes. They change which calls are viable without creating distinct signatures.

---

## 13. References, const, and overloads

```cpp
void inspect(Device&);
void inspect(const Device&);
```

A mutable `Device` prefers `Device&`; a const `Device` can use only `const Device&`.

Rvalue-reference overloads distinguish value categories:

```cpp
void submit(const Packet& packet); // reads lvalues and can bind rvalues
void submit(Packet&& packet);      // may consume rvalues
```

### Dangerous combinations

Overloading by value and const reference can be ambiguous:

```cpp
void process(Packet);
void process(const Packet&);
```

For many arguments both are exact-enough matches, and the compiler cannot infer whether the caller intends a copy or borrow.

Choose the semantic contract rather than offering every possible form.

### Null pointer constants

Overloads such as:

```cpp
void f(int);
void f(char*);
```

make `f(0)` favor the integer overload. Use `nullptr` for pointer intent:

```cpp
f(nullptr);
```

### Interview question

**Question:** Why is `nullptr` better than `0` or `NULL` in overload resolution?

**Answer:** `nullptr` has `std::nullptr_t`, which converts to pointer types without also behaving as an integer argument.

---

## 14. Overload hiding in inheritance

A derived declaration with a name hides base declarations of the same name:

```cpp
class Base {
public:
    void configure(int);
    void configure(double);
};

class Derived : public Base {
public:
    void configure(const std::string&);
};

Derived d;
// d.configure(10); // base overloads hidden
```

Restore the overload set:

```cpp
class Derived : public Base {
public:
    using Base::configure;
    void configure(const std::string&);
};
```

Now all three overloads participate.

This is name hiding, not overriding. Overriding specifically concerns virtual functions with matching signatures.

### Interview question

**Question:** Why can adding `Derived::f(std::string)` make `Base::f(int)` unavailable through a `Derived` object?

**Answer:** Name lookup finds the derived declaration and hides the base overload set unless a using-declaration reintroduces it.

---

## 15. Templates and overload sets

Templates may coexist with non-template overloads:

```cpp
void print(int);

template<class T>
void print(const T&);
```

For an `int`, the non-template exact match is generally preferred over an equally good template specialization.

Constraints improve overload intent:

```cpp
template<std::integral T>
void encode(T value);

template<std::floating_point T>
void encode(T value);
```

### Universal/forwarding-reference trap

A broad forwarding-reference overload can capture calls intended for other overloads:

```cpp
template<class T>
void log(T&& value);
```

It may be a better match than a `const std::string&` overload for some arguments. Constrain generic overloads and test the complete set.

### Interview question

**Question:** If a non-template and a template are equally good matches, which is normally preferred?

**Answer:** The non-template function, after conversion ranking establishes an otherwise equivalent match.

---

## 16. Operator-overload fundamentals

The keyword `operator` forms special function names:

```cpp
class Buffer {
public:
    int& operator[](std::size_t index);
};
```

This expression:

```cpp
buffer[3]
```

corresponds to:

```cpp
buffer.operator[](3)
```

A binary non-member operator:

```cpp
Point operator+(const Point& left, const Point& right);
```

allows:

```cpp
Point result = a + b;
```

### Fixed language properties

Operator overloading cannot:

- Create a new symbol such as `**`.
- Change precedence.
- Change associativity.
- Change the number of operands.
- Redefine behavior when every operand is a built-in type.

At least one operand normally must be a user-defined class or enum type.

### Operators that cannot be overloaded

Important examples include:

```text
.
.*
::
?:
sizeof
typeid
alignof
```

### Interview question

**Question:** What does operator overloading change?

**Answer:** It supplies function behavior for an existing operator involving a user-defined type; it does not change the operator's grammar or precedence.

---

## 17. Member versus non-member operators

### Must be members

Operators including assignment, subscript, call, and member access arrow are defined as members:

```cpp
T& operator=(const T&);
Element& operator[](std::size_t);
Result operator()(Arguments...);
T* operator->();
```

### Symmetric binary operators

Prefer a non-member for symmetric operations so conversions can apply to both operands:

```cpp
class Distance {
public:
    explicit Distance(int meters) : meters_{meters} {}

    Distance& operator+=(const Distance& other) {
        meters_ += other.meters_;
        return *this;
    }

private:
    int meters_;

    friend Distance operator+(Distance left, const Distance& right) {
        left += right;
        return left;
    }
};
```

Taking the left operand by value reuses `+=` and permits efficient move/copy behavior.

### Stream insertion

```cpp
std::ostream& operator<<(std::ostream& out, const Device& device);
```

It must be a non-member because the left operand is an `std::ostream`, which you do not modify by adding a member.

### Interview question

**Question:** Why is a symmetric `operator+` often a non-member?

**Answer:** It treats both operands symmetrically and allows conversions on the left operand as well as the right.

---

## 18. Canonical operator relationships

Related operators should agree.

### Arithmetic

Implement compound assignment first:

```cpp
Vector& operator+=(const Vector& rhs);
```

Then derive binary addition:

```cpp
Vector operator+(Vector lhs, const Vector& rhs) {
    lhs += rhs;
    return lhs;
}
```

### Increment

```cpp
Counter& operator++();   // prefix
Counter operator++(int); // postfix; dummy int distinguishes syntax
```

Postfix normally returns the old value and may cost a copy.

### Equality and ordering

Modern C++ can synthesize comparisons:

```cpp
struct Version {
    int major{};
    int minor{};

    auto operator<=>(const Version&) const = default;
};
```

Use only when memberwise ordering matches domain meaning.

### Subscript const pair

```cpp
T& operator[](std::size_t);
const T& operator[](std::size_t) const;
```

### Interview question

**Question:** Why is postfix increment declared with an unused `int` parameter?

**Answer:** The dummy parameter distinguishes `operator++(int)` for postfix syntax from `operator++()` for prefix syntax.

---

## 19. Conversion operators

A conversion operator converts an object to another type:

```cpp
class File {
public:
    explicit operator bool() const noexcept {
        return valid_;
    }

private:
    bool valid_{};
};
```

Usage:

```cpp
if (file) {
    // valid
}
```

`explicit operator bool` works in contextual Boolean expressions while preventing many unintended arithmetic or overload conversions.

Implicit conversion operators can create surprising overload resolution and should be used sparingly.

### Interview question

**Question:** Why is `operator bool` commonly explicit?

**Answer:** It supports natural condition checks while preventing broad implicit conversion of the object to numeric or unrelated types.

---

## 20. Operator pitfalls

### Surprising meaning

Do not make `operator+` mutate its left operand or perform unrelated I/O.

### Incorrect return type

Assignment and compound assignment conventionally return `T&`. Prefix increment normally returns `T&`; postfix returns the old value.

### Missing const

Read-only operators should be const:

```cpp
bool operator==(const T& other) const;
```

### Broken laws

If `a == b`, callers expect consistent hashing and ordering relationships. If `<` is used for ordered containers, it must provide strict weak ordering.

### Short-circuit assumptions

Overloaded `operator&&` and `operator||` are function calls and historically do not behave exactly like built-in short-circuit operators in all relevant semantic respects. Avoid overloading them for ordinary domain types.

### Address-of and comma

Overloading operators with fundamental language roles can make generic code surprising.

### Interview question

**Question:** What makes an operator overload good?

**Answer:** It preserves the conventional meaning and algebraic expectations of the operator, with clear complexity and no surprising side effects.

---

## 21. Namespaces and operators together

Place a non-member operator in the same namespace as its type:

```cpp
namespace geometry {
    struct Point {
        int x{};
        int y{};
    };

    Point operator+(Point left, const Point& right) {
        left.x += right.x;
        left.y += right.y;
        return left;
    }
}
```

Then:

```cpp
geometry::Point a;
geometry::Point b;
auto c = a + b;
```

ADL finds `geometry::operator+`.

Do not add overloads for your own types to namespace `std` except where the standard explicitly permits a specialization. Adding ordinary functions to `std` is undefined behavior.

### Interview question

**Question:** Where should a non-member operator for `my::Type` normally be declared?

**Answer:** In namespace `my`, so it is part of the type's interface and can be found by ADL.

---

## 22. Operator-design guidelines

Before adding an overload, ask:

1. Does the operator have an obvious conventional meaning for this type?
2. Will its complexity surprise users?
3. Should it be a member or symmetric non-member?
4. Does it preserve const correctness?
5. Are related operators consistent?
6. Would a named function be clearer?
7. Can implicit conversions create ambiguity?
8. Does it preserve required ordering or equality laws?

Named functions are better when multiple interpretations are plausible:

```cpp
matrix.concatenate(other);
matrix.multiply(other);
```

instead of assigning an arbitrary meaning to an operator.

### Interview question

**Question:** When should you prefer a named function over an operator overload?

**Answer:** When the operation is not conventional, has surprising cost or side effects, or has multiple plausible meanings.

---

## 23. Embedded and systems considerations

Namespaces are zero-runtime-cost organization. Overload and operator resolution occurs at compile time, though selected functions may use dynamic behavior internally.

Review:

- Code-size growth from many template/operator instantiations.
- Implicit conversions that hide allocation.
- Operator implementations that throw or block.
- Ambiguous integral overloads across different target widths.
- Unnamed namespace objects that duplicate storage per translation unit.
- ABI effects from inline namespace versioning.
- Debug readability of highly generic overload sets.

Strong types can improve embedded correctness:

```cpp
struct Millivolts {
    int value;
};

struct Milliamps {
    int value;
};
```

Overloads and explicit constructors prevent mixing units accidentally without runtime overhead.

### Interview question

**Question:** Does function overloading add runtime dispatch overhead?

**Answer:** Ordinary overload resolution is compile-time. It is distinct from virtual-function dynamic dispatch.

---

## 24. Common mistakes

- `using namespace std;` in public headers.
- Expecting return type to choose an overload.
- Treating top-level const by-value parameters as distinct overloads.
- Creating ambiguous integral overload sets.
- Mixing default arguments with overlapping overloads.
- Forgetting that derived declarations hide base overloads.
- Confusing overloading with virtual overriding.
- Relying on implicit converting constructors.
- Defining symmetric binary operators only as members.
- Placing a type's non-member operator in an unrelated namespace.
- Giving operators surprising meaning.
- Assuming overloaded operators can change precedence.

---

## 25. Final design checklist

You should be able to explain:

- Namespace scope and qualification.
- Reopening, nesting, aliases, and inline namespaces.
- Using-declarations versus using-directives.
- Unnamed namespaces and internal linkage.
- Name lookup versus overload resolution.
- ADL and the custom-swap pattern.
- What forms a valid overload set.
- Why return type, parameter names, and top-level const do not distinguish overloads.
- Conversion ranking and ambiguity.
- Default-argument hazards.
- Const/ref overloads and `nullptr`.
- Base overload hiding.
- Templates in overload sets.
- Operator limitations.
- Member versus non-member operator design.
- Canonical arithmetic, increment, comparison, and subscript operators.
- Explicit conversion operators.
- Strong-type advantages in embedded code.
