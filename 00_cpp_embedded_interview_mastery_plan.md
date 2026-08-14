# C++ / OOP / Problem-Solving Interview Mastery Plan

## Goal

Prepare for C++ and problem-solving interviews for embedded systems, systems software, robotics, and autonomous-vehicle teams at companies such as:

- Google
- Amazon
- Meta
- Zoox
- Tesla
- Waymo

## Current Background

You already have a strong base:

- Embedded systems experience
- Strong C programming
- Basic C++
- Familiarity with object-oriented programming
- Familiarity with smart pointers
- Some familiarity with RAII
- Strong understanding of the differences between C and C++
- Strong understanding of compilers and the code-building process

Because of this background, the plan should **not** treat you as a C++ beginner.

Your transition is:

```text
Strong C / Embedded Engineer
        ↓
Modern C++ Systems Programmer
        ↓
Strong Data Structures & Algorithms Problem Solver
        ↓
Strong C++ / Embedded / Systems Interview Candidate
        ↓
Google / Amazon / Meta / Zoox / Tesla / Waymo
```

---

# 1. Overall Strategy

Your preparation should focus on five major areas:

1. Modern C++
2. Data structures and algorithms
3. Object-oriented programming and software design
4. Operating systems, concurrency, and embedded systems
5. Embedded/autonomous-system design and debugging

Recommended time distribution:

| Area | Approximate Time |
|---|---:|
| Data structures & algorithms | 35% |
| Modern C++ | 25% |
| Embedded + OS + concurrency | 20% |
| OOP / design | 10% |
| System design + behavioral + applications | 10% |

A good overall preparation duration is approximately **20 weeks / 5 months**.

Recommended workload:

- 15–18 hours per week
- 2 hours on most weekdays
- 3–4 hours on weekend days

The goal is not merely to "know C++."

The goal is to be able to:

- Receive an unfamiliar coding problem
- Clarify requirements
- Develop a brute-force approach
- Derive an optimized approach
- Implement it cleanly in modern C++
- Explain time and space complexity
- Discuss memory ownership and lifetime
- Handle edge cases
- Debug your code
- Discuss concurrency implications
- Discuss embedded/real-time implications
- Design a larger system when asked

---

# 2. Phase 1 — Modern C++ Foundation

## Weeks 1–4

Because you already know C, skip beginner material such as:

- What a variable is
- Basic loops
- Basic functions
- Primitive data types
- Basic compiler concepts
- Basic preprocessing
- Basic pointers
- Basic build pipelines

Focus on the parts that distinguish effective modern C++ from C-style programming.

---

# Week 1 — C++ Object Model

## Topics

Master:

- References vs pointers
- `const`
- Const correctness
- Constructors
- Destructors
- Initialization lists
- Copy constructor
- Copy assignment
- Namespaces
- Function overloading
- Operator overloading
- `static`
- `explicit`
- `friend`
- Stack objects
- Heap objects
- Object lifetime
- Scope
- Temporary objects

Example:

```cpp
Foo a;
Foo b = a;
Foo c(a);
b = a;
```

Be able to explain exactly what happens in each statement.

Understand when the following execute:

- Default constructor
- Copy constructor
- Copy assignment operator
- Move constructor
- Move assignment operator
- Destructor

## Rule of Three

If a class manually manages a resource and defines one of:

- Destructor
- Copy constructor
- Copy assignment

it frequently needs all three.

## Rule of Five

Modern C++ adds:

- Move constructor
- Move assignment operator

## Rule of Zero

Prefer designing classes so that resource-owning standard-library types handle resource lifetime automatically.

This is usually the best design.

Example:

```cpp
class Buffer {
public:
    explicit Buffer(std::size_t size)
        : data_(std::make_unique<char[]>(size)),
          size_(size) {}

private:
    std::unique_ptr<char[]> data_;
    std::size_t size_;
};
```

The compiler-generated destructor is sufficient.

---

# Week 2 — RAII and Ownership

RAII is one of the most important C++ concepts for systems engineers.

RAII means:

> Resource Acquisition Is Initialization.

Resources are tied to object lifetime.

Resources can include:

- Heap memory
- File handles
- Mutex locks
- Sockets
- File descriptors
- Hardware handles
- Threads
- Database handles
- Device handles

## Smart Pointers

Master:

```cpp
std::unique_ptr
std::shared_ptr
std::weak_ptr
std::make_unique
std::make_shared
```

### `std::unique_ptr`

Represents exclusive ownership.

```cpp
auto sensor = std::make_unique<Sensor>();
```

Ownership can move:

```cpp
auto sensor2 = std::move(sensor);
```

Afterward:

```cpp
sensor == nullptr
```

typically holds.

Know why copying a `unique_ptr` is prohibited.

---

### `std::shared_ptr`

Represents shared ownership.

```cpp
auto sensor = std::make_shared<Sensor>();
```

Understand:

- Reference counting
- Ownership semantics
- Destruction behavior
- Runtime overhead
- Thread-safety limitations

Do not use `shared_ptr` simply because ownership is unclear.

Unclear ownership is often a design problem.

---

### `std::weak_ptr`

Understand why it exists.

Typical use:

```text
Object A owns Object B
Object B needs to refer back to Object A
```

If both use `shared_ptr`, you may create an ownership cycle.

A `weak_ptr` can break the cycle.

---

## RAII Beyond Memory

Example with a mutex:

Bad:

```cpp
mutex.lock();

do_work();

mutex.unlock();
```

Problems:

- Exceptions
- Early returns
- Forgotten unlock
- Future code changes

Better:

```cpp
std::lock_guard<std::mutex> lock(mutex);

do_work();
```

The mutex unlocks automatically when the guard leaves scope.

Other RAII examples:

```cpp
std::fstream
std::unique_lock
std::scoped_lock
std::jthread
std::unique_ptr
```

For embedded interviews, also understand situations where:

- Dynamic allocation is restricted
- Heap usage is prohibited
- Deterministic memory use matters
- Static allocation is preferred

---

# Week 3 — Move Semantics and Modern C++

Master:

```cpp
T&&
std::move
std::forward
```

Understand:

- lvalues
- rvalues
- lvalue references
- rvalue references
- move construction
- move assignment
- copying vs moving
- temporary objects
- perfect forwarding at a conceptual level
- return-value optimization
- copy elision

Classic interview question:

> What does `std::move()` do?

Good answer:

`std::move()` does not itself move an object. It performs a cast that allows the object to be treated as an rvalue so that move operations may be selected.

---

## Modern C++ Language Features

Study:

```cpp
auto
decltype
constexpr
consteval
noexcept
nullptr
enum class
using
range-based for
structured bindings
lambda expressions
```

Be comfortable with:

```cpp
for (const auto& item : items) {
    ...
}
```

and:

```cpp
auto [key, value] = pair;
```

and lambdas:

```cpp
auto compare = [](const Node& a, const Node& b) {
    return a.priority > b.priority;
};
```

Understand lambda captures:

```cpp
[]
[&]
[=]
[this]
[x]
[&x]
```

---

# Week 4 — STL Mastery

STL fluency is essential for C++ coding interviews.

## Containers

Know:

```cpp
std::vector
std::array
std::deque
std::list
std::string
std::stack
std::queue
std::priority_queue
std::set
std::unordered_set
std::map
std::unordered_map
```

You should know:

- Typical use case
- Time complexity
- Memory characteristics
- Iterator behavior

---

## Important Algorithms

Know:

```cpp
std::sort
std::stable_sort
std::lower_bound
std::upper_bound
std::binary_search
std::find
std::count
std::reverse
std::min_element
std::max_element
std::accumulate
```

You should be able to write custom comparators.

Example:

```cpp
std::sort(items.begin(), items.end(),
          [](const Item& a, const Item& b) {
              return a.priority < b.priority;
          });
```

---

## Complexity Knowledge

Know approximately:

```text
vector push_back       amortized O(1)
vector random access   O(1)
vector front insertion O(n)

list insertion         O(1), given iterator
list random access     O(n)

map lookup             O(log n)
unordered_map lookup   average O(1)

priority_queue push    O(log n)
priority_queue pop     O(log n)
priority_queue top     O(1)
```

---

## Important STL Interview Topics

Understand:

- Iterator invalidation
- `vector::size()`
- `vector::capacity()`
- Reallocation
- `reserve()`
- `resize()`
- Hash collisions
- Custom hashes
- Custom comparators
- `emplace`
- `emplace_back`
- `push_back`
- Copying vs moving elements

Example question:

> What happens when a vector runs out of capacity?

Typical answer:

It allocates a larger storage block and moves or copies elements into the new block, potentially invalidating pointers, references, and iterators to existing elements.

---

# 3. Phase 2 — Object-Oriented Programming and C++ Design

## Weeks 5–6

Do not spend excessive time memorizing design-pattern names.

Focus on good design decisions.

---

# OOP Fundamentals

Master:

- Encapsulation
- Abstraction
- Inheritance
- Polymorphism
- Composition

---

## Virtual Functions

Understand:

```cpp
class Device {
public:
    virtual ~Device() = default;
    virtual void start() = 0;
};
```

Know:

- Pure virtual functions
- Abstract base classes
- Dynamic dispatch
- Virtual tables conceptually
- Virtual destructors
- `override`
- `final`

---

## Important OOP Interview Topics

Understand:

- Object slicing
- Base vs derived destruction
- Interface design
- Composition vs inheritance
- Multiple inheritance basics
- Diamond inheritance
- Virtual inheritance conceptually

Example object slicing:

```cpp
Derived d;
Base b = d;
```

The derived part is sliced away.

---

# SOLID Principles

Understand the ideas behind:

## Single Responsibility Principle

A class should have one clear reason to change.

## Open/Closed Principle

Software entities should be open for extension but closed for unnecessary modification.

## Liskov Substitution Principle

Derived objects should behave correctly wherever the base type is expected.

## Interface Segregation Principle

Avoid forcing clients to depend on methods they do not use.

## Dependency Inversion Principle

High-level code should depend on abstractions rather than concrete implementations.

---

# Composition Over Inheritance

Prefer:

```text
VehicleController
    contains
SensorManager
Logger
SafetyMonitor
```

rather than forcing everything into a deep inheritance hierarchy.

For embedded systems, simpler dependency relationships are often easier to:

- Reason about
- Test
- Verify
- Profile
- Debug
- Certify

---

# Weeks 5–6 Project — Device Framework

Build a small device framework.

Example architecture:

```text
Device
 |
 +-- TemperatureSensor
 |
 +-- Camera
 |
 +-- IMU
```

Then add:

```text
SensorManager
Logger
ErrorHandler
CommunicationInterface
```

Use:

- Interfaces
- RAII
- `std::unique_ptr`
- Dependency injection
- Composition
- Callbacks
- Unit tests

Be prepared to explain:

- Why you chose inheritance
- Why you chose composition
- Who owns each object
- How object lifetimes are controlled
- How errors propagate
- How the design could become thread-safe
- How you would adapt it for an RTOS
- How you would avoid heap allocation if required

---

# 4. Phase 3 — Data Structures and Problem Solving

## Weeks 7–14

This becomes the largest portion of the interview preparation.

Do not optimize for the number of LeetCode problems solved.

Optimize for:

- Pattern recognition
- Correctness
- Speed
- Explanation
- Repetition
- Clean C++ implementation

A good target is roughly **150–200 carefully chosen problems**.

---

# Weeks 7–8 — Arrays, Strings, Hashing

Master:

- Arrays
- Strings
- Hash maps
- Hash sets
- Prefix sums
- Frequency tables

---

## Two Pointers

Typical structure:

```text
left →            ← right
```

Use for problems involving:

- Sorted arrays
- Pairs
- Removing duplicates
- Palindromes
- Partitioning

---

## Sliding Window

Typical structure:

```text
[L ---------------- R]
```

Use for:

- Longest substring
- Maximum/minimum subarray under constraints
- Frequency-based substring problems
- Fixed-size windows

---

## Prefix Sums

Typical idea:

```text
sum(l...r) = prefix[r] - prefix[l-1]
```

Useful for:

- Range sums
- Subarray conditions
- Counting problems

Target:

**25–30 problems**

---

# Week 9 — Linked Lists, Stacks, Queues

## Linked Lists

Master:

- Reverse linked list
- Find middle node
- Fast/slow pointers
- Detect cycle
- Merge sorted lists
- Remove Nth node
- Intersection of lists

---

## Stack Patterns

Study:

- Balanced parentheses
- Expression evaluation
- Monotonic stacks
- Next greater element
- Histogram problems

---

## Queue / Deque Patterns

Study:

- BFS
- Sliding-window maximum
- Producer/consumer concepts

Target:

**15–20 problems**

---

# Week 10 — Binary Search

Do not think of binary search merely as:

> Find X in a sorted array.

Master:

- Standard binary search
- Lower bound
- Upper bound
- First/last occurrence
- Rotated arrays
- Search in answer space
- Monotonic predicate search

Mental model:

```text
Can answer X work?

false false false false true true true
                        ^
                   boundary
```

Target:

**15 problems**

---

# Week 11 — Trees

Master:

- DFS
- BFS
- Preorder
- Inorder
- Postorder
- Binary search trees
- Level-order traversal
- Recursion
- Iterative traversal

Important problems:

- Tree height
- Tree diameter
- Lowest common ancestor
- Validate BST
- Serialize/deserialize
- Path sum
- Balanced tree
- Tree construction
- Kth smallest in BST

Target:

**20–25 problems**

---

# Week 12 — Graphs

Master:

- DFS
- BFS
- Graph representation
- Adjacency lists
- Cycle detection
- Topological sorting
- Union-Find / DSU
- Dijkstra's algorithm basics

Understand when a problem that appears unrelated is actually a graph problem.

Examples:

- Dependencies
- Course scheduling
- Connectivity
- Network propagation
- Island counting
- State-space exploration

Target:

**20–25 problems**

---

# Week 13 — Heaps, Greedy, Intervals

Master:

```cpp
std::priority_queue
```

Study problems involving:

- Top K elements
- K-way merge
- Median-like problems
- Scheduling
- Resource allocation
- Meeting rooms
- Interval merging
- Interval insertion

Target:

**15–20 problems**

---

# Week 14 — Backtracking and Dynamic Programming

You do not need competitive-programming-level DP.

Learn the basic model:

```text
State
  ↓
Choices
  ↓
Transition
  ↓
Base case
```

Then:

```text
Recursion
   ↓
Memoization
   ↓
Bottom-up DP
```

Study:

- Subsets
- Permutations
- Combinations
- Combination sum
- Knapsack basics
- Coin change
- Grid DP
- Longest increasing subsequence
- Basic string DP

Target:

**20–25 problems**

---

# 5. How to Practice Coding Problems

Do not use this process:

```text
Read problem
↓
Struggle for 90 minutes
↓
Read solution
↓
Move to next problem
```

Use:

```text
Read problem
    ↓
Clarify requirements
    ↓
Identify possible pattern
    ↓
Describe brute-force approach
    ↓
Analyze complexity
    ↓
Develop optimized approach
    ↓
Code
    ↓
Test manually
    ↓
Analyze complexity
    ↓
Review mistakes
    ↓
Repeat problem later
```

Initially give yourself approximately:

**30–40 minutes per interview-style problem.**

---

# Interview Communication

Practice speaking while solving.

Example:

> The brute-force approach compares every pair, which costs O(n²). I can eliminate the repeated search by storing previously seen values in an unordered_map. That gives average O(n) time at the cost of O(n) additional memory.

Practice explaining:

1. Assumptions
2. Brute force
3. Optimization
4. Data structure choice
5. Complexity
6. Edge cases
7. Testing

---

# 6. Phase 4 — Systems C++

## Weeks 15–16

This phase connects your C++ preparation with your systems background.

---

# Memory Model

Review:

```text
Text / Code
Read-only data
Initialized data
BSS
Heap
Stack
```

Master:

- Stack vs heap
- Static storage duration
- Automatic storage duration
- Dynamic storage duration
- Alignment
- Padding
- Fragmentation
- Dangling pointers
- Use-after-free
- Double-free
- Buffer overflow
- Undefined behavior
- Memory leaks
- Placement new

Example:

```cpp
struct Foo {
    char a;
    int b;
    char c;
};
```

Be able to explain why:

```text
sizeof(Foo)
```

may be larger than:

```text
1 + 4 + 1
```

because of alignment and padding.

---

# C++ Concurrency

This is extremely important for systems software interviews.

Master:

```cpp
std::thread
std::jthread
std::mutex
std::recursive_mutex
std::lock_guard
std::unique_lock
std::scoped_lock
std::condition_variable
std::atomic
```

Understand:

- Race condition
- Data race
- Deadlock
- Livelock
- Starvation
- Critical section
- Producer/consumer
- Reader/writer concepts
- Memory visibility
- Lock ordering

---

# C++ Memory Model Basics

Understand:

```text
happens-before
atomic operations
acquire
release
sequential consistency
```

You do not initially need to become an expert in lock-free programming.

But understand why shared access such as:

```cpp
counter++;
```

can be unsafe.

---

# Thread-Safe Queue Project

Implement:

```cpp
template<typename T>
class BlockingQueue {
public:
    void push(T value);
    T pop();

private:
    std::queue<T> queue_;
    std::mutex mutex_;
    std::condition_variable cv_;
};
```

Then improve it.

Add:

- Maximum capacity
- `try_push`
- `try_pop`
- Shutdown support
- Timeout support
- Move semantics
- Exception safety

Discuss:

- Who owns stored elements?
- When should threads block?
- How does shutdown work?
- How do you avoid lost wakeups?
- How do you handle spurious wakeups?
- How could deadlock occur?
- What are the performance implications?

---

# 7. Phase 5 — Embedded Interview Specialization

## Weeks 17–18

This is not beginner embedded study.

Use your existing experience and convert it into concise interview-ready knowledge.

---

# MCU Topics

Review:

- Interrupts
- Interrupt service routines
- Interrupt latency
- DMA
- Timers
- Watchdogs
- GPIO
- ADC
- PWM
- Memory-mapped I/O
- Boot sequence
- Bootloaders
- Flash
- SRAM
- Cache basics
- Memory barriers

---

# Communication Protocols

Review:

- UART
- SPI
- I2C
- CAN
- CAN-FD
- Ethernet basics

For each, know:

- Typical topology
- Timing characteristics
- Error detection
- Advantages
- Disadvantages
- Common embedded uses
- Typical debugging methods

---

# RTOS Topics

Master:

- Tasks / threads
- Priorities
- Preemption
- Scheduler
- Semaphores
- Mutexes
- Message queues
- Event flags
- Priority inversion
- Priority inheritance
- Interrupt latency
- Context switching
- Timer services
- Deadlines

Be able to answer:

> What is priority inversion?

And:

> How can priority inheritance help?

---

# Embedded Debugging

Be able to discuss:

- GDB
- JTAG
- SWD
- Core dumps
- Crash dumps
- Assertions
- Logging
- Trace systems
- Logic analyzer
- Oscilloscope
- Bus analyzer
- Fault injection

Also study sanitizers when working on Linux-hosted components:

```text
AddressSanitizer
UndefinedBehaviorSanitizer
ThreadSanitizer
```

---

# 8. Linux Systems Programming

Important for many Google, Meta, Amazon, Tesla, Waymo, and Zoox systems roles.

Master:

- Processes
- Threads
- Virtual memory
- Page faults
- `mmap`
- File descriptors
- Pipes
- Signals
- Sockets
- `select`
- `poll`
- `epoll`
- IPC
- System calls
- Context switches
- Scheduling basics

Understand:

```text
User space
    ↓ system call
Kernel
    ↓
Hardware
```

Be prepared to compare:

```text
Process vs thread
Mutex vs semaphore
Pipe vs socket
Blocking vs non-blocking I/O
Synchronous vs asynchronous I/O
```

---

# 9. Phase 6 — Autonomous Vehicle Specialization

## Weeks 19–20

You do not need to become an ML researcher to apply for embedded/systems roles.

Understand the high-level autonomy stack:

```text
Sensors
   ↓
Sensor Drivers
   ↓
Sensor Fusion / Perception
   ↓
Localization
   ↓
Prediction
   ↓
Planning
   ↓
Control
   ↓
Vehicle
```

For embedded and systems roles, go deeper into:

```text
Sensors
   ↓
Drivers
   ↓
Data Transport
   ↓
Timestamping
   ↓
Synchronization
   ↓
Compute
   ↓
Control / Actuation
```

Study:

- Sensor timestamps
- Clock synchronization
- Sensor synchronization
- Latency
- Jitter
- Deterministic behavior
- Fault detection
- Health monitoring
- Watchdogs
- Redundancy
- Graceful degradation
- Safe states
- Telemetry
- Logging
- CAN communication
- Sensor interfaces
- Safety-critical design

---

# 10. Recommended Major Project

Build a **Mini Vehicle Embedded Platform Simulator**.

This is significantly more relevant to your target roles than a generic application project.

Possible architecture:

```text
                 VehicleController
                        |
       +----------------+----------------+
       |                |                |
      IMU          WheelSpeed          Battery
       |                |                |
       +---------- SensorManager --------+
                        |
                   Message Bus
                        |
            +-----------+-----------+
            |                       |
          Logger               SafetyMonitor
                                      |
                                   Watchdog
```

---

# Features

Implement:

- Device interfaces
- RAII
- `std::unique_ptr`
- `std::shared_ptr` only where justified
- Threads
- Mutexes
- Condition variables
- State machines
- Ring buffers
- Queues
- Callbacks
- CAN-message abstraction
- Logging
- Unit tests
- Fault injection

---

# Fault Injection

Simulate:

```text
Sensor timeout
Invalid CAN frame
Dropped CAN frame
Over-temperature
Communication failure
Watchdog timeout
Invalid sensor data
Slow sensor
Thread stall
```

---

# Safety State Machine

Example:

```text
NORMAL
   ↓
DEGRADED
   ↓
SAFE_STOP
```

Possible conditions:

```text
NORMAL
  |
  | sensor failure
  ↓
DEGRADED
  |
  | critical fault
  ↓
SAFE_STOP
```

Implement transitions explicitly.

Example:

```cpp
enum class VehicleState {
    Normal,
    Degraded,
    SafeStop
};
```

---

# Project Discussion Questions

Prepare to answer:

- Who owns each object?
- What are the lifetimes?
- Where do threads exist?
- Where can race conditions occur?
- What happens when a sensor dies?
- What happens when CAN traffic stops?
- What happens if logging becomes slow?
- Can a high-priority task block on a low-priority one?
- How would this work on an RTOS?
- How would you eliminate dynamic allocation?
- How would you measure latency?
- How would you test failures?
- How would you design the watchdog?
- How would you make the system deterministic?
- What data needs timestamps?

A project that allows you to answer these questions is excellent interview material.

---

# 11. C++ Interview Checklist

You should eventually be able to explain each of these immediately.

## Language

- Pointer vs reference
- Const pointer vs pointer-to-const
- Stack vs heap
- `new` / `delete`
- RAII
- Rule of Three
- Rule of Five
- Rule of Zero
- Copy constructor
- Copy assignment
- Move constructor
- Move assignment
- lvalue
- rvalue
- `std::move`
- `std::forward`
- Virtual functions
- Virtual destructor
- Pure virtual functions
- Object slicing
- Templates
- `constexpr`
- `noexcept`
- Lambdas
- `explicit`
- `override`
- `final`

---

# STL Checklist

Know:

- `vector` vs `list`
- `map` vs `unordered_map`
- `set` vs `unordered_set`
- `deque`
- `priority_queue`
- Iterator invalidation
- Vector reallocation
- `reserve`
- `resize`
- `emplace_back` vs `push_back`
- Custom comparator
- Custom hash
- Copy vs move behavior

---

# Memory Checklist

Know:

- `unique_ptr`
- `shared_ptr`
- `weak_ptr`
- Ownership
- Shared-pointer cycles
- Alignment
- Padding
- Fragmentation
- Undefined behavior
- Dangling references
- Memory leaks
- Buffer overrun
- Use-after-free

---

# Concurrency Checklist

Know:

- Mutex
- Semaphore
- Condition variable
- Atomic
- Race condition
- Data race
- Deadlock
- Livelock
- Starvation
- Producer/consumer
- Lock ordering
- Memory ordering basics
- Happens-before

---

# Systems Checklist

Know:

- Process vs thread
- Virtual memory
- Page fault
- Context switch
- System call
- Interrupt
- DMA
- IPC
- Socket
- File descriptor
- Blocking/non-blocking I/O

---

# Embedded Checklist

Know:

- ISR
- Interrupt latency
- Priority inversion
- DMA
- Watchdog
- Timer
- GPIO
- ADC
- PWM
- UART
- SPI
- I2C
- CAN
- CAN-FD
- RTOS scheduling
- Bootloaders
- Memory-mapped I/O

---

# 12. Weekly Study Schedule

A sustainable schedule for someone working full time:

## Monday — 2 Hours

```text
60 min — DSA
45 min — C++
15 min — review
```

## Tuesday — 2 Hours

```text
60 min — DSA
60 min — C++ / OOP
```

## Wednesday — 2 Hours

```text
60 min — DSA
60 min — OS / embedded
```

## Thursday — 2 Hours

```text
60 min — DSA
60 min — C++
```

## Friday

Rest.

Optional:

```text
30–60 min review
```

Do not make every day high intensity.

Consistency is more important than burnout.

## Saturday — 4 Hours

```text
90 min  — DSA
120 min — project
30 min  — C++ review
```

## Sunday — 3 Hours

```text
60 min — timed coding
60 min — systems / embedded
60 min — review + notes
```

Total:

**Approximately 15 hours per week.**

---

# 13. Interview Error Notebook

Maintain a notebook for mistakes.

Example:

```text
Problem:
Longest Substring Without Repeating Characters

Pattern:
Sliding window

Mistake:
Moved left pointer incorrectly.

Correct insight:
Track the most recent index of each character.

Complexity:
O(n)

Redo:
3 days
10 days
30 days
```

---

# C++ Mistake Log

Create a section for C++ mistakes.

Examples:

```text
Forgot virtual destructor
Iterator invalidated
Copied object instead of moving it
Used shared_ptr unnecessarily
Forgot const correctness
Held mutex for too long
Deadlock caused by inconsistent lock order
Used reference after vector reallocation
Returned reference to local variable
Captured lambda variable incorrectly
```

Over time, focus your study increasingly on recurring weaknesses.

---

# 14. Recommended Problem Count

You do not need 500 random problems.

A better target:

| Area | Target |
|---|---:|
| Arrays / Strings / Hashing | 30 |
| Two pointers / Sliding window | 20 |
| Linked lists | 10 |
| Stack / Queue | 15 |
| Binary search | 15 |
| Trees | 25 |
| Graphs | 25 |
| Heap / Priority queue | 15 |
| Backtracking | 15 |
| Greedy / Intervals | 15 |
| Dynamic programming | 20 |
| Bit manipulation | 10 |

Total:

**Approximately 150–200 problems.**

Repeated problems count as valuable practice.

Quality is much more important than raw problem count.

---

# 15. Bit Manipulation

Because you are targeting embedded roles, give bit manipulation slightly more attention than a generic software-engineering candidate.

Master:

```cpp
x & mask
x | mask
x ^ mask
~x
x << n
x >> n
```

Know how to:

- Set a bit
- Clear a bit
- Toggle a bit
- Test a bit
- Count bits
- Determine power of two
- Extract bit fields
- Manipulate hardware-register masks

Example:

```cpp
register_value |= (1u << bit);
```

Clear:

```cpp
register_value &= ~(1u << bit);
```

Test:

```cpp
bool set = register_value & (1u << bit);
```

---

# 16. Company-Specific Focus

The exact interview loop can change, so always inspect the specific role before interviewing.

Still, the preparation priorities generally look like this.

| Company / Team | Highest Priorities |
|---|---|
| Google embedded/systems | DSA → C++ → OS/concurrency → embedded → design |
| Amazon embedded/robotics | DSA → C++ → embedded/RTOS → OOD → behavioral |
| Meta systems/on-device | DSA → C++ → OS/concurrency → performance → design |
| Tesla embedded/vehicle | C++ → embedded/Linux → debugging → concurrency → DSA |
| Zoox embedded | C/C++ → RTOS → MCU/hardware → CAN → debugging → DSA |
| Waymo systems/autonomy | C++ → DSA → systems/concurrency → performance → autonomy architecture |

---

# Google Preparation

Emphasize:

- Algorithms
- Clean C++ implementation
- Data structures
- Complexity analysis
- Systems fundamentals
- Linux
- Concurrency
- Embedded fundamentals for embedded positions
- Communication during coding

Practice solving unfamiliar medium-level problems without assistance.

---

# Amazon Preparation

Emphasize:

- DSA
- C++
- OOP
- Embedded systems
- RTOS
- System design
- Behavioral interviews

Prepare strong examples related to:

- Ownership
- Debugging
- Production incidents
- Reliability
- Delivering under uncertainty
- Technical disagreements
- Tradeoffs
- Leadership

---

# Meta Preparation

Emphasize:

- Coding speed
- DSA
- Clean C++
- Systems
- Performance
- Memory
- Concurrency

Practice solving two medium problems under time pressure.

---

# Tesla Preparation

For embedded/vehicle positions emphasize:

- Strong C++
- C
- Linux
- Firmware
- Drivers
- Hardware interfaces
- CAN
- Debugging
- Performance optimization
- Real-time behavior
- Concurrency

Be ready to discuss actual debugging stories.

---

# Zoox Preparation

Emphasize:

- C/C++
- RTOS
- MCU development
- Bootloaders
- Hardware/software integration
- CAN
- Real-time systems
- Safety
- Debugging

Your embedded background can be a particularly strong advantage here.

---

# Waymo Preparation

Emphasize:

- C++
- Algorithms
- Systems
- Concurrency
- Performance
- Distributed / autonomous system concepts
- Sensors
- Latency
- Reliability
- Vehicle architecture
- Safety

---

# 17. When to Start Applying

Do not wait until Week 20.

Recommended progression:

```text
Weeks 1–6
Modern C++
OOP
First project
No interview pressure

Weeks 7–10
DSA foundations
Start easy/medium problems
Improve coding speed

Weeks 11–14
Trees
Graphs
DP
Start mock interviews
Apply to lower-priority companies

Weeks 15–16
Systems C++
Concurrency
Linux
Start recruiter conversations

Weeks 17–18
Embedded / RTOS specialization
Apply more aggressively

Weeks 19–20
Autonomy specialization
Mock interview intensity increases
Target:
Google
Meta
Amazon
Tesla
Zoox
Waymo
```

You want real interview experience before interviewing with your highest-priority companies.

---

# 18. Avoid "C With Classes"

A very important transition for you is moving from C-style resource management toward C++ ownership models.

Avoid automatically writing:

```cpp
Foo* foo = new Foo();

...

delete foo;
```

Prefer:

```cpp
auto foo = std::make_unique<Foo>();
```

But even that is unnecessary if the object can simply live on the stack:

```cpp
Foo foo;
```

The mental-model change is:

Old question:

```text
Who calls delete/free?
```

Better question:

```text
Who owns this resource?
What is its lifetime?
Which object's lifetime should control it?
Can lifetime be expressed automatically?
```

This shift distinguishes modern C++ design from "C with classes."

---

# 19. Topics to Deprioritize Initially

Do not spend excessive preparation time on:

- Advanced template metaprogramming
- Extremely obscure C++ standard rules
- Competitive-programming tricks
- Extremely hard dynamic programming
- Memorizing every design pattern
- GUI programming
- Web development
- Advanced CMake internals
- ML research theory

You already understand compilers and build processes well, so only review them if a particular role strongly emphasizes:

- Toolchains
- Linkers
- Build systems
- Cross compilation
- Compiler infrastructure

---

# 20. Additional High-Value C++ Topics

Once the fundamentals are strong, study:

## Templates

Understand:

```cpp
template<typename T>
T max_value(T a, T b);
```

Know the concepts behind:

- Function templates
- Class templates
- Template specialization
- Type deduction

You do not need advanced metaprogramming initially.

---

## Type Safety

Understand why C++ provides safer alternatives such as:

```cpp
static_cast
dynamic_cast
const_cast
reinterpret_cast
```

Be particularly cautious with:

```cpp
reinterpret_cast
```

---

## `std::optional`

Useful for representing a value that may not exist.

```cpp
std::optional<SensorReading>
```

---

## `std::variant`

Useful for type-safe alternatives.

---

## `std::span`

Especially useful for systems programming where you want:

- A view into contiguous memory
- No ownership
- Size information

Example:

```cpp
void process(std::span<const std::byte> data);
```

---

## `std::string_view`

Useful for non-owning views over string data.

Know lifetime risks.

---

# 21. Systems Design Topics for Embedded Interviews

Practice designing:

- Logging system
- Telemetry system
- Sensor ingestion system
- Device manager
- Firmware-update system
- CAN message router
- Watchdog service
- Configuration service
- Thread-safe queue
- Event dispatcher
- Hardware abstraction layer
- Fault-monitoring system

For every design ask:

```text
What are the requirements?
What are the latency requirements?
What are the memory constraints?
What are the failure modes?
What happens during overload?
What owns each resource?
Which components are concurrent?
How do components communicate?
How is the system tested?
How is the system monitored?
```

---

# 22. Real-Time Thinking

For embedded/autonomy work, train yourself to think beyond average performance.

Instead of:

```text
Average latency = 2 ms
```

also ask:

```text
What is the worst-case latency?
What is the 99.9 percentile?
Is latency deterministic?
Can memory allocation occur on this path?
Can the thread block?
Could priority inversion occur?
```

This mindset is highly valuable for real-time systems.

---

# 23. Debugging Interview Preparation

Prepare real examples from your experience.

Structure debugging stories like:

```text
Symptom
↓
Initial hypotheses
↓
Instrumentation
↓
Evidence
↓
Root cause
↓
Fix
↓
Verification
↓
Prevention
```

Examples to prepare:

- Memory corruption
- Race condition
- Hardware communication failure
- Timing bug
- Interrupt problem
- Stack overflow
- Heap corruption
- Driver bug
- CAN issue
- Boot failure
- Performance regression

---

# 24. Behavioral Interview Preparation

Prepare approximately 8–10 strong stories.

Cover:

- Most difficult technical problem
- Production failure
- Disagreement with teammate
- Design tradeoff
- Leadership without authority
- Tight deadline
- Mistake you made
- Major debugging problem
- Performance improvement
- Reliability improvement

Use STAR:

```text
Situation
Task
Action
Result
```

But keep most of the interview time focused on:

**Action + Result.**

---

# 25. Mock Interview Progression

## Early Stage

Practice without strict time limits.

Goal:

- Correct thinking
- Clean code
- Pattern recognition

## Middle Stage

Use 35–45 minute coding sessions.

Goal:

- Interview pacing
- Communication
- Debugging

## Final Stage

Simulate complete interviews.

For coding:

```text
5 min  clarify + examples
5 min  brute force + optimization
20 min implementation
5 min  testing
5 min  follow-up discussion
```

---

# 26. Final Readiness Criteria

You are ready to interview aggressively when most of these are true.

## Coding

You can solve most standard medium problems in approximately 25–35 minutes.

You consistently:

- Explain before coding
- Use good variable names
- Test edge cases
- State complexity
- Avoid compiler-level mistakes

---

## C++

You can explain:

- Ownership
- RAII
- Rule of Zero/Five
- Move semantics
- Smart pointers
- STL complexity
- Iterator invalidation
- Virtual dispatch
- Object lifetime
- Const correctness
- Templates
- Lambdas

without needing to look them up.

---

## Concurrency

You can:

- Diagnose races
- Explain deadlocks
- Use mutexes correctly
- Use condition variables correctly
- Explain atomics at a basic level
- Discuss lock granularity
- Design producer/consumer queues

---

## Embedded

You can confidently discuss:

- Interrupts
- DMA
- RTOS scheduling
- Memory constraints
- Device drivers
- Hardware interfaces
- CAN
- Watchdogs
- Debugging
- Real-time behavior

---

## Systems

You can explain:

- Processes
- Threads
- Virtual memory
- System calls
- File descriptors
- IPC
- Networking basics
- Context switching
- Synchronization

---

# 27. Five-Month Milestone View

## Month 1

Focus:

```text
Modern C++
RAII
Ownership
STL
Move semantics
```

Expected outcome:

You stop writing C++ as "C with classes."

---

## Month 2

Focus:

```text
OOP
Design
Arrays
Strings
Hashing
Two pointers
Sliding windows
Linked lists
Binary search
```

Expected outcome:

You become comfortable solving easy and lower-medium interview problems in C++.

---

## Month 3

Focus:

```text
Trees
Graphs
Heaps
Intervals
Backtracking
DP
```

Expected outcome:

Most major interview patterns are familiar.

---

## Month 4

Focus:

```text
Concurrency
Linux
Memory
Systems programming
Mock interviews
```

Expected outcome:

You become competitive for general systems C++ interviews.

---

## Month 5

Focus:

```text
RTOS
Embedded design
CAN
Real-time systems
Autonomy architecture
Mock interviews
Applications
```

Expected outcome:

You are specifically prepared for embedded/autonomy/system roles.

---

# 28. Final Priority Order

When deciding what to study next, use this ranking:

```text
1. Data Structures & Algorithms
2. Modern C++ / ownership / lifetime
3. STL fluency
4. Concurrency
5. OS / Linux systems knowledge
6. Embedded / RTOS knowledge
7. OOP / design
8. Autonomous vehicle architecture
9. Behavioral interview preparation
10. Advanced C++ topics
```

Because you already have embedded and C experience, your largest improvements will probably come from:

```text
Modern C++ fluency
        +
Interview problem solving
        +
Concurrency/system-design communication
```

---

# 29. Your Target Interview Identity

Do not aim to present yourself merely as:

> An embedded C engineer who has learned some C++.

Aim to become:

> A systems-oriented C++ engineer with strong embedded fundamentals who can reason about memory, ownership, concurrency, real-time behavior, algorithms, hardware/software boundaries, reliability, and system design.

That combination is highly aligned with the roles you are targeting.

---

# 30. Final Roadmap

```text
CURRENT PROFILE
Embedded Systems + Strong C
          │
          ▼
Modern C++ Object Model
          │
          ▼
RAII + Ownership + Lifetime
          │
          ▼
STL Fluency
          │
          ▼
OOP + Software Design
          │
          ▼
Arrays / Strings / Hashing
          │
          ▼
Trees / Graphs / Heaps / DP
          │
          ▼
C++ Memory + Concurrency
          │
          ▼
Linux Systems Programming
          │
          ▼
RTOS + Embedded Interview Review
          │
          ▼
CAN + Safety + Real-Time Systems
          │
          ▼
Autonomous Vehicle Architecture
          │
          ▼
Projects + Mock Interviews
          │
          ▼
Google / Amazon / Meta
Tesla / Zoox / Waymo
```

---

# Guiding Principle

By the end of this plan, you should be able to take an unfamiliar problem and:

1. Clarify the requirements.
2. Identify the relevant data structures.
3. Develop a brute-force solution.
4. Optimize it.
5. Implement clean modern C++.
6. Explain time and space complexity.
7. Reason about ownership and lifetime.
8. Identify concurrency implications.
9. Discuss real-time and embedded constraints.
10. Debug failures systematically.
11. Explain engineering tradeoffs clearly.

That is the level to target for strong C++ systems, embedded, robotics, and autonomous-vehicle interviews.
