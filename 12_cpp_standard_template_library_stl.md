# C++ Standard Template Library (STL): Containers, Iterators, and Algorithms

The STL is the generic-programming core of the C++ standard library. Its central achievement is separating data structures from algorithms through iterator and callable interfaces.

Read [`11_cpp_templates_and_generic_programming.md`](./11_cpp_templates_and_generic_programming.md) for the template mechanics behind these facilities.

---

## Part I - Five-Minute Interview Review

## What the STL is

The STL design consists primarily of:

```text
Containers
    + Iterators
    + Algorithms
    + Function objects/callables
    + Allocators
```

Example:

```cpp
std::vector<int> values{4, 1, 3, 2};

std::ranges::sort(values);

auto iterator = std::ranges::find(values, 3);
```

- `vector` owns elements.
- Iterators/ranges expose traversal.
- `sort` and `find` are generic algorithms.
- A comparator can customize ordering.
- An allocator controls storage acquisition policy.

See [The STL architecture](#2-the-stl-architecture).

## Container selection in five minutes

| Need | Strong default |
|---|---|
| General dynamic sequence, random access | `std::vector` |
| Compile-time fixed contiguous sequence | `std::array` |
| Efficient insertion/removal at both ends | `std::deque` |
| Stable nodes and frequent known-position splicing | `std::list` |
| Ordered unique keys | `std::set` |
| Ordered key/value pairs | `std::map` |
| Average constant-time key lookup, no ordering | `std::unordered_map` / `unordered_set` |
| LIFO | `std::stack` |
| FIFO | `std::queue` |
| Repeated highest/lowest priority extraction | `std::priority_queue` |

See [Container comparison](#10-container-selection-and-tradeoffs).

### Default rule

> Prefer `std::vector` unless another container's specific semantics are required.

A linked list is not automatically faster for insertion because locating the position is linear and node allocation/cache misses can dominate.

## High-frequency complexities

| Operation | Typical complexity |
|---|---:|
| `vector[index]` | O(1) |
| `vector::push_back` | Amortized O(1) |
| `vector` middle insertion | O(n) |
| `map::find` | O(log n) |
| `unordered_map::find` | Average O(1), worst O(n) |
| `priority_queue::push/pop` | O(log n) |
| `priority_queue::top` | O(1) |
| `std::find` | O(n) |
| `std::sort` | O(n log n) |
| `lower_bound` comparisons | O(log n) on a partitioned range |

See [Complexity guarantees](#18-complexity-guarantees-and-amortization).

## Iterator invalidation in five minutes

- `vector` reallocation invalidates all element pointers, references, and iterators.
- `vector` erase invalidates those at and after the erased position.
- `list` insertion does not invalidate existing iterators; erase invalidates only erased elements.
- Ordered associative insertion preserves iterators/references; erase invalidates erased elements.
- Unordered rehash invalidates iterators, while references/pointers to elements generally remain valid; erasure invalidates the erased element.

See [Iterator invalidation](#15-iterator-pointer-and-reference-invalidation).

## Loop and algorithm choices

```cpp
for (const auto& value : values) { } // read without copies
for (auto& value : values) { }       // mutate elements
for (auto value : values) { }        // copy each element
```

Prefer named algorithms when they express intent:

```cpp
std::ranges::sort(values);
std::ranges::reverse(values);
auto found = std::ranges::find(values, target);
```

See [Algorithms](#16-core-algorithm-families) and [`std::ranges`](#17-c20-ranges-algorithms-and-views).

### Five interview checks

1. **`vector` or `list` by default?** `vector`, because contiguous storage and locality usually dominate.
2. **`map` or `unordered_map`?** Ordered/predictable logarithmic behavior versus hash-based average constant lookup and rehash costs.
3. **`reserve` or `resize`?** Reserve changes capacity; resize changes element count.
4. **Does `emplace_back` always outperform `push_back`?** No.
5. **Can `std::sort` sort a `std::list`?** No; use `list::sort` because standard sort requires random-access iterators.

---

## Part II - Detailed Reference

## 1. STL versus the C++ standard library

The C++ standard library is broader than the STL.

STL-style components include:

- Containers.
- Iterators.
- Algorithms.
- Function objects.
- Allocators.

The standard library also includes:

- Strings and streams.
- Filesystem.
- Threads and atomics.
- Chrono.
- Regular expressions.
- Smart pointers.
- `optional`, `variant`, and `expected`.
- Numerics and math.
- Ranges and views.
- Many other facilities.

People often use “STL” informally for most of `std`, but a precise interview answer distinguishes the generic container/iterator/algorithm design from the entire library.

### Interview question

**Question:** Is `std::thread` part of the STL?

**Answer:** It is part of the C++ standard library, but not traditionally part of the STL container/iterator/algorithm design.

---

## 2. The STL architecture

### Container

Owns and organizes elements:

```cpp
std::vector<Device> devices;
```

### Iterator

Represents a traversal position:

```cpp
auto first = devices.begin();
auto last = devices.end();
```

`end()` is a past-the-end sentinel/iterator and cannot be dereferenced.

### Algorithm

Operates on iterator/range abstractions:

```cpp
std::sort(first, last);
```

### Callable/policy

Customizes behavior:

```cpp
std::sort(first, last,
          [](const Device& left, const Device& right) {
              return left.priority() < right.priority();
          });
```

### Allocator

Controls storage allocation/deallocation mechanics:

```cpp
std::vector<Device, CustomAllocator<Device>> devices;
```

### Separation benefit

An algorithm can work with many containers when iterator capabilities match. `std::find` works with vector, list, arrays, and many custom ranges. `std::sort` needs random access, so it is more restrictive.

### Interview question

**Question:** Why do STL algorithms accept iterators rather than container types?

**Answer:** Iterators decouple algorithms from storage, allowing one generic implementation to work with many containers/ranges that provide the required traversal operations.

---

## 3. Headers and namespace

Common headers:

```cpp
#include <algorithm>
#include <array>
#include <deque>
#include <functional>
#include <iterator>
#include <list>
#include <map>
#include <memory>
#include <numeric>
#include <queue>
#include <ranges>
#include <set>
#include <span>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
```

Standard names are in `std`:

```cpp
std::vector<int> values;
```

Avoid:

```cpp
using namespace std;
```

in headers. It affects every includer and can create collisions/overload changes.

Do not add ordinary declarations to namespace `std`. Only explicitly permitted specializations/customizations are allowed, under their exact requirements.

### Interview question

**Question:** Why should `using namespace std;` be avoided in headers?

**Answer:** It imports a large evolving name set into every including translation unit, causing collisions and changed lookup/overload behavior.

---

## 4. `std::array`

```cpp
std::array<int, 4> values{1, 2, 3, 4};
```

Properties:

- Fixed element count in the type.
- Contiguous storage.
- Usually stored directly inside its containing object.
- Standard container interface (`begin`, `end`, `size`, `data`).
- No dynamic resizing.
- Supports aggregate-like initialization and value semantics.

Compared with a built-in array:

```cpp
int raw[4]{};
```

`std::array` is assignable as a whole, works directly with algorithms, and reports size.

```cpp
std::array<int, 4> other = values;
```

`std::array<int, 4>` and `std::array<int, 8>` are different types.

Zero-size arrays are supported through `std::array<T, 0>`, with special front/back rules.

### Interview question

**Question:** When prefer `std::array` over `std::vector`?

**Answer:** When the extent is fixed at compile time and direct contiguous storage without dynamic resizing is desired.

---

## 5. `std::vector`

```cpp
std::vector<int> values;
values.push_back(10);
```

Properties:

- Contiguous element storage.
- O(1) random access.
- Dynamic size.
- Amortized O(1) `push_back`.
- O(n) insertion/erase except near the end.
- Excellent cache locality.
- Compatible with C APIs through `data()` when element representation/API rules match.

Conceptual state:

```text
size     = number of live elements
capacity = number of elements storage can currently hold
```

Reallocation allocates a larger block, moves/copies elements, destroys old elements, and releases old storage.

### Why vector is the default

- Low per-element overhead.
- Few allocations.
- Locality and prefetching.
- Fast iteration.
- Random access.
- Broad algorithm compatibility.

### `vector<bool>`

`std::vector<bool>` is a space-optimized specialization whose element access uses proxy objects rather than ordinary `bool&`. Generic code must not assume `operator[]` returns a real reference.

### Interview question

**Question:** What happens when vector size exceeds capacity?

**Answer:** It reallocates storage, moves or copies elements, destroys the old elements, and invalidates all pointers/references/iterators into the previous block.

---

## 6. `std::deque`

```cpp
std::deque<int> values;
values.push_front(1);
values.push_back(2);
```

Properties:

- Efficient insertion/removal at both ends.
- O(1) random access.
- Usually segmented/non-contiguous storage.
- No guarantee that all elements occupy one continuous block.
- Different invalidation rules from vector.

Use when:

- Both front and back operations are frequent.
- Random access remains useful.
- Stable contiguous storage is not required.

Do not pass deque element storage as one C-style contiguous array.

### Tradeoff versus vector

Deque avoids moving all elements for front insertion, but has more indirection and often poorer locality. Vector remains preferable for simple append-and-iterate workloads.

### Interview question

**Question:** Can `deque.data()` provide one contiguous buffer like vector?

**Answer:** No general contiguous-storage guarantee exists for deque; its storage is typically segmented.

---

## 7. `std::list` and `std::forward_list`

### Doubly linked list

```cpp
std::list<int> values;
```

Properties:

- Bidirectional iterators.
- O(1) insertion/erase given a valid position.
- Stable iterators/references to other nodes.
- O(1) splicing between compatible lists.
- No random access.
- Node allocation and pointer overhead per element.
- Poor locality.

### Singly linked list

```cpp
std::forward_list<int> values;
```

Properties:

- Forward iteration only.
- Smaller node linkage.
- Operations often use “before” positions (`insert_after`, `erase_after`).
- No ordinary `size()` requirement historically due complexity/design goals.

### Why O(1) insertion may still be slower

You must first reach the position, often O(n), and allocate a node. Vector's bulk memory movement can outperform lists due to locality.

### List-specific algorithms

Because list iterators are not random-access:

```cpp
values.sort();
values.merge(other);
values.unique();
values.remove_if(predicate);
```

### Interview question

**Question:** When is `std::list` justified?

**Answer:** When stable node addresses/iterators, known-position insertion/erasure, or constant-time splicing is required and node allocation/locality costs are acceptable.

---

## 8. Ordered associative containers

```cpp
std::set<Key> keys;
std::map<Key, Value> values;
std::multiset<Key> duplicate_keys;
std::multimap<Key, Value> duplicate_pairs;
```

Typically implemented as balanced search trees, though the standard specifies behavior/complexity rather than exact structure.

Properties:

- Ordered iteration.
- O(log n) lookup/insertion/erase.
- Stable references/iterators except erased elements.
- Key equivalence based on comparator, not necessarily `operator==`.
- Node allocation overhead.

### `map::operator[]`

```cpp
counts[key]++;
```

If `key` is absent, `operator[]` inserts a default-constructed mapped value.

For lookup without insertion:

```cpp
auto iterator = counts.find(key);
```

C++20:

```cpp
if (counts.contains(key)) {
}
```

For insertion without requiring default construction:

```cpp
counts.try_emplace(key, arguments...);
counts.insert_or_assign(key, value);
```

### Comparator equivalence

Keys `a` and `b` are equivalent when:

```cpp
!compare(a, b) && !compare(b, a)
```

Comparator must provide strict weak ordering.

### Interview question

**Question:** Why can reading `map[key]` modify a map?

**Answer:** `operator[]` inserts a default mapped value when the key is absent.

---

## 9. Unordered associative containers

```cpp
std::unordered_set<Key> keys;
std::unordered_map<Key, Value> values;
```

Hash-table properties:

- Average O(1) lookup/insertion/erase.
- Worst-case O(n).
- No sorted iteration.
- Buckets, load factor, and rehashing.
- Requires compatible hash and equality.
- Often significant memory overhead.
- Iterator invalidation on rehash.

### Hash/equality contract

If keys are equal under the equality predicate, they must produce the same hash value.

A custom key:

```cpp
struct Key {
    int bus;
    int address;

    bool operator==(const Key&) const = default;
};

struct KeyHash {
    std::size_t operator()(const Key& key) const noexcept {
        // combine fields with an appropriate hash strategy
    }
};
```

### Reserve and load factor

```cpp
values.reserve(expected_count);
values.max_load_factor(0.8f);
```

Reserving can avoid repeated rehashing and reduce latency spikes.

### Security/determinism

Adversarial collisions can degrade to linear behavior. Ordered maps provide logarithmic worst-case guarantees and often more predictable iteration.

### Interview question

**Question:** Why is unordered-map lookup not simply O(1)?

**Answer:** O(1) is the average expected complexity under suitable hashing/load; collisions can produce O(n) worst-case behavior.

---

## 10. Container selection and tradeoffs

| Container | Contiguous | Random access | Ordered keys | Typical insertion strength | Stability |
|---|---:|---:|---:|---|---|
| `array` | Yes | O(1) | N/A | Fixed size | Addresses stable while object lives |
| `vector` | Yes | O(1) | N/A | Back append | Reallocation invalidates all |
| `deque` | No guarantee | O(1) | N/A | Front/back | Operation-specific |
| `list` | No | No | N/A | Known position/splice | Other nodes stable |
| `map`/`set` | No | No | Yes | O(log n) | Other nodes stable |
| `unordered_map`/`set` | No | No | No | Average O(1) | Rehash invalidates iterators |

Selection questions:

1. Is ordering required?
2. Is random access required?
3. Is contiguous memory required?
4. Are stable references required?
5. What are worst-case timing requirements?
6. What is the insertion/erase pattern?
7. Is dynamic allocation allowed?
8. How large are elements and keys?
9. Does iteration dominate lookup?
10. Is an alternative sorted vector better for read-heavy data?

A sorted vector can outperform a tree for small/read-heavy sets due to locality, at the cost of O(n) insertion.

### Interview question

**Question:** Why might a sorted vector beat a map?

**Answer:** Contiguous storage gives better locality and lower overhead; binary search is logarithmic, though insertion remains linear.

---

## 11. Container adapters

Adapters provide restricted interfaces over another container.

### Stack

```cpp
std::stack<int> stack;
stack.push(1);
stack.pop();
stack.top();
```

LIFO. Default underlying container is typically deque.

### Queue

```cpp
std::queue<int> queue;
queue.push(1);
queue.pop();
queue.front();
queue.back();
```

FIFO.

### Priority queue

```cpp
std::priority_queue<int> priorities;
```

Default is a max heap:

```cpp
priorities.top(); // largest
```

Min heap:

```cpp
std::priority_queue<
    int,
    std::vector<int>,
    std::greater<int>
> minimums;
```

Adapters intentionally do not expose general iteration.

### Interview question

**Question:** Why does `priority_queue` with `std::less` place the largest element at top?

**Answer:** The comparator defines heap ordering such that the element considered highest priority under the adapter's rules is the maximum for `less`.

---

## 12. `std::string`

`std::string` is a contiguous owning sequence of characters with string-specific operations.

```cpp
std::string name = "camera";
name += "_front";
```

Properties:

- Dynamic size.
- Contiguous characters.
- Null terminator available through `c_str()` and modern `data()` rules.
- Value semantics.
- Iterator/reference invalidation on modifying operations according to specified rules.
- May use Small String Optimization, but SSO is not guaranteed or standardized in size/layout.

### String versus string view

```cpp
std::string      // owns characters
std::string_view // borrows characters
```

A view is cheaper to copy but can dangle and is not necessarily null-terminated.

### Interview question

**Question:** Is Small String Optimization guaranteed?

**Answer:** No. It is a common implementation optimization, but capacity/layout/threshold are implementation-specific.

---

## 13. Iterator fundamentals

An iterator represents a position in a sequence/range.

```cpp
auto iterator = values.begin();

if (iterator != values.end()) {
    int value = *iterator;
    ++iterator;
}
```

Core operations vary by category:

- Dereference: `*iterator`.
- Increment: `++iterator`.
- Comparison.
- Decrement for bidirectional.
- Arithmetic/indexing for random access.

### Past-the-end

`end()` identifies the position after the last element:

```cpp
for (auto it = values.begin(); it != values.end(); ++it) {
}
```

Never dereference `end()`.

### Const iterators

```cpp
auto it = values.begin();   // mutable iterator for mutable container
auto cit = values.cbegin(); // read-only element access
```

A `const_iterator` is an iterator object that may itself be reassigned/incremented, but it yields const element access. It is not the same as a const iterator variable:

```cpp
const auto it = values.begin(); // iterator object cannot increment
```

### Interview question

**Question:** What is the difference between `const_iterator` and `const iterator`?

**Answer:** A const_iterator traverses while exposing const elements; a const-qualified iterator object itself cannot be advanced/reassigned.

---

## 14. Iterator categories

Classic hierarchy:

```text
Input / Output
    -> Forward
        -> Bidirectional
            -> Random Access
                -> Contiguous (C++20 concept)
```

### Input iterator

Single-pass reading.

### Output iterator

Writes through traversal.

### Forward iterator

Multi-pass forward traversal.

### Bidirectional iterator

Adds decrement; used by list/set/map iterators.

### Random-access iterator

Adds arithmetic, difference, ordering, indexing; vector/deque iterators.

### Contiguous iterator

Random-access plus contiguous element layout; vector/array/string pointers/iterators under relevant rules.

Algorithms require capabilities:

```text
find          -> input iterator
reverse       -> bidirectional iterator
sort          -> random-access iterator
```

C++20 iterator concepts refine the model and ranges may use different sentinel types for end.

### Interview question

**Question:** Why cannot `std::sort` accept list iterators?

**Answer:** Sort requires random-access operations such as efficient jumps/differences; list iterators are only bidirectional.

---

## 15. Iterator, pointer, and reference invalidation

### Vector

- Reallocation: invalidates all element iterators, pointers, and references.
- Insert without reallocation: invalidates at/after insertion point; earlier elements remain valid.
- Erase: invalidates erased and following positions.
- `reserve` can itself reallocate if requested capacity exceeds current capacity.

### Deque

Rules vary by operation; insertions/erases can invalidate iterators broadly while reference behavior differs. Check the exact operation rather than assuming list-like stability.

### List/forward_list

Insertion preserves existing iterators/references. Erasure invalidates only erased elements.

### Ordered associative containers

Insertion preserves existing references/iterators. Erasure invalidates only erased elements.

### Unordered containers

Rehash invalidates iterators. References/pointers to elements generally remain valid across rehash, but erasure invalidates the erased element.

### Borrowed views

A span/string_view/iterator can dangle even while its handle object remains alive.

### Interview question

**Question:** Does `vector::reserve` guarantee references remain valid forever?

**Answer:** No. It prevents reallocation only while size stays within capacity and no other invalidating operation occurs.

---

## 16. Core algorithm families

### Non-modifying queries

```cpp
std::find
std::find_if
std::count
std::count_if
std::all_of
std::any_of
std::none_of
std::equal
std::mismatch
```

### Copy/move/transform

```cpp
std::copy
std::copy_if
std::move
std::transform
std::fill
std::generate
```

Destination must have sufficient storage unless using an inserter:

```cpp
std::copy(source.begin(), source.end(),
          std::back_inserter(destination));
```

### Reordering

```cpp
std::reverse
std::rotate
std::shuffle
std::partition
std::stable_partition
```

### Sorting/selection

```cpp
std::sort
std::stable_sort
std::partial_sort
std::nth_element
```

### Binary search

```cpp
std::lower_bound
std::upper_bound
std::binary_search
std::equal_range
```

The range must satisfy the required partition/sorted condition under the same comparator.

### Set algorithms on sorted ranges

```cpp
std::set_union
std::set_intersection
std::set_difference
std::includes
```

### Heap algorithms

```cpp
std::make_heap
std::push_heap
std::pop_heap
std::sort_heap
```

### Interview question

**Question:** What precondition does `lower_bound` require?

**Answer:** The range must be partitioned with respect to the searched value/comparator—normally sorted consistently under that ordering.

---

## 17. C++20 ranges algorithms and views

Ranges algorithms accept whole ranges:

```cpp
std::ranges::sort(values);
auto found = std::ranges::find(values, target);
```

Many support projections:

```cpp
std::ranges::sort(devices, {}, &Device::priority);
```

Views are lazy adaptors:

```cpp
auto active_names =
    devices
    | std::views::filter(&Device::active)
    | std::views::transform(&Device::name);
```

### Benefits

- Fewer mismatched begin/end errors.
- Concepts state requirements.
- Projections avoid custom comparator boilerplate.
- Lazy composition avoids some temporary containers.

### Risks

- Views may borrow and dangle.
- Lazy work may repeat on repeated traversal.
- Some ranges are single-pass.
- Complex pipelines can obscure cost/control flow.
- Compiler/library support varies by standard/toolchain.

Ranges algorithms often return borrowed-aware result types; an iterator into a destroyed temporary may be represented as `std::ranges::dangling`.

### Interview question

**Question:** Does a view normally own transformed elements?

**Answer:** Usually no; it lazily computes/adapts elements and often borrows the underlying range, so lifetime must be checked.

---

## 18. Complexity guarantees and amortization

### Big-O describes growth

O(log n) map lookup and average O(1) hash lookup do not tell the complete constant factors, allocation cost, locality, or worst-case latency.

### Amortized complexity

`vector::push_back` is amortized O(1):

- Most pushes construct one element.
- Occasional growth moves/copies all existing elements.
- Total cost across many pushes remains linear under the growth strategy.

One individual push can be O(n).

### Iterator effects

`std::lower_bound` uses O(log n) comparisons, but on forward iterators it may require O(n) iterator increments. A tree container's member `lower_bound` navigates its tree in O(log n).

Prefer:

```cpp
map.lower_bound(key);
```

over generic `std::lower_bound(map.begin(), map.end(), ...)`.

### Worst-case requirements

Real-time code may reject average/amortized guarantees even if throughput is excellent.

### Interview question

**Question:** Does amortized O(1) mean every vector push is constant time?

**Answer:** No. Occasional reallocation is O(n); the average cost over a sequence is constant.

---

## 19. `size`, `capacity`, `reserve`, and `resize`

```cpp
std::vector<int> values;
values.reserve(100);
```

After reserve:

```text
capacity >= 100
size == 0
```

There are no elements to index yet.

```cpp
values.resize(100);
```

Now 100 elements exist, value/default-initialized as specified.

### Common error

```cpp
values.reserve(10);
// values[0] = 42; // invalid: size is still zero
```

Use:

```cpp
values.push_back(42);
```

or resize first.

### Shrinking

`clear()` destroys elements but need not reduce capacity.

`shrink_to_fit()` is a non-binding request and can invalidate if reallocation occurs.

### Interview question

**Question:** What is the difference between reserve and resize?

**Answer:** Reserve changes storage capacity without creating elements; resize changes the number of live elements.

---

## 20. Insertion, emplacement, and assignment APIs

### `push_back`

```cpp
values.push_back(Device{args});
```

Takes an existing value and copies/moves it into the container.

### `emplace_back`

```cpp
values.emplace_back(args);
```

Forwards arguments to construct the element in container storage.

### Emplace is not always faster

If an object already exists:

```cpp
Device device;
values.push_back(std::move(device));
```

is clear and efficient.

Emplace can:

- Invoke explicit constructors unexpectedly.
- Make conversions less visible.
- Offer no advantage when a temporary is already created.
- Still be followed by later vector reallocation/move.

### Map APIs

```cpp
map.emplace(key, value);
map.try_emplace(key, constructor_args...);
map.insert_or_assign(key, value);
```

`try_emplace` avoids constructing the mapped value when the key already exists in relevant cases.

### Interview question

**Question:** Why is `emplace_back` not automatically better than `push_back`?

**Answer:** It only avoids a temporary in suitable construction patterns; existing values move efficiently, and emplace may hide conversions without reducing work.

---

## 21. Comparators, predicates, and projections

Comparator:

```cpp
std::sort(devices.begin(), devices.end(),
          [](const Device& left, const Device& right) {
              return left.priority() < right.priority();
          });
```

A sorting comparator must provide strict weak ordering:

- Irreflexive: `comp(x, x)` is false.
- Asymmetric in the required sense.
- Transitive ordering/equivalence behavior.

Bad comparator:

```cpp
return left.priority() <= right.priority(); // invalid ordering
```

Stateful comparators can be used, but their copies and consistency matter.

Projection:

```cpp
std::ranges::sort(devices, {}, &Device::priority);
```

Predicate purity is not always formally required in the casual sense, but mutating compared elements or returning inconsistent results breaks algorithm assumptions.

### Interview question

**Question:** Why is `<=` usually wrong for a sort comparator?

**Answer:** It returns true for equivalent/self elements, violating strict weak ordering.

---

## 22. Hashing and custom keys

```cpp
struct DeviceKey {
    int bus;
    int address;

    bool operator==(const DeviceKey&) const = default;
};

struct DeviceKeyHash {
    std::size_t operator()(const DeviceKey& key) const noexcept {
        std::size_t seed = std::hash<int>{}(key.bus);
        // combine address using a deliberate hash-combine strategy
        return seed;
    }
};

std::unordered_map<DeviceKey, Device, DeviceKeyHash> devices;
```

A complete hash should incorporate all equality-relevant fields.

Contract:

```text
if equal(a, b), then hash(a) == hash(b)
```

The reverse is not required; collisions are allowed.

Avoid mutable key state that changes hash/equality while stored.

Specializing `std::hash` for a user-defined type can be permitted under standard rules, but a separate hash functor is often explicit and local.

### Interview question

**Question:** Must two different keys have different hash values?

**Answer:** No. Collisions are valid; equal keys must hash equally, and the container resolves collisions.

---

## 23. Heterogeneous lookup

Transparent comparators/hashes can avoid constructing a key:

```cpp
std::map<std::string, Device, std::less<>> devices;

auto iterator = devices.find(std::string_view{"camera"});
```

Availability depends on overloads and the comparator supporting cross-type comparison.

Benefits:

- Avoid temporary allocation/construction.
- Improve lookup with string views or lightweight IDs.
- Preserve container ordering/equality semantics.

The compared cross-types must form a coherent ordering/equality relationship.

### Interview question

**Question:** What does `std::less<>` enable compared with `std::less<std::string>`?

**Answer:** It is transparent and can participate in heterogeneous comparisons/lookups when operand types support coherent comparison.

---

## 24. The erase-remove pattern

Algorithms do not know how to change a container's size.

Classic:

```cpp
auto new_end = std::remove_if(
    values.begin(),
    values.end(),
    predicate);

values.erase(new_end, values.end());
```

`remove_if` moves retained elements forward and returns a new logical end. It does not erase container elements.

C++20 convenience:

```cpp
std::erase_if(values, predicate);
```

For list-like containers, member `remove_if` can unlink nodes directly.

### Interview question

**Question:** Why does `std::remove` not reduce vector size?

**Answer:** It is a generic iterator algorithm without container ownership; it rearranges elements and returns the new logical end, after which the container erases the tail.

---

## 25. Numeric algorithms

From `<numeric>`:

```cpp
std::accumulate
std::inner_product
std::partial_sum
std::adjacent_difference
std::iota
std::reduce
std::transform_reduce
std::exclusive_scan
std::inclusive_scan
```

### Initial-value type matters

```cpp
std::vector<std::int64_t> values;

auto wrong = std::accumulate(values.begin(), values.end(), 0);
auto right = std::accumulate(values.begin(), values.end(), std::int64_t{0});
```

The accumulator type is derived from the initial value; `0` is `int` and may overflow/truncate.

### `reduce` versus `accumulate`

`accumulate` is an ordered left fold. `reduce` permits reordering (especially with execution policies), so operations should be associative/commutative as required for intended results. Floating-point results may differ.

### Interview question

**Question:** Why can `accumulate(..., 0)` be wrong for 64-bit values?

**Answer:** The initial `0` makes the accumulator an `int`, so intermediate results can overflow or narrow.

---

## 26. Parallel algorithms

C++17 execution policies:

```cpp
std::sort(std::execution::par,
          values.begin(),
          values.end());
```

Policies include sequenced, parallel, and vectorization-related forms depending on standard/library support.

Responsibilities:

- Element operations must be safe under the policy.
- Shared side effects need synchronization or elimination.
- Exceptions and termination behavior differ by policy/specification.
- Library/runtime backend support varies.
- Parallel overhead may exceed benefit for small inputs.
- Deterministic order may be lost.

Embedded systems may lack backend support entirely.

### Interview question

**Question:** Is adding `std::execution::par` enough to make an algorithm safely parallel?

**Answer:** No. Predicates/operations and shared state must satisfy concurrency requirements, and backend/support/cost must be verified.

---

## 27. Allocators and `std::pmr`

Containers separate element behavior from allocation policy.

Traditional allocator parameter:

```cpp
std::vector<T, Allocator>
```

Allocator type becomes part of the container type.

C++17 polymorphic memory resources:

```cpp
std::pmr::monotonic_buffer_resource resource{buffer, sizeof(buffer)};
std::pmr::vector<int> values{&resource};
```

`std::pmr` moves resource selection toward runtime while retaining standard container interfaces.

### Uses

- Arenas.
- Fixed buffers.
- Request-scoped allocation.
- Reducing fragmentation.
- Grouped deallocation.
- Instrumentation.

### Tradeoffs

- Resource lifetime must outlive containers using it.
- Moving/copying across resources has rules/costs.
- Monotonic resources do not reclaim individual allocations.
- Fixed resources need clear exhaustion behavior.
- Allocators do not remove element constructor/destructor costs.

### Interview question

**Question:** What problem does `std::pmr` address?

**Answer:** It allows standard containers to use runtime-selected memory-resource strategies without making every resource choice a different high-level container type.

---

## 28. Exception safety and element requirements

Container operations depend on element properties:

- Copy/move constructibility.
- Copy/move assignment.
- Destruction.
- Swappability.
- Comparator/hash behavior.
- `noexcept` move.

During vector growth, a throwing move may cause vector to copy elements instead when copying is available and needed for guarantees.

Common guarantees:

- Strong: operation failure leaves original state unchanged.
- Basic: invariants preserved, state may change.
- No-throw: operation does not throw.

Exact guarantee depends on operation, allocator, element type, and standard specification.

### Interview question

**Question:** Why can marking a move constructor `noexcept` improve vector behavior?

**Answer:** Vector can move elements during reallocation while preserving its exception guarantees instead of falling back to copying.

---

## 29. Ownership and lifetime

Containers own their elements:

```cpp
std::vector<Device> devices;
```

Destroying the vector destroys its elements.

A container of pointers has different semantics:

```cpp
std::vector<Device*> observers;                  // normally non-owning
std::vector<std::unique_ptr<Device>> owners;     // exclusive ownership
std::vector<std::shared_ptr<Device>> shared;     // shared ownership
```

Do not infer ownership from “container stores addresses”; express it in the element type.

References/views/iterators into a container do not own elements and can be invalidated.

### Interview question

**Question:** Does `vector<Device*>` delete the pointed-to devices?

**Answer:** No. It destroys pointer values only; use an owning smart-pointer element type when the container owns devices.

---

## 30. Embedded and real-time considerations

Questions for every container/algorithm:

- Does it allocate?
- When can it reallocate?
- What is worst-case complexity?
- Can an operation throw?
- What is per-element overhead?
- Are addresses stable?
- Is memory contiguous?
- Can capacity be fixed/preallocated?
- Is the allocator deterministic?
- Does the implementation exist in the vendor library?

### Useful facilities

```cpp
std::array
std::span
std::algorithm
std::bitset
```

These can support fixed storage and generic algorithms without heap ownership.

`vector` may still be acceptable when constructed/pre-reserved during initialization and never grows on a real-time path, subject to project policy.

Node/hash containers can fragment memory and create timing variability.

### Interview question

**Question:** Is STL forbidden in embedded systems?

**Answer:** No. Select facilities by allocation, exceptions, code size, timing, implementation support, and determinism rather than rejecting the entire library.

---

## 31. Common mistakes

- Choosing list solely because insertion is O(1).
- Forgetting vector reallocation invalidation.
- Using `map[key]` for lookup and accidentally inserting.
- Treating unordered complexity as guaranteed O(1).
- Using an invalid comparator such as `<=`.
- Calling `reserve` and indexing nonexistent elements.
- Assuming emplace always improves performance.
- Dereferencing `end()`.
- Mixing iterators from different containers.
- Keeping iterators across invalidating operations.
- Forgetting sorted-range preconditions.
- Copying expensive elements in range loops.
- Assuming views own data.
- Using `accumulate` with the wrong initial type.
- Storing owning raw pointers.
- Ignoring allocator/resource lifetime.

### Interview question

**Question:** What STL bug appears most often in systems code?

**Answer:** Using a pointer/reference/iterator after container reallocation, erasure, rehash, or owner destruction.

---

## 32. Interview comparison drills

### Vector versus list

Discuss:

- Contiguous locality versus nodes.
- Random access versus traversal.
- Invalidation.
- Known-position operations.
- Allocation overhead.
- Typical workload, not only asymptotic insertion.

### Map versus unordered_map

Discuss:

- Ordering.
- O(log n) worst-case versus average O(1).
- Hash quality/security.
- Rehash invalidation.
- Memory overhead.
- Heterogeneous lookup.
- Deterministic iteration/timing.

### Array versus vector

Discuss:

- Compile-time fixed extent versus runtime dynamic size.
- Direct storage versus dynamic allocation.
- Type identity.
- Stack/object-size constraints.
- Ability to resize.

### Deque versus vector

Discuss:

- Front operations.
- Contiguity.
- Locality.
- Invalidation.
- Random access.

### Interview question

**Question:** What is a strong container-comparison answer?

**Answer:** State required operations, complexity including worst/amortized cases, memory layout/locality, invalidation, allocation, and workload-specific tradeoffs.

---

## 33. Practical algorithm patterns

### Find

```cpp
if (auto iterator = std::ranges::find(values, target);
    iterator != values.end()) {
}
```

### Transform into reserved destination

```cpp
std::vector<Result> results;
results.reserve(inputs.size());

std::ranges::transform(
    inputs,
    std::back_inserter(results),
    convert);
```

### Sort and deduplicate

```cpp
std::ranges::sort(values);
auto subrange = std::ranges::unique(values);
values.erase(subrange.begin(), subrange.end());
```

### Top K

Use `priority_queue`, partial sort, or nth-element depending whether you need streaming behavior, sorted output, memory limits, and K relative to N.

### Frequency table

```cpp
std::unordered_map<Value, std::size_t> frequencies;

for (const auto& value : values) {
    ++frequencies[value];
}
```

### Interview question

**Question:** How do `partial_sort`, `nth_element`, and a heap differ for top-K?

**Answer:** Partial sort orders the selected prefix, nth-element partitions without fully ordering it, and a size-K heap supports streaming with O(n log k) behavior.

---

## 34. Practical guidelines

1. Prefer vector for a general sequence.
2. Choose containers by operations, layout, stability, allocation, and worst-case needs.
3. Know iterator category requirements before selecting an algorithm.
4. Treat every pointer/reference/iterator as a borrowed handle with invalidation rules.
5. Reserve expected vector/unordered capacity when it improves predictability.
6. Use `find`/`contains` instead of `map[]` for non-inserting lookup.
7. Keep comparator/hash/equality semantics consistent.
8. Prefer algorithms/ranges when they make intent clearer.
9. Use correct loop references to avoid copies.
10. Do not assume emplace, unordered containers, or parallel execution are automatically faster.
11. Use RAII element types to express ownership.
12. Review allocator/resource lifetime in custom-memory systems.
13. Measure with representative data and target hardware.
14. In embedded code, review worst case, not only average throughput.

### Interview question

**Question:** What should you say before selecting an STL container in an interview?

**Answer:** Clarify ordering, access, insertion/erase, lifetime stability, memory, size bounds, allocation, and worst-case complexity requirements.

---

## Final interview checklist

You should be able to explain:

- STL versus the complete standard library.
- Containers, iterators, algorithms, callables, and allocators.
- Array/vector/deque/list tradeoffs.
- Ordered versus unordered associative containers.
- Stack/queue/priority-queue behavior.
- String ownership and string-view borrowing.
- Iterator categories and past-the-end semantics.
- Const iterators.
- Invalidation rules by container.
- Core algorithm families and preconditions.
- Ranges algorithms, views, projections, and dangling.
- Complexity, worst case, and amortization.
- Size/capacity/reserve/resize.
- Push versus emplace.
- Comparator and hash contracts.
- Heterogeneous lookup.
- Erase-remove.
- Numeric and parallel algorithm pitfalls.
- Allocators and `std::pmr`.
- Exception/noexcept element effects.
- Ownership through container element types.
- Embedded allocation, memory-layout, and determinism tradeoffs.
