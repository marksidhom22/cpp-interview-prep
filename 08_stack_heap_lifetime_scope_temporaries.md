# Stack, Heap, Lifetime, Scope, and Temporaries

## Stack objects

```cpp
void f() {
    Device d;
}
```

`d` has automatic storage duration.

It is destroyed automatically when its scope ends.

Benefits:
- simple lifetime
- no manual `delete`
- usually fast allocation/deallocation

---

## Heap objects

```cpp
Device* d = new Device;
delete d;
```

The object remains alive until it is explicitly deleted.

Modern C++ usually prefers:

```cpp
auto d = std::make_unique<Device>();
```

Use dynamic allocation only when the required lifetime or ownership model needs it.

---

## Scope

Scope determines where a name is visible.

```cpp
{
    int x = 10;
}
// x no longer exists here
```

Common scopes:
- block
- function
- class
- namespace

---

## Object lifetime

Lifetime is the period during which an object actually exists.

A pointer/reference may still exist after the object dies:

```cpp
int* p;

{
    int x = 10;
    p = &x;
}

// p is now dangling
```

Always separate:
- pointer/reference lifetime
- pointed-to object's lifetime

---

## Temporary objects

Temporaries are objects created for intermediate expressions.

```cpp
std::string s = std::string("hello");
```

A temporary may also appear here:

```cpp
void print(const std::string& s);

print("hello");
```

A temporary `std::string` can be created and bound to the const reference.

Temporary lifetime rules matter because references to expired temporaries can dangle.

## Interview takeaway

Think in terms of:

```text
Where is the object stored?
Who owns it?
When is it destroyed?
Can any pointer/reference outlive it?
```

Lifetime reasoning is more important than simply saying "stack vs heap."
