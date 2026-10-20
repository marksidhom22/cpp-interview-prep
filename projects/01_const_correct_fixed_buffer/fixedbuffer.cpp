include <stdint.h>
#include <cstddef>



template <typename T, std::size_t Size>
class fixedBuffer{
public:

    static_assert(Size>0 , "the size must be greater than zero");

    using value_type = T;
    using size_type = std::size_t;
    using iterator = T*;
    using const_iterator = const T*;

    FixedBuffer(){
    }
    explicit FixedBuffer(const T& initial_value){
        for (auto& element : data_){
            element = initial_value;
        }
     }

    [[nodiscard]] constexpr size_type size() const noexcept{
        return Size;
    }
    [[nodiscard]] constexpr bool empty() cost noexcept{
        return Size;

    }


    T& operator[](size_t index) noexcept{
        if (index <0 || index >= Size){
            throw("index is out of bounds");
        }
        return data_[index];
    }
    const T& operator[](size_t index) const noexcept{
        if (index <0 || index >= Size){
            throw("index is out of bounds");
        }
        return data_[index];
    }

    T& at(size_t index){
        return data_[index];
    }
    const T& at(size_t index) const{
        return data_[index];
    }

    T& front(){
        return data_[0];
    }
    const T& front() const{
        return data_[0];
    }

    T& back(){
        return data_[Size-1];
    }
    const T& back() const{
                return data_[Size-1];

    }

    iterator begin() noexcept{
        return data_;
    }
    const_iterator begin() const noexcept{
        return data_;
    }
    iterator end() noexcept{
        return data+Size;
    }
    const_iterator end() const noexcept{
        return data+Size;

    }


private:

    T data_[Size]{};



};
